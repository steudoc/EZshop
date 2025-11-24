from sqlalchemy import Column, Integer, Float
from app.database.database import Base


class SystemInfoDAO(Base):
    __tablename__ = "system_info"
    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False, default=0.0)