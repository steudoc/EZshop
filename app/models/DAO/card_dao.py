from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database.database import Base


class CardDAO(Base):
    __tablename__ = "cards"

    cardId = Column(Integer, primary_key=True, autoincrement=True)
    points = Column(Integer, nullable=False, default=0)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )

    customer = relationship(
        "CustomerDAO",
        back_populates="card",
        uselist=False
        )

