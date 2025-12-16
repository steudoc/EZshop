from pydantic import BaseModel, Field
from typing import Optional

class CardDTO(BaseModel):
    cardId: Optional[int] = None
    points: int


class UpdateCardDTO(BaseModel):
    cardId: Optional[int] = None
    points: Optional[int] = None

class CustomerDTO(BaseModel):
    id: Optional[int] = None
    name: str
    card: Optional[CardDTO] = None



class UpdateCustomerDTO(BaseModel):
    id: Optional[int] = None
    name: str
    card: Optional[UpdateCardDTO] = None