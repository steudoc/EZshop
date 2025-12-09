""" Return route module.
This module defines the return endpoints for the API, specifically handling
return operations. It provides a RESTful interface for users to process returns."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.DTO.return_dto import ReturnCreateDTO, ReturnResponseDTO
from app.models.user_type import UserType
from app.controllers.return_controller import ReturnController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response
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
      - BadRequestError: when mandatory fields (sale_id) are missing or invalid
    - Status code: 201 Created
    """
    if not sale_id:
        raise BadRequestError('invalid id')
    
    try:
        sale_id_int = int(sale_id)
        if sale_id_int <= 0:
            raise BadRequestError('invalid id')
    except ValueError:
        raise BadRequestError('invalid id')
    
    return await controller.start_return(sale_id_int)

@router.get("/{return_id}", response_model=ReturnResponseDTO,
            dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def get_user(return_id: int):
    """
    Retrieve a single return by ID.

    - Permissions: Administrator, ShopManager, Cashier
    - Path parameter: sale_id (int)
    - Returns: ReturnResponseDTO for the requested user
    - Raises:
      - NotFoundError: when the return does not exist
    - Status code: 200 OK
    """
    return_tx = await controller.get_return_by_id(return_id)
    if not return_tx:
        raise NotFoundError("Return transaction not found")
    return return_tx







