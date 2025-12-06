"""Return Repository Module.
This module contains the ReturnRepository class which handles database"""

from app.repositories.return_repository import ReturnRepository
from app.models.DTO.return_dto import ReturnCreateDTO, ReturnResponseDTO
from app.models.DAO.return_dao import ReturnDAO
from app.utils import throw_bad_request_if_found, find_or_throw_not_found
from app.models.errors.notfound_error import NotFoundError
from typing import Optional, List






