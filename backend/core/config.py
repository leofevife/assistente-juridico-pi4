import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

CAMINHO_ENV = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=CAMINHO_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_nome: str = "Assistente Jurídico CDC"
    app_versao: str = "0.2.0"
    ambiente: str = Field(default="desenvolvimento", alias="AMBIENTE")

    qdrant_url: str = Field(alias="QDRANT_URL")
    qdrant_api_key: SecretStr = Field(alias="QDRANT_API_KEY")
    qdrant_colecao: str = Field(default="cdc_vetores", alias="QDRANT_COLECAO")

    groq_api_key: SecretStr = Field(alias="GROQ_API_KEY")
    groq_modelo: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODELO")
    llm_temperatura: float = Field(default=0.0, ge=0.0, le=2.0, alias="LLM_TEMPERATURA")
    llm_timeout_segundos: float = Field(default=60.0, gt=0, alias="LLM_TIMEOUT_SEGUNDOS")
    llm_max_tentativas: int = Field(default=2, ge=0, alias="LLM_MAX_TENTATIVAS")

    modelo_embedding: str = Field(default="BAAI/bge-m3", alias="MODELO_EMBEDDING")
    retriever_k: int = Field(default=4, ge=1, le=20, alias="RETRIEVER_K")

    pergunta_tamanho_maximo: int = Field(default=1000, ge=10, alias="PERGUNTA_TAMANHO_MAXIMO")

    cors_origens: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGENS",
    )

    rate_limit_requisicoes: int = Field(default=20, ge=1, alias="RATE_LIMIT_REQUISICOES")
    rate_limit_janela_segundos: int = Field(default=60, ge=1, alias="RATE_LIMIT_JANELA_SEGUNDOS")

    # Aceita CORS_ORIGENS no .env como lista separada por vírgula, além do formato JSON
    @field_validator("cors_origens", mode="before")
    @classmethod
    def _separar_origens(cls, valor):
        if isinstance(valor, str):
            if valor.strip().startswith("["):
                return json.loads(valor)
            return [origem.strip() for origem in valor.split(",") if origem.strip()]
        return valor

    @property
    def em_producao(self) -> bool:
        return self.ambiente.lower() in {"producao", "production"}


@lru_cache
def obter_settings() -> Settings:
    return Settings()
