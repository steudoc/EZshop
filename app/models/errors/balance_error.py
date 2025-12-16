from app.models.errors.app_error import AppError

class BalanceError(AppError):
    """Balance error (421)"""
    
    def __init__(self, message: str):
        super().__init__(message, 421)
        self.name = "BalanceError"