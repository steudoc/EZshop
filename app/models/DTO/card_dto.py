from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

class CardDTO(BaseModel):
    cardId: Optional[int] = None
    points: int
    customer: Optional["CustomerDTO"] = None

class CardResponseDTO(BaseModel):
    cardId: Optional[int] = None
    points: int