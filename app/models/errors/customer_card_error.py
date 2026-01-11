from app.models.errors.app_error import AppError

class CustomerCardError(AppError):
    """Customer Card Error (500)"""
    
    def __init__(self, message: str):
        super().__init__(message, 500)
        self.name = "CustomerCardError"