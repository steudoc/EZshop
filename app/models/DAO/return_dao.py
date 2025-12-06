"""Return Data Access Object (DAO) module.
This module defines the ReturnDAO class which represents the return data structure
used for database interactions related to return operations."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.user_type import UserType
from app.models.DAO.base_dao import BaseDAO
from app.models.DAO.item_dao import ItemDAO
from app.models.DAO.user_dao import UserDAO






