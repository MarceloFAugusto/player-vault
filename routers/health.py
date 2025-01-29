from fastapi import APIRouter, Request, Depends
import psutil
import time
from slowapi import Limiter
from slowapi.util import get_remote_address
from database.db_manager import DatabaseManager, get_db
import sys
import platform
from models.responses import HealthCheckResponse, DetailedHealthCheckResponse

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Healthcheck básico e rápido"""
    return {"status": "healthy", "timestamp": time.time()}


@router.get("/health/detailed", response_model=DetailedHealthCheckResponse)
@limiter.limit("10/minute")
async def detailed_health_check(
    request: Request, db: DatabaseManager = Depends(get_db)
):
    """Healthcheck detalhado com informações do sistema"""
    try:
        with db.get_connection() as conn:
            conn.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system": {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "python_version": sys.version,
            "platform": platform.platform(),
            "uptime": time.time() - psutil.boot_time(),
        },
        "dependencies": {"database": db_status},
    }
