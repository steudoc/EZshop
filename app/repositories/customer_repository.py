from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DAO.card_dao import CardDAO
from app.models.DTO.customer_dto import CardDTO, UpdateCardDTO
from app.database.database import AsyncSessionLocal
from typing import Optional
from app.models.errors.notfound_error import NotFoundError
from app.utils import find_or_throw_not_found, throw_bad_request, throw_conflict, throw_not_found
from app.repositories.card_repository import CardRepository
class CustomerRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def create_customer(
            self,
            name: str,
            card: Optional[CardDTO]
    ) -> tuple[CustomerDAO, Optional[CardDAO]]:
        """
        Create and store a customer on the database.

        Args:
            name(str): The customer name
            card(Optional[CardDTO]): A customer card if already exists
        Returns:
            CustomerDAO: Instance of the newly created and saved customer.
            CardDAO: Instance of the card.
        Raises:
            ConflictError: If card is already attached to a customer.
        """
        async with await self._get_session() as session:
            
            customer = CustomerDAO(name=name)
            session.add(customer)
            await session.flush()

            card_dao: Optional[CardDAO] = None

            if card is not None:

                card_dao = await session.get(CardDAO, card.card_id)

                if card_dao is None:
                    throw_bad_request(f"Card with id {card.card_id} must be positive")

                if card_dao.customer_id is not None:
                    throw_conflict(f"Card with id {card.card_id} is already attached to a customer")

                card_dao.customer_id=customer.id

            await session.commit()
            await session.refresh(customer)

            if card_dao is not None:
                await session.refresh(card_dao)

            return customer, card_dao
        

    async def attach_card_to_customer(
        self,
        customer_id: int,
        card_id: int
    ) -> tuple[CustomerDAO, CardDAO]:
        """
        Attach an existing card to an existing customer in the database.

        Associates the card identified by `card_id` with the customer identified
        by `customer_id`. Both entities must already exist in the database.

        Args:
            customer_id (int): Unique identifier of the customer.
            card_id (int): Unique identifier of the card to attach.

        Returns:
            tuple[CustomerDAO, CardDAO]: A tuple containing:
                - CustomerDAO: The updated customer instance.
                - CardDAO: The attached card instance.

        Raises:
            NotFoundError: If no customer with the given `customer_id` exists
                or if no card with the given `card_id` exists.
            ConflictError: If the card with the given `card_id` is already
                attached to a customer.
        """
        async with await self._get_session() as session:

            customer = await session.get(CustomerDAO, customer_id)
            find_or_throw_not_found(
                [customer] if customer else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )

            card = await session.get(CardDAO, card_id)
            find_or_throw_not_found(
                    [card] if card else [],
                lambda _: True,
                f"Card with id '{card_id}' not found"
            )
            
            if card.customer_id == customer.id:
                return customer, card

            # If the card is already attached to another customer
            if card.customer_id is not None:
                throw_conflict(
                    f"Card with id '{card_id}' is already attached to a customer"
                )

            # Detach previous card if exists
            stmt = select(CardDAO).filter_by(customer_id=customer_id)
            result = await session.execute(stmt)
            previous_card = result.scalars().first()

            if previous_card and previous_card.cardId != card.cardId:
                previous_card.customer_id = None
                await session.flush()

            # Attach card
            card.customer_id = customer.id

            await session.commit()
            await session.refresh(card)
            await session.refresh(customer)

            return customer, card
        
    async def delete_customer(self, customer_id: int) -> bool: 
        """
        Delete a customer and its associated card from the database.

        Removes the customer identified by `customer_id`. If a card is
        associated with the customer, the card is deleted as well within
        the same transaction.

        Args:
            customer_id (int): Unique identifier of the customer to delete.

        Returns:
            bool: True if the customer was successfully deleted.

        Raises:
            NotFoundError: If no customer with the given `customer_id` exists.
        """
        async with await self._get_session() as session:
            customer = await session.get(CustomerDAO, customer_id)
            find_or_throw_not_found(
                [customer] if customer else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )
            cardRepository_instance = CardRepository(session=session)
            card = await cardRepository_instance.get_card_by_customer_without_raise_notfounderror(customer_id)
            if card is not None:
                await session.delete(card)

            await session.delete(customer)
            await session.commit()
            return True
    

    async def get_customer(self, customer_id: int) -> CustomerDAO:
        """
        Retrieve a customer by its unique identifier.

        Fetches the customer with the given `customer_id` from the database.
        If the customer does not exist, a `NotFoundError` is raised.

        Args:
            customer_id (int): Unique identifier of the customer to retrieve.

        Returns:
            CustomerDAO: The requested customer if found.

        Raises:
            NotFoundError: If no customer with the given `customer_id` exists.
        """
        async with await self._get_session() as session:
            user = await session.get(CustomerDAO, customer_id)
            return find_or_throw_not_found(
                [user] if user else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )
        

    async def list_customers(self) -> list[CustomerDAO]:
        """
        Retrieve all customer.

        Fetches the customers from the database.

        Returns:
            list[CustomerDAO]: The list of customers.
        """
        async with await self._get_session() as session:
            result = await session.execute(select(CustomerDAO))
            return result.scalars().all()
        
    async def update_customer(self, customer_id: int, updated_name: str, updated_card: UpdateCardDTO) -> CustomerDAO:
        """
        Update customer information and manage the associated card.

        Updates the customer's name and optionally updates the card
        association according to the provided `updated_card` payload.

        Card update behavior:
        - If `updated_card` is None, the card association is left unchanged.
        - If `updated_card.cardId` is None, the existing card (if any) is removed.
        - If `updated_card.cardId` refers to a non-existing card, a new card is created and attached to the customer.
        - If `updated_card.cardId` refers to an existing card:
            - If the card is already attached to another customer, a `ConflictError` is raised.
            - If the customer already has a card, the existing association is updated or replaced accordingly.
            - If the customer has no card, the card is attached.

        All changes are persisted within a single transaction.

        Args:
            customer_id (int): Unique identifier of the customer to update.
            updated_name (str): New name to assign to the customer.
            updated_card (UpdateCardDTO): Card update payload defining how the customer's card association should be modified.

        Returns:
            CustomerDAO: The updated customer instance.

        Raises:
            NotFoundError: If no customer with the given `customer_id` exists.
            ConflictError: If the specified card is already attached to another customer.
        """
        async with await self._get_session() as session:
            db_customer = await session.get(CustomerDAO, customer_id)
            if not db_customer:
                find_or_throw_not_found(
                    [db_customer] if db_customer else [],
                    lambda _: True,
                    f"Customer with id '{customer_id}' not found"
                )

            cardRepository_instance = CardRepository(session=session)
            
            if updated_card is None:
                pass
            elif updated_card.card_id is None:
                # remove card if it exists
                card = await cardRepository_instance.get_card_by_customer(customer_id)
                if card is not None:
                    await session.delete(card)
            else:
                body_card_dao = await cardRepository_instance.get_card(updated_card.card_id)
                
                customer_card_dao = await cardRepository_instance.get_card_by_customer_without_raise_notfounderror(customer_id)
                
                if(updated_card.points<0):
                    throw_bad_request("Card points must be positive") 

                if body_card_dao is None:
                    # the updated card does not exist
                    if customer_card_dao is not None:
                        # the customer already had a card, remove it and attach the new one
                        await cardRepository_instance.delete_card(customer_card_dao.cardId)
                        await cardRepository_instance.create_and_attach_new_card_to_customer(customer_id, updated_card.card_id, updated_card.points)
                    else:
                        # the customer had not a card, attach the new one
                        await cardRepository_instance.create_and_attach_new_card_to_customer(customer_id, updated_card.card_id, updated_card.points)
                else:
                    # the updated card existed
                    if customer_id != body_card_dao.customer_id and await cardRepository_instance.is_attached(body_card_dao.cardId) is True:
                        throw_conflict(f"Card with id {updated_card.card_id} is already attached to another customer")
                    if customer_card_dao is not None:
                        # the customer already has a card
                        if body_card_dao.cardId != customer_card_dao.cardId:
                            # the card is different, remove the old one and attach the new one
                            await cardRepository_instance.delete_card(customer_card_dao.cardId)
                            await cardRepository_instance.update_and_attach_card_to_customer(customer_id, body_card_dao.cardId, updated_card.points)
                        else:
                            # the card is the same, just update the points
                            await cardRepository_instance.update_card_without_sum(body_card_dao.cardId, updated_card.points)
                    else:
                        # the customer had not a card, attach the existing one
                        await cardRepository_instance.update_and_attach_card_to_customer(customer_id, updated_card.card_id, updated_card.points)
            
            db_customer.name = updated_name
            await session.commit()
            return db_customer