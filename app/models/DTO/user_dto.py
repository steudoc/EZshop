from pydantic import BaseModel, Field
from typing import Optional
from app.models.user_type import UserType

class UserDTO(BaseModel):
    id: Optional[int] = None
    username: str = Field(min_length=5)
    password: Optional[str] = None
    type: Optional[UserType] = None

class UserLoginDTO(BaseModel):
    username: str = Field(min_length=5)
    password: str = Field(min_length=5)

class UserResponseDTO(BaseModel):
    id: Optional[int] = None
    username: str
    type: Optional[UserType] = None

class UserCreateDTO(BaseModel):
    id: Optional[int] = None
    username: str = Field(min_length=5)
    password: str = Field(min_length=5)
    type: UserType