""" Return route module.
This module defines the return endpoints for the API, specifically handling
return operations. It provides a RESTful interface for users to process returns."""

from fastapi import APIRouter, Depends, status
from typing import List
from app.models.DTO.return_dto import ReturnCreateDTO, ReturnResponseDTO
from app.models.user_type import UserType
from app.controllers.return_controller import ReturnController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError

router = APIRouter(prefix=ROUTES['V1_RETURNS'], tags=["Returns"])
controller = ReturnController()




