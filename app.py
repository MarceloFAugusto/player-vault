import logging
from bootstrap import init_environment
import sys

# Inicializar ambiente
settings = init_environment()  # Removido o test_mode aqui para permitir leitura do -test

# Resto das importações
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from services.utils import get_static_directory
from routers import auth, players, health
from database.db_manager import DatabaseManager
import uvicorn
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

logger = logging.getLogger(__name__)

# Atualizar nível de log baseado nas configurações
logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL))

logger.info(f"Iniciando aplicação no ambiente: {settings.ENVIRONMENT}")

# Configuração do rate limiter
limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Valorant API",
        description="API para gerenciamento de jogadores do Valorant",
        version="1.0.0",
        docs_url="/docs" if not settings.TESTING else None,  # Desativa docs em teste
        redoc_url="/redoc" if not settings.TESTING else None,  # Desativa redoc em teste
    )

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Incluindo todos os routers
    app.include_router(auth.router)
    app.include_router(players.router)
    app.include_router(health.router)

    try:
        static_dir = get_static_directory()
        logger.info(f"Usando diretório estático: {static_dir}")
        app.mount("/css", StaticFiles(directory=os.path.join(static_dir, "css")), name="css")
        app.mount("/js", StaticFiles(directory=os.path.join(static_dir, "js")), name="js")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    except Exception as e:
        logger.error(f"Erro ao montar diretórios estáticos: {e}")

    @app.get("/")
    async def get_index():
        index_path = os.path.join(get_static_directory(), "index.html")
        return FileResponse(index_path)

    return app

app = create_app()

# Inicializar o banco de dados
DatabaseManager()

def run_api_server():
    try:
        config = uvicorn.Config(
            app,
            host=settings.HOST,
            port=settings.PORT,
            workers=settings.WORKERS,
            loop="auto",
            reload=settings.DEBUG
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_api_server()