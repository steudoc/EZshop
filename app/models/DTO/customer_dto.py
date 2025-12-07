from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class CustomerDTO(BaseModel):
    id: Optional[int] = None
    name: str = Field(min_length=5)
    card: Optional["CardDTO"] = None
