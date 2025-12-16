from sqlalchemy import Column, Integer, String
from app.database.database import Base

class SaleDAO(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="CLOSED")  # default value for testing
