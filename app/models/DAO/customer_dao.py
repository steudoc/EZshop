from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base


class CustomerDAO(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    card = relationship(
        "CardDAO",
        back_populates="customer",
        uselist=False,
        single_parent=True 
    )

