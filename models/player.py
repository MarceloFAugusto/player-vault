from pydantic import BaseModel


class Player(BaseModel):
    name: str
    tag: str
    email: str
    login: str
    password: str


class CredentialRequest(BaseModel):
    login: str
    email: str