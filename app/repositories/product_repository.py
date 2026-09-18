from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.DAO.product_dao import ProductDAO
from app.repositories.base_repository import BaseRepository
from app.utils import throw_bad_request, throw_not_found, throw_conflict, throw_invalid_state
from app.database.database import AsyncSessionLocal
from typing import Optional
import re


class ProductRepository(BaseRepository):

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return super().get_session()

    def is_barcode_valid(self, barcode: str) -> bool:
        '''
        Returns True if the given barcode string is a valid barcode, False otherwise.
        Given barcode must be a digits-only string of 12 to 14 digits, matching the 
        GTIN checksum algorithm
        '''

        # preliminary checks such as length and decimal chars format 
        if (barcode == None or len(barcode) < 12 or 
            len(barcode) > 14 or not barcode.isdecimal()):
            return False
        
        # GTIN check for barcodes (https://www.gs1.org/services/how-calculate-check-digit-manually)
        reversed_barcode = barcode[::-1]
        digits = [ord(ch) - ord('0') for ch in reversed_barcode]
        sum = 0
        for (i, digit) in enumerate(digits):
            mul_digit = digit * (1 if (i % 2 == 0) else 3)
            sum += mul_digit

        if (sum % 10 != 0):
            return False
        
        # if all conditions pass, then the barcode is valid
        return True
    
    def is_position_valid(self, position: str, allow_unassigned: bool = True) -> bool:
        '''
        Returns True if the given position string is a valid position, False otherwise.
        If an unassigned position is allowed (default behaviour), then None and empty string
        will be considered valid positions
        '''

        # if allowed, check that position is an empty string or None
        if (allow_unassigned and (position is None or position == "")):
            return True
        # check that position matches the format <digits>-<letters>-<digits> from requirements
        else:
            return re.match(r"\d+-\w+-\d+", position)

    def is_product_data_valid(self, barcode, description, price_per_unit, quantity, position) -> bool:
        '''
        Returns True if the given product data is valid, False otherwise.
        barcode must be valid, description must be present (min 1 char), 
        price_per_unit must be >= 0, quantity must be >= 0, position must be 
        either not present (None or empty string) or it must be of the correct format 
        '''

        #check barcode format (12-14 digits)
        if (not self.is_barcode_valid(barcode)):
            return False
        
        # check that description is present
        if (description == None or description == ""):
            return False

        # check that price is present and valid
        if (price_per_unit == None or price_per_unit <= 0):
            return False

        # check that quantity is valid
        if (quantity is None or quantity < 0):
            return False
        
        # check the position format
        if (not self.is_position_valid(position)):
            return False
        
        # if all conditions pass, then the data is valid
        return True


    async def is_position_free(self, position: str) -> bool:
        """
        Check if position is free. Will throw BadRequestError if position is not valid,
        """
        
        # check position format
        if (not self.is_position_valid(position)):
            throw_bad_request("Position format is not valid")

        # check if other products have occupied the position
        async with await self._get_session() as session:
            result = await session.execute(select(ProductDAO).filter(ProductDAO.position == position))
            productOrNone = result.scalars().first()
            return (productOrNone is None)


    async def create_product(self, barcode: str, price_per_unit: float, description: str, quantity: int, position: str = None, note: str = None) -> ProductDAO:
        """
        Create product or throw ConflictError if barcode exists, throw BadRequestError if parameters are not valid
        """

        if (not self.is_product_data_valid(barcode, description, price_per_unit, quantity, position)):
            throw_bad_request("Product data is not valid")

        sameBarcodeProduct = await self.get_product_by_barcode(barcode)
        
        async with await self._get_session() as session:
            result = await session.execute(select(ProductDAO).filter(ProductDAO.barcode == barcode))
            sameBarcodeProduct = result.scalars().all()

            if (sameBarcodeProduct):
                throw_conflict(f"Product with barcode'{barcode}' already exists")

            product = ProductDAO(barcode=barcode, price_per_unit=price_per_unit, quantity=quantity, position=position, description=description, note=note)
            session.add(product)
            await session.flush()
            await session.refresh(product)
            return product	
        
    async def get_product_by_id(self, product_id: int) -> Optional[ProductDAO]:
        """
        Get product by id or return None if not found
        """
        async with await self._get_session() as session:
            productOrNone = await session.get(ProductDAO, product_id)
            return productOrNone


    async def get_product_by_barcode(self, barcode: str) -> Optional[ProductDAO]:
        """
        Get product by barcode or return None if not found, 
        throw BadRequestError if barcode is not correctly formatted
        """

        if (not self.is_barcode_valid(barcode)):
            throw_bad_request("Invalid product code")

        async with await self._get_session() as session:
            result = await session.execute(select(ProductDAO).filter(ProductDAO.barcode == barcode))
            productOrNone = result.scalars().first()
            return productOrNone


    async def list_products(self) -> list[ProductDAO]:
        """Get all products"""
        async with await self._get_session() as session:
            result = await session.execute(select(ProductDAO))
            return result.scalars().all()

    
    async def update_product(self, product: ProductDAO) -> ProductDAO:
        """
        Update product information. Will throw ConflictError if the barcode already exists,
        will throw BadRequestError if product data is not valid, will throw InvalidStateError 
        if the product barcode is changed and the product is associated with at least a 
        sale/order/return transaction, will throw NotFoundError if product doesn't exist.
        """
        
        if (not self.is_product_data_valid(product.barcode, product.description, 
            product.price_per_unit, product.quantity, product.position)):
            throw_bad_request("Product data is not valid")

        async with await self._get_session() as session:
            db_product = await session.get(ProductDAO, product.id)

            # check that product to update is found
            if (db_product is None):
               throw_not_found("Product not found")

             # check that product to update is found
            same_pos = await session.execute(select(ProductDAO).filter(ProductDAO.barcode == product.barcode).filter(ProductDAO.id != product.id))

            # if the barcode changed, perform some additional checks
            if (product.barcode != db_product.barcode):

                # check that the product is not included in any operation
                if (db_product.involvedOperations > 0):
                    throw_invalid_state("Invalid sale state")

                # get products with same barcode and different id (expected: 0)
                result_conflict = await session.execute(select(ProductDAO).filter(ProductDAO.barcode == product.barcode).filter(ProductDAO.id != product.id))
                (confilicting_products) = result_conflict.scalars().all()

                if ((confilicting_products)):
                    throw_conflict("Barcode already in use")
               
            # update product data
            db_product.barcode = product.barcode
            db_product.description = product.description
            db_product.price_per_unit = product.price_per_unit
            db_product.note = product.note 
            db_product.position = product.position 
            db_product.quantity = product.quantity 
            db_product.involvedOperations = product.involvedOperations

            await session.flush()
            await session.refresh(db_product)
            return db_product
        
    
    async def delete_product(self, product_id: int) -> None:
        """
        Delete product by id. Will throw NotFoundError if product doesn't exist,
        will throw InvalidStateError if product cannot be deleted in its current state
        """
        async with await self._get_session() as session:
            db_product = await session.get(ProductDAO, product_id)

            # check that product to delete is found
            if (db_product is None):
                throw_not_found("Product not found")

            # check that the product is not included in any operation
            if (db_product.involvedOperations > 0):
                    throw_invalid_state("Invalid sale state")

            await session.delete(db_product)
            await session.flush()


    


    async def include_product_in_op(self, product_id: int, include: bool) -> None:
        """
        Include or exclude product from shop operation. 
        Will throw NotFoundError if product with given id is not found, will throw
        BadRequestError if the product cannot be excluded from any shop operation when
        trying to do so
        """

        async with await self._get_session() as session:
            # get product from db
            product = await session.get(ProductDAO, product_id)

            # check that product is present
            if (product is None):
                throw_not_found("Product not found")

            # check that involved operations can be decremented
            if (not include and product.involvedOperations < 1):
                throw_bad_request("Product is not involved in any shop operation")

            # update number of operations in which product is involved and update db (+-1)
            product.involvedOperations += (1 if include else -1)
            await session.flush()

        
