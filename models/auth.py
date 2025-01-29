from pydantic import BaseModel
from typing import Optional


class AdminLogin(BaseModel):
    username: str
    password: str
    code: Optional[str] = None


class Setup2FARequest(BaseModel):
    user_id: int


class Verify2FACode(BaseModel):
    secret: str
    code: str


class Reset2FARequest(BaseModel):
    user_id: Optional[int] = 1  # Default para o admin
