from pydantic import BaseModel
from typing import List, Optional


class TokenResponse(BaseModel):
    token: str
    expiry_time: int

class PlayerRank(BaseModel):
    message: str
    url: str

class PlayerRankResponse(BaseModel):
    id: int
    name: str
    tag: str
    rank: PlayerRank
    email: str
    login: str
    password: str


class BasicPlayerResponse(BaseModel):
    id: int
    name: str
    tag: str
    status: Optional[str] = None


class CredentialResponse(BaseModel):
    status: str
    password: str


class PlayerExistsResponse(BaseModel):
    email_exists: bool
    login_exists: bool


class DeletePlayerResponse(BaseModel):
    status: str
    message: str


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: float


class SystemInfo(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    python_version: str
    platform: str
    uptime: float


class Dependencies(BaseModel):
    database: str


class DetailedHealthCheckResponse(BaseModel):
    status: str
    timestamp: float
    system: SystemInfo
    dependencies: Dependencies


class Setup2FAResponse(BaseModel):
    is_configured: bool
    secret: Optional[str] = None
    qr_code_url: Optional[str] = None


class Verify2FAResponse(BaseModel):
    success: bool


class ErrorResponse(BaseModel):
    detail: str
