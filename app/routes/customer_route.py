from app.models.errors.notfound_error import NotFoundError
from fastapi import APIRouter, status, Depends, Response
from app.models.DTO.customer_dto import CustomerDTO, UpdateCustomerDTO
from app.models.user_type import UserType
from app.controllers.customer_controller import CustomerController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from app.utils import throw_bad_request
from typing import List


router = APIRouter(prefix=ROUTES['V1_CUSTOMERS'], tags=["Customers"])
controller = CustomerController()

@router.post("/", 
    response_model=CustomerDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def create_customer(customer: CustomerDTO):
    """
    Create a new customer given a name and optionally a card_id.

    - Permissions: Administrator, Shop manager, Cashier
    - Returns: Created card as CardResponseDTO
    - Status code: 201 Created
    """
    if customer.name is None or customer.name == "":
        throw_bad_request("Customer name is required")

    return await controller.create_customer(customer)


@router.patch("/{customer_id}/attach-card/{card_id}", 
    response_model=CustomerDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def attach_card_to_customer(customer_id:str, card_id:str):
    """
    Attach a card with card_id to a customer with customer_id.

    - Permissions: Administrator, Shop manager, Cashier
    - Returns: Created card as CardResponseDTO
    - Status code: 201 Created
    """

    if not card_id or not card_id.isdigit():
        throw_bad_request("Card ID must be an integer string")
    if not customer_id or not customer_id.isdigit():
        throw_bad_request("Customer ID must be an integer string")

    return await controller.attach_card_to_customer(customer_id=customer_id, card_id=card_id)


@router.delete("/{customer_id}", 
               status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def delete_user(customer_id: int):
    """
    Delete a customer by ID, if a card is attached, the card will deleted as well.

    - Permissions: Administrator, Shop manager, Cashier
    - Path parameter: customer_id (int)
    - Returns: No content (204) on success
    - Raises:
      - NotFoundError: when the customer to delete does not exist
    - Status code: 204 No Content
    """
    success = await controller.delete_user(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{customer_id}",
            response_model=CustomerDTO,
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def get_customer(customer_id: int):
    """
    Retrieve a single customer by ID.

    - Permissions: Administrator, Shop manager, Cashier
    - Path parameter: customer_id (int)
    - Returns: CustomerDTO for the requested customer
    - Raises:
      - NotFoundError: when the customer does not exist
    - Status code: 200 OK
    """
    if customer_id<0:
        throw_bad_request("Customer ID must be a positive integer")
    customer = await controller.get_customer(customer_id)
    if not customer:
        raise NotFoundError("Customer not found")
    return customer


@router.get("/", response_model=List[CustomerDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def list_users():
    """
    List all customers.

    - Permissions:  Administrator, Shop manager, Cashier
    - Returns: List of CustomerDTO
    - Status code: 200 OK
    """
    return await controller.list_customers()



@router.put("/{customer_id}", response_model=CustomerDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def update_customer(customer_id: int, customer: UpdateCustomerDTO):
    """
    Update an existing customer.

    - Permissions: Administrator, Shop manager, Cashier
    - Path parameter: customer_id (int)
    - Request body: CustomerDTO (fields to update)
    - Returns: Updated customer as CustomerDTO
    - Raises:
      - NotFoundError: when the user to update does not exist
      - BadRequestError: when the customer input is invalid
      - ConflictError: when there is a conflict updating the customer
    - Status code: 201 Created
    """
    if customer.name == "":
        throw_bad_request("Customer name cannot be empty")

    updated = await controller.update_customer(customer_id, customer)
    if not updated:
        raise NotFoundError("Customer not found")
    return updated