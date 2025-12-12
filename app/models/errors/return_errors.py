"""Return errors Module.
This module defines custom error classes related to return operations,
facilitating error handling and reporting in the application."""

from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.app_error import AppError
from app.models.errors.unauthorized_error import UnauthorizedError
from app.models.errors.notfound_error import NotFoundError

class PaymentFailedError(AppError):
    """Errore quando il rimborso non va a buon fine (carta non valida, credito insufficiente)."""
    def __init__(self, message: str = "Payment failed"):
        super().__init__(code=422, message=message, name="PaymentFailedError")





