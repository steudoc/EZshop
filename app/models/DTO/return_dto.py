"""Return DTO Module.
This module defines the Data Transfer Objects (DTOs) for return operations,
facilitating data exchange between different layers of the application."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.user_type import UserType
from app.models.DTO.item_dto import ItemResponseDTO
from app.models.DTO.user_dto import UserResponseDTO






