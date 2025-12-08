from app.repositories.system_repository import SystemRepository
from app.models.DTO.system_dto import SystemInfoDTO, SystemInfoResponseDTO
from app.services.mapper_service import systemdao_to_responsedto

class SystemController:
    def __init__(self):
        self.repo = SystemRepository()

    async def create_system_info(self, system_info_dto: SystemInfoDTO) -> SystemInfoResponseDTO: 
        """Create system info"""
        created = await self.repo.create_system_info(system_info_dto.balance)
        return systemdao_to_responsedto(created)
    
    async def get_system_info(self, system_info_id: int) -> SystemInfoResponseDTO: 
        """"Get system info by id - throws NotFoundError if not found"""
        dao = await self.repo.get_system_info(system_info_id)
        return systemdao_to_responsedto(dao)
    
    async def set_balance(self, amount: float): 
        """Sets the system balance to the provided amount"""
        await self.create_system_info(
            SystemInfoDTO(
                balance=amount
            )
        )
    
    async def reset_balance(self): 
        """Resets the balance value to 0"""
        await self.create_system_info(
            SystemInfoDTO(
                balance=0.0
            )
        )
    
    async def get_balance(self) -> SystemInfoResponseDTO: 
        """Returns the current balance value of the system"""
        return await self.get_system_info(-1)