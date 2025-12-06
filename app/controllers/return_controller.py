""" Return Controller Module.
This module contains the ReturnController class which handles the business logic"""

from app.models.DTO.return_dto import ReturnCreateDTO, ReturnResponseDTO
from app.repositories.return_repository import ReturnRepository
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError
from typing import List
from app.models.DAO.return_dao import ReturnDAO
from app.models.user_type import UserType
from app.utils import map_dao_to_dto
from app.database.database import AsyncSessionLocal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository




