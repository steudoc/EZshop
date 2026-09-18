from typing import List, Optional
from app.repositories.product_repository import ProductRepository
from app.models.DTO.product_dto import ProductDTO
from app.services.mapper_service import productdao_to_dto, update_productdao_from_partial_dto
from app.utils import throw_conflict, throw_not_found, throw_bad_request


class ProductController:

    def __init__(self):
        self.repo = ProductRepository()


    async def create_product(self, product_dto: ProductDTO) -> ProductDTO: 
        """Create product - throws ConflictError if barcode exists, throws BadRequestError if parameters are not valid"""
        # check for missing values in given product and initialize them
        if (product_dto.position is None):
            product_dto.position = ""

        if (product_dto.quantity is None):
            product_dto.quantity = 0

		# check that new position is reset position or free from other products
        if (product_dto.position != ""):
            position_free = await self.repo.is_position_free(product_dto.position)
            if (not position_free):
                throw_conflict(f"Position {product_dto.position} already occupied by another product")

        
        created = await self.repo.create_product(product_dto.barcode, 
                                                 product_dto.price_per_unit, product_dto.description,
                                                 product_dto.quantity, product_dto.position,
                                                 product_dto.note)
        return productdao_to_dto(created)
    

    async def get_product_by_id(self, product_id: int) -> Optional[ProductDTO]:
        """Get product which has given id or None if no product is found"""
        product = await self.repo.get_product_by_id(product_id)
        return None if (product is None) else productdao_to_dto(product)
    

    async def get_product_by_barcode(self, barcode: str) -> Optional[ProductDTO]:
        """Get product which has given barcode or None if no product is found,
          throws BadRequestError if barcode is not correctly formatted"""
        product = await self.repo.get_product_by_barcode(barcode)
        return None if (product is None) else productdao_to_dto(product)


    async def get_products_by_description(self, partial_description: str) -> List[ProductDTO]:
        """Get products with a description that contains the given partial description string"""
        all_products = await self.repo.list_products()
        # matches = list()
        # for dao in all_products:
        #     # if (partial_description in dao.description):
        #         matches.append(productdao_to_dto(dao))
        matches = [productdao_to_dto(dao) for dao in all_products if (partial_description.lower() in dao.description.lower())]
        return matches
    

    async def update_product(self, product_dto: ProductDTO) -> ProductDTO:
        """
        Update product information. Will throw ConflictError if the barcode already exists,
        will throw BadRequestError if product data is not valid, will throw InvalidStateError 
        if the product barcode is changed and the product is associated with at least a 
        sale/order/return transaction, will throw NotFoundError if product doesn't exist.
        """

        # get the product in the db (throw not found if not found)
        db_product = await self.repo.get_product_by_id(product_dto.id)
        if (db_product is None):
            throw_not_found("Product not found")
            
        # check that new position is reset position or free from other products
        if (product_dto.position is not None and product_dto.position != db_product.position):
            if (product_dto.position != "" ):
                position_free = await self.repo.is_position_free(product_dto.position)
                if (not position_free):
                    throw_conflict(f"Position {product_dto.position} already occupied by another product")
                
        # check that quantity is >= 0
        if (product_dto.quantity is not None and product_dto.quantity < 0):
            throw_bad_request("Product quantity must be greater than or equal to 0")

        # update product with present information from the request update request dto
        update_productdao_from_partial_dto(db_product, product_dto)
        
        updated_product = await self.repo.update_product(db_product)
        return productdao_to_dto(updated_product)
         

    async def delete_product(self, product_id: int) -> None:
        """
        Delete product by id. Will throw NotFoundError if product doesn't exist,
        will throw InvalidStateError if product cannot be deleted in its current state
        """
        await self.repo.delete_product(product_id)


    async def list_products(self) -> List[ProductDTO]:
        """Get all products"""
        all_products = await self.repo.list_products()
        return [productdao_to_dto(dao) for dao in all_products]
    

    async def increment_product_quantity(self, product_id: int, increment: int) -> None:
        """Increments the quantity of the product with the given id. Will throw NotFoundError 
        if product doesn't exist, throw BadRequestError if resulting quantity is negative"""

        # get the product in the db (throw not found if not found)
        product = await self.repo.get_product_by_id(product_id)
        if (product is None):
            throw_not_found("Product not found")
            
        # check that resulting quantity is >= 0
        if (product.quantity + increment < 0):
            throw_bad_request("Insufficient product quantity")

        # update product quantity and update db
        product.quantity += increment
        await self.repo.update_product(product)


    async def move_product(self, product_id: int, position: str) -> None:
        """Moves the product with the given id to a new position.
        Will throw NotFoundError if product doesn't exist, will throw
        BadRequestError if position is not valid,
        will throw ConflictError if position is already occupied"""
        
		# first check that given position is valid
        if (not self.repo.is_position_valid(position)):
            throw_bad_request("Invalid position")

        # get the product in the db (throw not found if not found)
        product = await self.repo.get_product_by_id(product_id)
        if (product is None):
            throw_not_found("Product not found")

        # check that position is reset position or free from other products
        if (position != "" and position != product.position):
            position_free = await self.repo.is_position_free(position)
            if (not position_free):
                throw_conflict(f"Position {position} already occupied by another product")

        # update product position
        product.position = position
        await self.repo.update_product(product)
    
    
    async def include_product_in_op(self, product_id: int) -> ProductDTO:
        """Adds an association the product with the given id with a shop transaction.
        Will throw NotFoundError if product doesn't exist"""
        # get the product in the db (throw not found if not found)
        product = await self.repo.get_product_by_id(product_id)
        if (product is None):
            throw_not_found("Product not found")
            
        # update number of operations in which product is involved and update db
        product.involvedOperations += 1
        await self.repo.update_product(product)
    

    async def exclude_product_from_op(self, product_id: int) -> ProductDTO:
        """Removes an association of the product with the given id with a shop transaction.
        Will throw NotFoundError if product doesn't exist, will throw BadRequestError if 
        product is not involved in any operation"""
        # get the product in the db (throw not found if not found)
        product = await self.repo.get_product_by_id(product_id)
        if (product is None):
            throw_not_found("Product not found")
            
        # check that product is involved in at least one transaction 
        if (product.involvedOperations < 1):
            throw_bad_request("Product is not involved in any shop operation")

        # update number of operations in which product is involved and update db
        product.involvedOperations -= 1
        await self.repo.update_product(product)