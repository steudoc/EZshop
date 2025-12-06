"""Return service Module.
This module contains the ReturnService class which handles the business logic
for return operations, interacting with the ReturnRepository to perform CRUD operations.
"""

from app.repositories.return_repository import ReturnRepository
from app.models.DTO.return_dto import ReturnCreateDTO, ReturnResponseDTO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError
from typing import Optional, List
from app.models.DAO.return_dao import ReturnDAO
from app.utils import map_dao_to_dto, throw_bad_request_if_found, find_or_throw_not_found
from app.database.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository





