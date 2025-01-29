import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)