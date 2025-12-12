from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.order_status import OrderStatus

class OrderDTO(BaseModel):
    id: Optional[int] = None
    product_barcode: str
    quantity: int
    price_per_unit: float
    status: Optional[OrderStatus] = None
    issue_date: Optional[datetime] = None
