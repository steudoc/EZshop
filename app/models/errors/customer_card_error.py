from app.models.errors.app_error import AppError

class CustomerCardError(AppError):
    """Customer Card Error (400)"""
    
    def __init__(self, message: str):
        super().__init__(message, 400)
        self.name = "CustomerCardError"