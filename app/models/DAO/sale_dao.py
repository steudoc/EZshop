from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.models.sale_status import SaleStatus


class SaleDAO(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(SaleStatus), default=SaleStatus.OPEN)
    discount_rate = Column(Float, default=0.0)
    lines = relationship("SaleLineDAO", back_populates="sale", cascade="all, delete-orphan")


class SaleLineDAO(Base):
    __tablename__ = "sale_lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_barcode = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    discount_rate = Column(Float, default=0.0)
    sale = relationship("SaleDAO", back_populates="lines") 