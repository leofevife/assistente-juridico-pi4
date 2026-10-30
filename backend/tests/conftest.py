import os

import pytest

# Valores fictícios garantem que os testes rodem sem o .env real e sem acesso à rede
os.environ.update({
    "QDRANT_URL": "http://qdrant.teste",
    "QDRANT_API_KEY": "chave-qdrant-teste",
    "GROQ_API_KEY": "chave-groq-teste",
    "PERGUNTA_TAMANHO_MAXIMO": "1000",
    "AMBIENTE": "teste",
})

from backend.core.config import Settings, obter_settings  # noqa: E402
from backend.tests.fakes import criar_settings  # noqa: E402

obter_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return criar_settings()
