from fastapi import APIRouter, HTTPException, status, Depends
from app.models.DTO.system_dto import SystemInfoResponseDTO
from app.models.user_type import UserType
from app.controllers.system_controller import SystemController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response
from app.models.errors.balance_error import BalanceError


router = APIRouter(prefix=ROUTES['V1_BALANCE'], tags=["Accounting"])
controller = SystemController()

@router.post("/reset",
    status_code=status.HTTP_205_RESET_CONTENT,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def reset_balance():
    # TODO: aggiungere commenti
    await controller.reset_balance()
    return Response(status_code=status.HTTP_205_RESET_CONTENT)


@router.post("/set",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def set_balance(amount: float):
    # TODO: aggiungere commenti
    if amount < 0: 
        raise BalanceError('Balance cannot be negative')
    await controller.set_balance(amount)
    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/", 
    response_model=SystemInfoResponseDTO,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def get_balance():
    # TODO: aggiungere commenti
    return await controller.get_balance()