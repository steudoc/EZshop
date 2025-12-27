from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.sale_status import SaleStatus 


class SaleLineDTO(BaseModel):
    id: Optional[int] = None 
    sale_id: int
    product_barcode: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    price_per_unit: float = Field(default=0.0)
    discount_rate: float = Field(default=0.0)


class SaleDTO(BaseModel):
    id: Optional[int] = None 
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    status: SaleStatus = SaleStatus.OPEN 
    discount_rate: float = Field(default=0.0)
    lines: List[SaleLineDTO] = Field(default_factory=list)

class SaleDiscountDTO(BaseModel):
    id: int
    discount_rate: float

class SaleLineDiscountDTO(BaseModel):
    sale_id: int
    product_barcode: str
    discount_rate: float

class SalePaymentDTO(BaseModel):
    sale_id: int
    amount_paid: float
class SaleChangeDTO(BaseModel):
    change: float   

class SalePointsDTO(BaseModel):
    points: int


