from datetime import datetime
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.DAO.sale_dao import SaleDAO, SaleLineDAO
from app.models.sale_status import SaleStatus
from app.utils import find_or_throw_not_found, throw_bad_request, throw_not_found

class SaleRepository(BaseRepository):
    _instance: Optional["SaleRepository"] = None

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SaleRepository, cls).__new__(cls)
        return cls._instance

    async def _get_session(self) -> AsyncSession:
        return super().get_session()

    # ==============================================================================
    # PRIVATE HELPER METHODS
    # ==============================================================================

    async def _get_sale_with_lines(self, session: AsyncSession, sale_id: int) -> Optional[SaleDAO]:
        """Helper to fetch a sale including lines (Eager Loading)"""
        query = (
            select(SaleDAO)
            .where(SaleDAO.id == sale_id)
            .options(selectinload(SaleDAO.lines))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    # ==============================================================================
    # PUBLIC METHODS
    # ==============================================================================

    async def list_sales(self) -> List[SaleDAO]:
        """Get all sales"""
        async with await self._get_session() as session:
            query = select(SaleDAO).options(selectinload(SaleDAO.lines))
            result = await session.execute(query)
            return result.scalars().all()

    async def create_sale(self) -> SaleDAO:
        """Create a new sale"""
        async with await self._get_session() as session:
            new_sale = SaleDAO()
            session.add(new_sale)
            await session.commit()
            
            # Reuse helper to return the fresh object with lines loaded
            return await self._get_sale_with_lines(session, new_sale.id)

    async def get_sale_by_id(self, sale_id: int) -> Optional[SaleDAO]:
        """Get a sale by ID - returns None if not found"""
        async with await self._get_session() as session:
            return await self._get_sale_with_lines(session, sale_id)

    async def delete_sale(self, sale_id: int) -> None:
        """Delete a sale - throws NotFoundError if not found"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")

            product_repository = ProductRepository(session)

            # Restore product quantities
            for line in sale.lines:
                product = await product_repository.get_product_by_barcode(line.product_barcode)
                if product:
                    product.quantity += line.quantity
                    product.involvedOperations -= 1
                    await product_repository.update_product(product)
                    
            await session.delete(sale)

    async def add_item_to_sale(self, sale_id: int, product_barcode: str, quantity: int) -> bool:
        """Add item to sale - throws NotFoundError if sale/product missing, BadRequestError if no stock"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")

            product_repository = ProductRepository(session)
            product = await product_repository.get_product_by_barcode(product_barcode)

            # Validate Product
            if not product:
                throw_not_found(f"Product with barcode '{product_barcode}' not found")

            # Validate Stock
            if product.quantity < quantity:
                throw_bad_request(f"Not enough quantity available. Requested: {quantity}, Available: {product.quantity}")

            # Check for existing line
            existing_line = next(
                (line for line in sale.lines if line.product_barcode == product_barcode), 
                None
            )

            if existing_line:
                existing_line.quantity += quantity
            else:
                new_line = SaleLineDAO(
                    sale_id=sale.id, 
                    product_barcode=product_barcode, 
                    quantity=quantity, 
                    price_per_unit=product.price_per_unit 
                )
                sale.lines.append(new_line)
                product.involvedOperations += 1

            # Update Product Stock
            product.quantity -= quantity
            await product_repository.update_product(product)

            return True

    async def remove_item_from_sale(self, sale_id: int, product_barcode: str, quantity: int) -> bool:
        """Remove item from sale - throws NotFoundError if sale/line/product missing"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")

            # Find line to remove
            line_to_remove = next(
                (line for line in sale.lines if line.product_barcode == product_barcode), 
                None
            )

            if not line_to_remove:
                throw_not_found("Sale line not found")

            # Adjust quantity to remove
            if line_to_remove.quantity < quantity:
                quantity = line_to_remove.quantity
    
            line_to_remove.quantity -= quantity

            # Restore Product Stock
            product_repository = ProductRepository(session)
            product = await product_repository.get_product_by_barcode(product_barcode)

            if not product:
                throw_not_found("Product not found")

            # Remove line if empty
            if line_to_remove.quantity <= 0:
                sale.lines.remove(line_to_remove)
                product.involvedOperations -= 1
            
            product.quantity += quantity              
            await product_repository.update_product(product)

            return True

    async def update_sale_line_discount(self, sale_id: int, product_barcode: str, discount: float) -> bool:
        """Update discount on a specific line - throws NotFoundError if sale/line missing"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")

            line_to_update = next(
                (line for line in sale.lines if line.product_barcode == product_barcode),
                None
            )

            if not line_to_update:
                throw_not_found("Sale line not found")

            line_to_update.discount_rate = discount
            return True

    async def update_sale_discount(self, sale_id: int, discount: float) -> bool:
        """Update global sale discount - throws NotFoundError if sale missing"""
        async with await self._get_session() as session:
            # Simple fetch is enough here, but using helper ensures consistency
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")
                
            sale.discount_rate = discount
            session.add(sale)
            return True

    async def update_sale_status_pending(self, sale_id: int) -> bool:
        """Set sale status to PENDING - deletes sale if empty"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")
            
            # Check empty sale
            if not sale.lines:
                await session.delete(sale)
                return True
                
            sale.status = SaleStatus.PENDING    
            sale.closed_at = datetime.now()
            return True

    async def update_sale_status_paid(self, sale_id: int) -> bool:
        """Set sale status to PAID from PENDING"""
        async with await self._get_session() as session:
            sale = await self._get_sale_with_lines(session, sale_id)
            if not sale:
                throw_not_found("Sale not found")
            sale.status = SaleStatus.PAID    
            return True