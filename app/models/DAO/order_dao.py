from sqlalchemy import Column, Integer, String, Enum, Float, DateTime, CheckConstraint
from app.models.order_status import OrderStatus
from app.database.database import Base


class OrderDAO(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_barcode = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    issue_date = Column(DateTime, nullable=True)