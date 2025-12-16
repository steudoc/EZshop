from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- Request DTOs ---

class ReturnDTO(BaseModel):
    """Representation of a return transaction"""
    id: Optional[int] = None
    sale_id: int = Field(..., description="ID of the sale to return products from")
    status: Optional[str] = Field("OPEN", description="Status of the return transaction")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp of the return transaction")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp of the return transaction")
    lines: List['ReturnLineDTO'] = Field([], description="List of return line items")

class ReturnCreateDTO(BaseModel):
    id: Optional[int] = None
    sale_id: int = Field(..., description="ID of the sale to return products from")
    status: Optional[str] = Field("OPEN", description="Status of the return transaction")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp of the return transaction")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp of the return transaction")
    lines: List['ReturnLineDTO'] = Field([], description="List of return line items")

class ReturnItemDTO(BaseModel):
    id: Optional[int] = None
    product_barcode: str = Field(..., description="Barcode of the product being returned")
    quantity: int = Field(..., description="Quantity of the product being returned")
    price_per_unit: float = Field(..., description="Price per unit of the product being returned")


class ReturnCloseDTO(BaseModel):
    """Used to close a return transaction"""
    closed_at: Optional[datetime] = Field(None, description="Data di chiusura del reso")


class ReturnReimburseDTO(BaseModel):
    """Used to reimburse a return transaction"""
    refund_amount: float = Field(..., description="Amount to reimburse for the return transaction")

# --- Response DTOs ---

class ReturnLineDTO(BaseModel):
    """Representation of a return line item"""
    id: Optional[int]
    return_id: Optional[int]
    product_barcode: str
    quantity: int
    price_per_unit: float


class ReturnResponseDTO(BaseModel):
    """Response representation of a return transaction"""
    id: int
    sale_id: int
    status: str
    created_at: datetime
    closed_at: Optional[datetime]
    lines: List[ReturnLineDTO] = Field([], description="List of return line items")








