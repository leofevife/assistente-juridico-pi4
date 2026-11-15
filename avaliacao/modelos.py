from datetime import datetime

from pydantic import BaseModel, Field


class FonteRecuperada(BaseModel):
    artigo: str | None = None
    titulo: str | None = None
    capitulo: str | None = None
    secao: str | None = None
    trecho: str


class ResultadoGeracao(BaseModel):
    id: str
    resposta: str | None = None
    fontes: list[FonteRecuperada] = Field(default_factory=list)
    duracao_segundos: float | None = None
    tentativas: int = 0
    erro: str | None = None


class MetricasCaso(BaseModel):
    id: str
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    recall_artigos: float | None = None
    citacao_artigos: float | None = None
    erros: dict[str, str] = Field(default_factory=dict)


class Execucao(BaseModel):
    rotulo: str
    criada_em: datetime
    versao_ground_truth: str
    total_casos: int
    configuracao: dict[str, str | int | float]
