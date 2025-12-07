from fastapi import APIRouter, HTTPException, status, Depends
from app.models.DTO.card_dto import CardResponseDTO
from app.models.user_type import UserType
from app.controllers.card_controller import CardController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES


router = APIRouter(prefix=ROUTES['V1_CUSTOMERS_CARDS'], tags=["Cards"])
controller = CardController()

@router.post("/", 
    response_model=CardResponseDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def create_card():
    """
    Create a new card with 0 points.

    - Permissions: Administrator, Shop manager, Cashier
    - Request body: CardDTO (contains cardId and points)
    - Returns: Created card as CardDTO
    - Status code: 201 Created
    """
    return await controller.create_card()
    