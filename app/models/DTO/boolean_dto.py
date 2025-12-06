from pydantic import BaseModel

class BooleanDTO(BaseModel):
    success: bool = True
