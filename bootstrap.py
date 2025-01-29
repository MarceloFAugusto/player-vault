import os
import argparse
import logging
import sys
from config.settings import get_settings

logger = logging.getLogger(__name__)

def init_environment(test_mode=None):
    """Inicializa o ambiente da aplicação"""
    # Configurar logging primeiro
    logging.basicConfig(level=logging.INFO)
    
    if test_mode is not None:
        # Se test_mode foi explicitamente passado, use-o
        os.environ["ENVIRONMENT"] = "test" if test_mode else "production"
    elif 'pytest' in sys.modules:
        # Se estiver rodando via pytest, force modo teste
        os.environ["ENVIRONMENT"] = "test"
    else:
        # Parse argumentos CLI para execução normal
        try:
            parser = argparse.ArgumentParser(description='Iniciar servidor Valorant API')
            parser.add_argument('-test', action='store_true', help='Iniciar em modo de teste')
            args = parser.parse_args()
            
            if args.test:
                os.environ["ENVIRONMENT"] = "test"
        except SystemExit:
            # Ignora erros de argumentos durante testes
            pass
    
    # Forçar recarregamento das configurações
    settings = get_settings()
    logger.info(f"Ambiente configurado: {os.getenv('ENVIRONMENT', 'production')}")
    
    return settings