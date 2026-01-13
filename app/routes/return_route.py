from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.DTO.boolean_dto import BooleanDTO
from app.models.DTO.return_dto import ReturnCreateDTO, ReturnReimburseDTO, ReturnResponseDTO, ReturnItemDTO
from app.models.user_type import UserType
from app.controllers.return_controller import ReturnController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController
from app.utils import throw_bad_request, throw_invalid_state, throw_not_found

from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError

router = APIRouter(prefix=ROUTES['V1_RETURNS'], tags=["Returns"])
controller = ReturnController()
    
@router.post("/", 
    response_model=ReturnResponseDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def create_return_transaction(sale_id: Optional[str] = Query(None)):
    """
    Create a new return transaction.

    - Permissions: Administrator, ShopManager, Cashier
    - Query parameter: sale_id (ID of the sale to return)
    - Returns: Created return as ReturnResponseDTO
    - Raises:
      - BadRequestError: when sale_id is missing or invalid
    - Status code: 201 Created
    """
    if not sale_id:
        throw_bad_request('invalid id')
    
    try:
        sale_id_int = int(sale_id)
        if sale_id_int <= 0:
            throw_bad_request('invalid id')
    except ValueError:
        throw_bad_request('invalid id')
    
    return await controller.start_return(sale_id_int)

@router.get("/", response_model=List[ReturnResponseDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def list_returns():
    """
    List all returns transactions.

    - Permissions: Administrator, ShopManager, Cashier
    - Returns: List of ReturnResponseDTO
    - Status code: 200 OK
    """
    return await controller.get_all_returns()

@router.get("/{return_id}", response_model=ReturnResponseDTO,
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def get_return_by_id(return_id: int):
    """
    Retrieve a single return by ID.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: return_id (int)
    - Returns: ReturnResponseDTO for the requested return
    - Raises:
      - BadRequestError: when the return_id is invalid or missing
      - NotFoundError: when the return does not exist
    - Status code: 200 OK
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    return return_tx

@router.delete("/{return_id}", 
               status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def delete_return(return_id: int):
    """
    Delete a return by ID.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: return_id (int)
    - Returns: No content (204) on success
    - Raises:
      - NotFoundError: when the return to delete does not exist
      - BadRequestError: when the return_id is invalid or missing
      - InvalidStateError: when the return cannot be deleted due to its current state REIMBURSED
    - Status code: 204 No Content
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    elif return_tx.status == "REIMBURSED":
        throw_invalid_state("Cannot delete a reimbursed return")

    success = await controller.delete_return(return_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/sale/{sale_id}", response_model=List[ReturnResponseDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def get_returns_by_sale(sale_id: int):
    """
    List all returns associated with a sale ID.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Returns: List of ReturnResponseDTO associated with the sale
    - Raises:
      - BadRequestError: when the sale_id is invalid or missing
    - Status code: 200 OK
    """
    if not sale_id or sale_id <= 0:
        throw_bad_request('Invalid return id')

    return await controller.get_returns_by_sale(sale_id)

@router.post("/{return_id}/items", 
    response_model=BooleanDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def add_item(return_id: int, barcode: str, amount: int):
    """
    Add a product to a return transaction.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: return_id (int)
    - Request body: ReturnItemDTO (product_barcode, quantity, price_per_unit)
    - Returns: BooleanDTO with success status
    - Raises:
      - BadRequestError: when return_id is invalid or missing
      - NotFoundError: when the return does not exist
      - InvalidStateError: when the return is already closed
    - Status code: 201 Created
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')
    
    if amount <= 0:
        throw_bad_request('Invalid amount')

    product_controller = ProductController()
    product = await product_controller.get_product_by_barcode(barcode)
    if not product:
        throw_not_found("Product not found")

    item_dto = ReturnItemDTO(
        product_barcode=barcode,
        quantity=amount,
        price_per_unit=product.price_per_unit
    )

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    elif return_tx.status == "CLOSED":
        throw_invalid_state("Cannot modify a closed return")
    
    # Validate that the quantity being returned doesn't exceed the quantity in the sale
    sale_controller = SaleController()
    sale = await sale_controller.get_sale(return_tx.sale_id)
    if not sale:
        throw_not_found("Sale not found")
    
    # Find the line item in the sale with the same barcode
    sale_line = next((line for line in sale.lines if line.product_barcode == barcode), None)
    if not sale_line:
        throw_bad_request("Product not in sale")
    
    # Calculate total quantity being returned for this barcode
    total_return_quantity = amount
    for line in return_tx.lines:
        if line.product_barcode == barcode:
            total_return_quantity += line.quantity
            break
    
    # Check that total return quantity doesn't exceed sale quantity
    if total_return_quantity > sale_line.quantity:
        throw_bad_request("Cannot return more items than were sold")
    
    updated_return = await controller.add_item(return_id, item_dto)
    return BooleanDTO(success=True)

@router.delete("/{return_id}/items", 
               status_code=status.HTTP_202_ACCEPTED, 
               dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def delete_return(return_id: int, barcode: str, amount: int):
    """
    Remove a product from a return transaction.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: return_id (int)
    - Returns: BooleanDTO with success status
    - Raises:
      - NotFoundError: when the return does not exist
      - BadRequestError: when the return_id is invalid or missing
      - InvalidStateError: when the return cannot be modified due to its current state CLOSED
    - Status code: 202 Accepted
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    elif return_tx.status == "CLOSED":
        throw_invalid_state("Cannot remove items from a closed return")

    await controller.remove_item(return_id, barcode, amount)
    return BooleanDTO(success=True)

@router.patch("/{return_id}/close", 
              response_model=BooleanDTO,    
              dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def close_return(return_id: int):
    """
    Close a return transaction.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: return_id (int)
    - Returns: BooleanDTO with success status
    - Raises:
      - NotFoundError: when the return does not exist
      - BadRequestError: when the return_id is invalid or missing
      - InvalidStateError: when the return cannot be closed due to its current state
    - Status code: 200 OK
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    elif return_tx.status == "CLOSED":
        throw_invalid_state("Invalid return state to be closed")

    success = await controller.close_return(return_id)
    return BooleanDTO(success=True)

@router.patch("/{return_id}/reimburse", 
              response_model=ReturnReimburseDTO,
              dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def reimburse_return(return_id: int):
    """
    Reimburse a return transaction.

    - Permissions: Administrator, ShopManager
    - Path parameter: return_id (int)
    - Returns: Refund amount
    - Raises:
      - NotFoundError: when the return does not exist
      - BadRequestError: when the return_id is invalid or missing
      - InvalidStateError: when the return cannot be reimbursed due to its current state
    - Status code: 200 OK
    """
    if not return_id or return_id <= 0:
        throw_bad_request('Invalid return id')

    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        throw_not_found("Return not found")
    elif return_tx.status != "CLOSED":
        throw_invalid_state("Return must be closed before reimbursement")

    return await controller.reimburse_return(return_id)









