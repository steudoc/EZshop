from pydantic import BaseModel, Field
from typing import Optional

class SystemInfoDTO(BaseModel):
    id: Optional[int] = None
    balance: float

class SystemInfoResponseDTO(BaseModel):
    balance: float