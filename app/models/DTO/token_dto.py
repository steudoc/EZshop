from pydantic import BaseModel

class TokenDTO(BaseModel):
    token: str
