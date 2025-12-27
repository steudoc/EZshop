from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from typing import List, Optional
from app.models.DTO.sale_dto import SaleDTO, SaleDiscountDTO, SaleLineDTO, SaleLineDiscountDTO, SalePaymentDTO, SalePointsDTO
from app.models.DTO.boolean_dto import BooleanDTO
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from app.utils import throw_bad_request, throw_not_found, throw_invalid_state
from app.models.user_type import UserType
from app.controllers.sale_controller import SaleController
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError

router = APIRouter(prefix=ROUTES['V1_SALES'], tags=["Sales"])
controller = SaleController()

@router.get("/{sale_id}", response_model=SaleDTO)
async def get_sale(sale_id: int):   
    """
    Retrieve a sale by its ID.

    - Permissions: Public (implicitly, or defined by middleware not shown here)
    - Path parameter: sale_id (int)
    - Returns: SaleDTO representing the sale
    - Raises:
      - BadRequestError: when the sale_id is invalid or missing
      - NotFoundError: when the sale does not exist
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    
        
    return await controller.get_sale(sale_id)

@router.get("/", response_model=List[SaleDTO],
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def list_sales():
    """
    List all sales.

    - Permissions: Administrator, ShopManager, Cashier
    - Returns: List of sales as List of SaleDTO
    - Status code: 200 OK
    """
    return await controller.list_sales()

@router.post("/", status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def create_sale():
    """
    Create a new sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Returns: SaleDTO of the created sale
    - Status code: 201 Created
    """
    return await controller.create_sale()

@router.delete("/{sale_id}",
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def delete_sale(sale_id: int):
    """
    Delete a sale by ID.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Returns: No content (204) on success
    - Raises:
      - BadRequestError: when the sale_id is invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale cannot be deleted (e.g. it is already PAID)
    - Status code: 204 No Content
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
        
    await controller.delete_sale(sale_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{sale_id}/items", status_code=status.HTTP_201_CREATED,    
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def add_item_to_sale(
    sale_id: int, 
    barcode: str, 
    amount: int
):
    """
    Add an item to a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Query parameters: barcode (str), amount (int)
    - Returns: BooleanDTO indicating success
    - Raises:
      - BadRequestError: when parameters are invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is closed or paid
    - Status code: 201 Created
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    if amount <= 0:
        throw_bad_request("Amount must be positive")
        
    item_dto = SaleLineDTO(sale_id=sale_id, product_barcode=barcode, quantity=amount)
    await controller.add_item_to_sale(item_dto)    
   
    return BooleanDTO(value=True)

@router.patch("/{sale_id}/discount", response_model=BooleanDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def update_sale_discount(sale_id: int, discountRate: float):
    """
    Update the discount of a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Query parameter: discountRate (float)
    - Returns: BooleanDTO indicating success
    - Raises:
      - BadRequestError: when parameters are invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is not OPEN
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    if discountRate < 0 or discountRate > 1:
        throw_bad_request("Discount must be between 0 and 1")
        
    sale_discount_dto = SaleDiscountDTO(id=sale_id, discount_rate=discountRate)
    result=await controller.update_sale_discount(sale_discount_dto)    
    return result

@router.patch("/{sale_id}/items/{product_barcode}/discount", response_model=BooleanDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def update_sale_line_discount(sale_id: int, product_barcode: str, discountRate: float):
    """
    Update the discount of a sale line.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameters: sale_id (int), product_barcode (str)
    - Query parameter: discountRate (float)
    - Returns: BooleanDTO indicating success
    - Raises:
      - BadRequestError: when parameters are invalid
      - NotFoundError: when the sale or line does not exist
      - InvalidStateError: when the sale is not OPEN
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    if discountRate < 0 or discountRate > 1:
        throw_bad_request("Discount must be between 0 and 1")
        
    sale_line_discount_dto = SaleLineDiscountDTO(sale_id=sale_id, product_barcode=product_barcode, discount_rate=discountRate)
    result=await controller.update_sale_line_discount(sale_line_discount_dto)

    return result

@router.delete("/{sale_id}/items",status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def delete_item_from_sale(sale_id: int, barcode: str, amount: int):
    """
    Delete an item from a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Query parameters: barcode (str), amount (int)
    - Returns: No content (204) on success
    - Raises:
      - BadRequestError: when parameters are invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is not OPEN
    - Status code: 204 No Content
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    if amount <= 0:
        throw_bad_request("Amount must be positive")    
        
    item_dto = SaleLineDTO(sale_id=sale_id, product_barcode=barcode, quantity=amount)
    result=await controller.delete_item_from_sale(item_dto)
    return result

@router.patch("/{sale_id}/close", 
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def close_sale(sale_id: int):
    """
    Close a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Returns: BooleanDTO indicating success
    - Raises:
      - BadRequestError: when the sale_id is invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is not OPEN
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    result=await controller.close_sale(sale_id)    
    return result

@router.patch("/{sale_id}/pay", # Assuming implementation returns details or just boolean, checked generic return in controller
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def payment(sale_id: int, cash_amount: float):
    """
    Process a payment for a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Query parameter: cash_amount (float)
    - Returns: SaleChangeDTO (Change amount)
    - Raises:
      - BadRequestError: when parameters are invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is not PENDING
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
    if cash_amount <= 0:
        throw_bad_request("Amount paid must be positive")
        
    sale_payment_dto = SalePaymentDTO(sale_id=sale_id, amount_paid=cash_amount)    
    return await controller.process_payment(sale_payment_dto)

@router.get("/{sale_id}/points", response_model=SalePointsDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))]) 
async def get_sale_points(sale_id: int):
    """
    Get the points earned from a sale.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Returns: SalePointsDTO with the points earned
    - Raises:
      - BadRequestError: when the sale_id is invalid
      - NotFoundError: when the sale does not exist
      - InvalidStateError: when the sale is not PAID
    - Status code: 200 OK
    """
    if sale_id <= 0:
        throw_bad_request("Invalid sale id")
        
    return await controller.get_sale_points(sale_id)