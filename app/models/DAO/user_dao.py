from sqlalchemy import Column, Integer, String, Enum
from app.models.user_type import UserType
from app.database.database import Base


class UserDAO(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    type = Column(Enum(UserType), nullable=False)

