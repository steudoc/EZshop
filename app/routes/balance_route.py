from fastapi import APIRouter, HTTPException, status, Depends
from app.models.DTO.system_dto import SystemInfoResponseDTO
from app.models.DTO.boolean_dto import BooleanDTO
from app.models.user_type import UserType
from app.controllers.system_controller import SystemController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response


router = APIRouter(prefix=ROUTES['V1_BALANCE'], tags=["Accounting"])
controller = SystemController()

@router.post("/reset",
    status_code=status.HTTP_205_RESET_CONTENT,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def reset_balance():
    """
    Reset the system balance to its default value.

    - Permissions: Administrator
    - Body: none
    - Returns: empty response with status 205
    - Status code: 205 Reset Content
    """
    await controller.reset_balance()
    return Response(status_code=status.HTTP_205_RESET_CONTENT)


@router.post("/set",
    response_model=BooleanDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def set_balance(amount: float):
    """
    Set the system balance to the specified amount.

    - Permissions: Administrator
    - Body parameter: amount (float) - the new balance to assign
    - Returns: BooleanDTO(True) on success
    - Raises:
      - BalanceError: when the provided amount is negative
    - Status code: 201 Created
    """
    await controller.set_balance(amount)
    return BooleanDTO(
        success=True
    )


@router.get("/", 
    response_model=SystemInfoResponseDTO,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def get_balance():
    """
    Retrieve the current system balance.

    - Permissions: Administrator
    - Returns: SystemInfoResponseDTO representing the latest system information
    - Raises:
      - NotFoundError: if no system information record exists
    - Status code: 200 OK
    """
    return await controller.get_balance()