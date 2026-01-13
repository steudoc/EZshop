from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.DTO.boolean_dto import BooleanDTO
from app.models.user_type import UserType
from app.models.DTO.product_dto import ProductDTO
from app.controllers.product_controller import ProductController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response
from app.utils import throw_bad_request, throw_not_found

from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError


router = APIRouter(prefix=ROUTES['V1_PRODUCTS'], tags=["Products"])
controller = ProductController()


@router.post("/", 
    response_model=ProductDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def create_product(product: ProductDTO):
	"""
    Create a new product.

    - Permissions: Administrator, ShopManager
    - Request body: ProductDTO (contains id, description, barcode...)
    - Returns: Created product as ProductDTO
    - Raises:
      - BadRequestError: if mandatory fields (description, barcode..) are missing or invalid
	  - ConflictError: if provided barcode is already used by another product
    - Status code: 201 Created
    """
	return await controller.create_product(product)


@router.get("/", response_model=List[ProductDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager, UserType.Cashier]))])
async def list_products():
	"""
    List all products.

    - Permissions: Administrator, ShopManager, Cashier
    - Returns: List of products as List of ProductDTO
	- Status code: 200 OK
    """
	return await controller.list_products()


@router.get("/search", response_model=List[ProductDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager]))])
async def search_products_by_description(query: str | None = None):
	"""
    Retrieve all products that contain the given description.

    - Permissions: Administrator, ShopManager
    - Query parameter: query (str)
    - Returns: List of products as List of ProductDTO
    - Status code: 200 OK
    """

	# in the absence of a description, return an empty list
	if (query is None):
		return []

	# retrieve all products by description
	return await controller.get_products_by_description(query)


@router.get("/{product_id}", response_model=ProductDTO,
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager, UserType.Cashier]))])
async def get_product_by_id(product_id: int):
	"""
    Retrieve a single product by id.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: product_id (int)
    - Returns: ProductDTO for the requested product
    - Raises:
      - NotFoundError: if the product with given id does not exist
    - Status code: 200 OK
    """

	# check that id is valid
	if (product_id <= 0):
		throw_bad_request(f"Invalid product id: {product_id}")

	# retrieve product and check if it is found
	product = await controller.get_product_by_id(product_id)
	if (product is None):
		throw_not_found("Product not found")

	return product


@router.get("/barcode/{barcode}", response_model=ProductDTO,
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager]))])
async def get_product_by_barcode(barcode: str):
	"""
    Retrieve a single product by barcode.

    - Permissions: Administrator, ShopManager
    - Path parameter: barcode (str)
    - Returns: ProductDTO for the requested product
    - Raises:
      - NotFoundError: if the product with given id does not exist
	  - BadRequestError: if the barcode is not vaid
    - Status code: 200 OK
    """

	# retrieve product and check if it is found
	product = await controller.get_product_by_barcode(barcode)
	if (product is None):
		throw_not_found("Product not found")

	return product


@router.patch("/{product_id}/position", response_model=BooleanDTO,
			  status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager]))])
async def assign_product_position(product_id: int, position: str):
	"""
    Assigns a new position to the product with the given id 
	(empty string to clear current position).

    - Permissions: Administrator, ShopManager
	- Path parameter: product_id (int)
    - Query parameter: position (str)
    - Returns: BooleanDTO
	- Raises:
      - NotFoundError: if the product with given id does not exist
	  - BadRequestError: if the position format is not valid or id is not valid
	  - ConflictError: if the position is already occupied by another product
    - Status code: 201
    """

	# check that product id is valid
	if (product_id <= 0):
		throw_bad_request(f"Invalid product id: {product_id}")

	# try to move product to new position
	await controller.move_product(product_id, position)

	# if product was updated without any error, then return success
	return BooleanDTO(success=True)


@router.patch("/{product_id}/quantity", response_model=BooleanDTO,
			  status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(authenticate_user([UserType.Administrator, 
													 UserType.ShopManager]))])
async def increment_product_quantity(product_id: int, quantity: int):
	"""
    Increments the quantity of the product with the given id (Decrements
	the quantity if given a negative number). 

    - Permissions: Administrator, ShopManager
	- Path parameter: product_id (int)
    - Query parameter: quantity (int)
    - Returns: BooleanDTO
	- Raises:
      - NotFoundError: if the product with given id does not exist
	  - BadRequestError: if the resulting product quantity is negative 
	  or product id is not valid
    - Status code: 201
    """

	# check that product id is valid
	if (product_id <= 0):
		throw_bad_request(f"Invalid product id: {product_id}")

	# try to increment (or decrement) product quantity
	await controller.increment_product_quantity(product_id, quantity)

	# if quantity was updated without any error, then return success
	return BooleanDTO(success=True)


@router.put("/{product_id}", response_model=BooleanDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def update_product(product_id: int, product: ProductDTO):
	"""
    Update an existing product.

    - Permissions: Administrator, ShopManager
    - Path parameter: product_id (int)
    - Request body: ProductDTO (fields to update)
    - Returns: BooleanDTO
    - Raises:
      - NotFoundError: if the product to update does not exist
	  - BadRequestError: if given product fields are not valid
	  - InvalidStateError: if the product barcode is updated while it has some 
	  shop transaction associated with it (any sale/return/order)
	  - ConflictError: if the barcode is updated but the new barcode is already in use
    - Status code: 201
    """

	# check that product id is valid
	if (product_id <= 0):
		throw_bad_request(f"Invalid product id: {product_id}")

	# check that price_per_unit, if present, is a positive number
	if (product.price_per_unit is not None and product.price_per_unit <= 0):
		throw_bad_request("Price per unit must be greater than 0")

	# check that quantity, if present, is a positive number
	if (product.quantity is not None and product.quantity < 0):
		throw_bad_request("Product quantity must be greater than 0")

	# barcode must be present
	if (product.barcode is None):
		throw_bad_request()

	# try to update product
	product.id = product_id
	await controller.update_product(product)

	# if product was updated without any error, then return success
	return BooleanDTO(success=True)


@router.delete("/{product_id}", 
               status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def delete_product(product_id: int):
	"""
    Delete an existing product.

    - Permissions: Administrator, ShopManager
    - Path parameter: product_id (int)
    - Returns: No content (204) on success
    - Raises:
      - NotFoundError: if the product to delete does not exist
	  - BadRequestError: if given product id is not valid
	  - InvalidStateError: if the product has some 
	  shop transaction associated with it (any sale/return/order)
    - Status code: 204
    """

	# check that product id is valid
	if (product_id <= 0):
		throw_bad_request(f"Invalid product id: {product_id}")

	# attempt to delete product
	await controller.delete_product(product_id)