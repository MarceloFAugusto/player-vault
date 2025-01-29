import os
import sys
import logging

logger = logging.getLogger(__name__)


def get_resource_path(relative_path):
    """Obtém o caminho absoluto para um recurso, seja em desenvolvimento ou no executável"""
    try:
        # PyInstaller cria um diretório temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_static_directory():
    """Determina qual diretório de arquivos estáticos usar"""
    base_dir = get_resource_path("static")
    if os.getenv("ENVIRONMENT") == "production":
        base_dir = get_resource_path("static_min")

    # Cria os diretórios se não existirem
    os.makedirs(os.path.join(base_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "js"), exist_ok=True)

    return base_dir
