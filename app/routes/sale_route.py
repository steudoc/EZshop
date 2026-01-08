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

# --- HELPER FUNCTIONS FOR VALIDATION ---

def _validate_sale_id(sale_id: int):
    """Validates that sale_id is a positive integer."""
    if sale_id is None or sale_id <= 0:
        throw_bad_request("Invalid sale id: must be a positive integer")

def _validate_positive_amount(amount: float, error_msg: str = "Amount must be a positive integer"):
    """Validates that amount is positive."""
    if amount is None or amount <= 0:
        throw_bad_request(error_msg)

def _validate_barcode(barcode: str) -> str:
    """
    Validates barcode: 
    - Not empty/whitespace
    - Numeric
    - Length 12-14 digits
    Returns stripped barcode.
    """
    if not barcode or not barcode.strip():
        throw_bad_request("Invalid barcode: cannot be empty or whitespace")
    
    clean_barcode = barcode.strip()
    
    if not clean_barcode.isdigit():
        throw_bad_request("Invalid barcode: non-numeric")

    # Check length constraint (12-14 digits)
    if not (12 <= len(clean_barcode) <= 14):
        throw_bad_request("Invalid barcode: must be between 12 and 14 digits")
        
    return clean_barcode

def _validate_discount(rate: float):
    """Validates discount rate is between 0 and 1."""
    if rate is None or not (0.0 <= rate < 1.0):
        throw_bad_request("Discount must be between 0 and 1")

# --- ROUTES ---


@router.get("/{sale_id}", response_model=SaleDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
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
    _validate_sale_id(sale_id)
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
    _validate_sale_id(sale_id)
        
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
    _validate_sale_id(sale_id)
    _validate_positive_amount(amount, "Amount must be a positive integer")
    clean_barcode = _validate_barcode(barcode)
        
    
    item_dto = SaleLineDTO(sale_id=sale_id, product_barcode=clean_barcode, quantity=amount)
    await controller.add_item_to_sale(item_dto)    
   
    return BooleanDTO(value=True)

@router.patch("/{sale_id}/discount", response_model=BooleanDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def update_sale_discount(sale_id: int, discount_rate: float):
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
    
    _validate_sale_id(sale_id)
    
    
    _validate_discount(discount_rate)

    sale_discount_dto = SaleDiscountDTO(id=sale_id, discount_rate=discount_rate)
    result = await controller.update_sale_discount(sale_discount_dto)    
    return result

@router.patch("/{sale_id}/items/{product_barcode}/discount", response_model=BooleanDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def update_sale_line_discount(sale_id: int, product_barcode: str, discount_rate: float):
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
    _validate_sale_id(sale_id)
    clean_barcode = _validate_barcode(product_barcode)
    _validate_discount(discount_rate)

    sale_line_discount_dto = SaleLineDiscountDTO(sale_id=sale_id, product_barcode=clean_barcode, discount_rate=discount_rate)
    result = await controller.update_sale_line_discount(sale_line_discount_dto)

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
    _validate_sale_id(sale_id)
    _validate_positive_amount(amount, "Amount must be a positive integer")
    clean_barcode = _validate_barcode(barcode)

    item_dto = SaleLineDTO(sale_id=sale_id, product_barcode=clean_barcode, quantity=amount)
    result = await controller.delete_item_from_sale(item_dto)
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
    _validate_sale_id(sale_id)
        
    result = await controller.close_sale(sale_id)    
    return result

@router.patch("/{sale_id}/pay", 
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
   
    _validate_sale_id(sale_id)
    
    
    _validate_positive_amount(cash_amount, "Amount paid must be positive")
        
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
    _validate_sale_id(sale_id)
        
    return await controller.get_sale_points(sale_id)