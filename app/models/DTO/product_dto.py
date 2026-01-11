from pydantic import BaseModel, Field
from typing import Optional

# all fields are optional to support update request that
# contains only some fields (checks will be performed later)
class ProductDTO(BaseModel):
    id: Optional[int] = None
    description: Optional[str] = None
    barcode: Optional[str] = None
    price_per_unit: Optional[float] = None
    note: Optional[str] = None
    quantity: Optional[int] = None
    position: Optional[str] = None
