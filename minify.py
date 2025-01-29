import os
import logging
from rjsmin import jsmin
from rcssmin import cssmin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def minify_file(input_path, output_path):
    """Minifica um arquivo JS ou CSS usando rjsmin/rcssmin"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        if input_path.endswith(".js"):
            minified = jsmin(content)
        elif input_path.endswith(".css"):
            minified = cssmin(content)
        else:
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(minified)

        logger.info(f"Arquivo minificado: {output_path}")

    except Exception as e:
        logger.error(f"Erro ao minificar {input_path}: {str(e)}")


def main():
    input_dir = "static"
    output_dir = "static_min"

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith((".js", ".css")):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                minify_file(input_path, output_path)


if __name__ == "__main__":
    main()
