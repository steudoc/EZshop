from fastapi import APIRouter, status, Depends
from app.models.DTO.customer_dto import CardDTO
from app.models.user_type import UserType
from app.controllers.card_controller import CardController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Query
from app.utils import throw_not_found, throw_bad_request, throw_customer_card_error


router = APIRouter(prefix=ROUTES['V1_CUSTOMERS_CARDS'], tags=["Cards"])
controller = CardController()

@router.post("", 
    response_model=CardDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def create_card():
    """
    Create a new card with 0 points.

    - Permissions: Administrator, Shop manager, Cashier
    - Returns: Created card as CardDTO
    - Status code: 201 Created
    """
    return await controller.create_card()

@router.patch("/{card_id}", 
    response_model=CardDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager, UserType.Cashier]))])
async def modify_points_card(
    card_id: str,
    points: int = Query(description="Points to add (positive) or remove (negative)")
):
    """
    Add or remove points from a loyalty card.

    - Permissions: Administrator, Shop manager, Cashier
    - Returns: Created card as CardDTO
    - Raises:
        - BadRequestError: when card_id is missing or invalid
        - CustomerCardError: when trying to remove more points than there are in the card
    - Status code: 200 Customer card points successfully updated
    """

    if not card_id or not card_id.isdigit():
        throw_bad_request("Card ID must be an integer string")


    card = await controller.get_card(card_id)

    if points+card.points<0:
        throw_customer_card_error("Insufficient points on the card")
    
    return await controller.modify_points_card(card_id=card_id, points=points)

    