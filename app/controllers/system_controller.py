from app.repositories.system_repository import SystemRepository
from app.models.DTO.system_dto import SystemInfoDTO, SystemInfoResponseDTO
from app.services.mapper_service import systemdao_to_dto, systemdao_to_responsedto
from app.utils import find_or_throw_not_found
from app.models.errors.balance_error import BalanceError

class SystemController:
    def __init__(self):
        self.repo = SystemRepository()

    async def _create_system_info(self, system_info_dto: SystemInfoDTO) -> SystemInfoDTO: 
        """Create system info"""
        created = await self.repo.create_system_info(system_info_dto.balance)
        return systemdao_to_dto(created)
    
    async def set_balance(self, amount: float): 
        """Sets the system balance to the provided amount"""
        if amount < 0: 
            raise BalanceError('Balance cannot be negative')
        await self._create_system_info(
            SystemInfoDTO(
                balance=amount
            )
        )
    
    async def reset_balance(self): 
        """Resets the balance value to 0"""
        await self._create_system_info(
            SystemInfoDTO(
                balance=0.0
            )
        )
    
    async def get_balance(self) -> SystemInfoResponseDTO: 
        """Returns the current balance value of the system"""
        dao = await self.repo.get_last_system_info()
        return systemdao_to_responsedto(
            find_or_throw_not_found(
                [dao] if dao else [],
                lambda _: True,
                f"System info not found"
            )
        )