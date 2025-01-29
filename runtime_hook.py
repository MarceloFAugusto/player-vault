import os
import tempfile
import json
import glob
import shutil


def is_process_running(pid):
    try:
        os.kill(pid, 0)
        print(f"Processo {pid} está em execução")
        return True
    except OSError:
        print(f"Processo {pid} não está em execução")
        return False


def cleanup_temp():
    print(f"Iniciando limpeza de arquivos temporários do processo {os.getpid()}")
    # Limpa arquivo de lock
    lock_file = os.path.join(tempfile.gettempdir(), "valorant-ranks.lock")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                data = json.load(f)
                if not is_process_running(data.get("pid")):
                    os.remove(lock_file)
        except BaseException:
            os.remove(lock_file)

    # Limpa diretórios temporários antigos
    temp_pattern = os.path.join(tempfile.gettempdir(), "valorant-ranks-*")
    for temp_dir in glob.glob(temp_pattern):
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except BaseException:
            pass


# Limpar arquivo de lock ao iniciar
cleanup_temp()
