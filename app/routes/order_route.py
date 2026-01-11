from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.DTO.order_dto import OrderDTO
from app.models.DTO.boolean_dto import BooleanDTO
from app.models.user_type import UserType
from app.controllers.order_controller import OrderController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES


router = APIRouter(prefix=ROUTES['V1_ORDERS'], tags=["Orders"])
controller = OrderController()

@router.post("/", 
    response_model=OrderDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def create_issued_order(order_dto: OrderDTO):
    """Create a new issued order"""
    return await controller.create_issued_order(order_dto)


@router.get("/", 
    response_model=List[OrderDTO],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def list_orders():
    """Retrieve all orders"""
    return await controller.list_orders()


@router.post("/payfor", 
    response_model=OrderDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def create_paid_order(order_dto: OrderDTO):
    """Create a new paid order"""
    return await controller.create_paid_order(order_dto)


@router.patch("/{order_id}/pay", 
    response_model=BooleanDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def pay_order(order_id: int):
    """Mark an order as paid"""
    await controller.pay_order(order_id)
    return BooleanDTO(
        success=True
    )


@router.patch("/{order_id}/arrival", 
    response_model=BooleanDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def complete_order(order_id: int):
    """Mark an order as completed upon arrival"""
    await controller.complete_order(order_id)
    return BooleanDTO(
        success=True
    )
