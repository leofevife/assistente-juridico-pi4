import logging
import sys

# Bibliotecas HTTP registram cada requisição (incluindo URLs de serviços externos) em INFO
BIBLIOTECAS_RUIDOSAS = ("httpx", "httpcore", "urllib3", "huggingface_hub", "sentence_transformers")


def configurar_logging(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    for nome in BIBLIOTECAS_RUIDOSAS:
        logging.getLogger(nome).setLevel(logging.WARNING)
