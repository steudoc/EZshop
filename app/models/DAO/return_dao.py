from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base


class ReturnDAO(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    lines = relationship("ReturnLineDAO", back_populates="return_tx", cascade="all, delete-orphan", lazy="selectin")    
    
class ReturnLineDAO(Base):
    __tablename__ = "return_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    product_barcode = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    return_tx = relationship("ReturnDAO", back_populates="lines")







