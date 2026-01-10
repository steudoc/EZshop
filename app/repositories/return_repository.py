from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.DAO.return_dao import ReturnDAO, ReturnLineDAO
from app.models.DAO.sale_dao import SaleDAO
from app.models.DTO.return_dto import ReturnItemDTO
from app.models.sale_status import SaleStatus
from app.utils import find_or_throw_not_found
from app.database.database import AsyncSessionLocal
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from typing import Optional
from datetime import datetime


class ReturnRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()
    
    async def start_return(self, sale_id: int) -> ReturnDAO:
        """
        Create new return transaction
        Validates that sale exists and is in closed and paid state
        """
        async with await self._get_session() as session:
            # Check if sale exists
            sale = await session.get(SaleDAO, sale_id)
            if not sale:
                raise NotFoundError(f"Sale with id '{sale_id}' not found")
            
            # Check if sale is closed and paid
            if sale.status != SaleStatus.PAID:
                raise InvalidStateError("Return allowed only on paid sales")

            return_transaction = ReturnDAO(
                sale_id=sale_id,
                status="OPEN",
                created_at=datetime.now()
            )
            session.add(return_transaction)
            await session.commit()
            await session.refresh(return_transaction)
            return return_transaction
        
    async def get_return_by_id(self, return_id: int) -> Optional[ReturnDAO]:
        """
        Get return transaction by id or throw NotFoundError if not found
        Eagerly loads the return lines
        """
        async with await self._get_session() as session:
            query = select(ReturnDAO).where(ReturnDAO.id == return_id).options(selectinload(ReturnDAO.lines))
            result = await session.execute(query)
            return_transaction = result.scalars().first()
            return find_or_throw_not_found(
                [return_transaction] if return_transaction else [],
                lambda _: True,
                "Return not found"
            )
        
    async def get_returns_by_sale(self, sale_id: int) -> list[ReturnDAO]:
        """
        Get all return transactions associated with a sale id
        """
        async with await self._get_session() as session:
            result = await session.execute(select(ReturnDAO).filter(ReturnDAO.sale_id == sale_id))
            return result.scalars().all()
    
    async def get_all_returns(self) -> list[ReturnDAO]:
        """Get all return transactions"""
        async with await self._get_session() as session:
            result = await session.execute(select(ReturnDAO))
            return result.scalars().all()
        
    async def update_return(self, return_id: int, updated_sale_id: int, updated_status: int, updated_created_at: datetime, updated_closed_at: datetime) -> Optional[ReturnDAO]:
        """
        Update return information. Throw NotFoundError if not found
        """
        async with await self._get_session() as session:
            db_return = await session.get(ReturnDAO, return_id)
            if not db_return:
                return None

            db_return.sale_id = updated_sale_id
            db_return.status = updated_status
            db_return.created_at = updated_created_at
            db_return.closed_at = updated_closed_at

            await session.commit()
            await session.refresh(db_return)
            return db_return
    
    async def delete_return(self, return_id: int) -> bool:
        """
        Delete return by id. Will throw NotFoundError if return doesn't exist
        or InvalidStateError if return is reimbursed
        """
        async with await self._get_session() as session:
            return_transaction = await session.get(ReturnDAO, return_id)

            find_or_throw_not_found(
                [return_transaction] if return_transaction else [],
                lambda _: True,
                f"Return not found"
            )

            # Check if return is reimbursed
            if return_transaction.status == "REIMBURSED":
                raise InvalidStateError("Cannot delete a reimbursed return")

            await session.delete(return_transaction)
            await session.commit()
            return True

    async def add_item(self, return_id: int, item: ReturnItemDTO) -> Optional[ReturnDAO]:
        """Add a product to a return transaction"""
        async with await self._get_session() as session:
            return_tx = await session.get(ReturnDAO, return_id, options=[selectinload(ReturnDAO.lines)])
            if not return_tx:
                raise NotFoundError(f"Return with id '{return_id}' not found")
            
            # Check if line with same barcode already exists
            existing_line = next((line for line in return_tx.lines if line.product_barcode == item.product_barcode), None)
            
            if existing_line:
                # Increase quantity of existing line
                existing_line.quantity += item.quantity
            else:
                # Create new line
                new_line = ReturnLineDAO(
                    return_id=return_id,
                    product_barcode=item.product_barcode,
                    quantity=item.quantity,
                    price_per_unit=item.price_per_unit
                )
                session.add(new_line)
            
            await session.commit()
            await session.refresh(return_tx)
            return return_tx

    async def remove_item(self, return_id: int, product_barcode: str, quantity: int) -> Optional[ReturnDAO]:
        """Remove a product from a return transaction
        If quantity equals the line quantity, delete the entire line
        If quantity is less, decrease the line quantity
        """
        async with await self._get_session() as session:
            result = await session.execute(
                select(ReturnLineDAO).where(
                    ReturnLineDAO.return_id == return_id,
                    ReturnLineDAO.product_barcode == product_barcode
                )
            )
            line = result.scalars().first()
            if not line:
                raise NotFoundError(f"Return line not found for return_id '{return_id}' and product_barcode '{product_barcode}'")
            
            # If quantity matches line quantity, delete the entire line
            if quantity >= line.quantity:
                await session.delete(line)
            else:
                # Decrease the quantity
                line.quantity -= quantity
            
            await session.commit()
            return_tx = await session.get(ReturnDAO, return_id, options=[selectinload(ReturnDAO.lines)])
            return return_tx

    async def close_return(self, return_id: int) -> Optional[ReturnDAO]:
        """Close a return transaction"""
        async with await self._get_session() as session:
            return_tx = await session.get(ReturnDAO, return_id)
            if not return_tx:
                return None
            return_tx.status = "CLOSED"
            return_tx.closed_at = datetime.now()
            await session.commit()
            await session.refresh(return_tx)
            return return_tx

    async def reimburse_return(self, return_id: int) -> Optional[ReturnDAO]:
        """Update a return transaction as reimbursed
        Throws NotFoundError if return not found
        Throws InvalidStateError if return status is not CLOSED
        """
        async with await self._get_session() as session:
            return_tx = await session.get(ReturnDAO, return_id)
            if not return_tx:
                raise NotFoundError(f"Return with id '{return_id}' not found")
            
            if return_tx.status != "CLOSED":
                raise InvalidStateError("Return must be closed before reimbursement")
            
            return_tx.status = "REIMBURSED"
            await session.commit()
            await session.refresh(return_tx)
            return return_tx







