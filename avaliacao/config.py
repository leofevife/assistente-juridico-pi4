from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from avaliacao.ground_truth import RAIZ_PROJETO

CAMINHO_ENV = RAIZ_PROJETO / "backend" / ".env"


class ConfiguracaoAvaliacao(BaseSettings):
    model_config = SettingsConfigDict(env_file=CAMINHO_ENV, env_file_encoding="utf-8", extra="ignore")

    modelo_juiz: str = Field(default="openai/gpt-oss-20b", alias="AVALIACAO_MODELO_JUIZ")
    pausa_segundos: float = Field(default=0.0, ge=0.0, alias="AVALIACAO_PAUSA_SEGUNDOS")
    tentativas: int = Field(default=3, ge=1, alias="AVALIACAO_TENTATIVAS")
    timeout_juiz_segundos: float = Field(default=120.0, gt=0, alias="AVALIACAO_TIMEOUT_JUIZ_SEGUNDOS")


DIRETORIO_RESULTADOS: Path = RAIZ_PROJETO / "avaliacao" / "resultados"
