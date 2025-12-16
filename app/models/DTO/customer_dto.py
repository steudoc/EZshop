from pydantic import BaseModel, Field
from typing import Optional

class CardDTO(BaseModel):
    cardId: Optional[int] = None
    points: int

class CustomerDTO(BaseModel):
    id: Optional[int] = None
    name: str
    card: Optional[CardDTO] = None