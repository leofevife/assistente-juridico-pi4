import hashlib
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from langchain_groq import ChatGroq

from avaliacao.armazenamento import carregar_objeto, salvar_json
from avaliacao.config import ConfiguracaoAvaliacao
from avaliacao.ground_truth import ConjuntoGroundTruth
from avaliacao.metricas import AvaliadorRagas
from avaliacao.modelos import Execucao
from backend.core.config import Settings
from backend.data.repositorio_vetorial import CDCVectorRepository
from backend.services.rag_service import AssistenteJuridicoService

ARQUIVO_EXECUCAO = "execucao.json"


def criar_servico(settings: Settings) -> tuple[AssistenteJuridicoService, CDCVectorRepository]:
    repositorio = CDCVectorRepository(settings=settings)
    return AssistenteJuridicoService(repositorio, settings=settings), repositorio


def _criar_llm_juiz(settings: Settings, config: ConfiguracaoAvaliacao, modelo: str) -> ChatGroq:
    extras: dict[str, object] = {}
    max_tokens = 650
    max_retries = 2
    if "safeguard" in modelo:
        extras["reasoning_effort"] = "low"
        max_tokens = 1500
        max_retries = 6
    elif "gpt-oss" in modelo:
        extras["reasoning_effort"] = "low"
        max_tokens = 1500
        max_retries = 2
    elif "qwen" in modelo:
        extras["reasoning_effort"] = "none"
        max_tokens = 600
        max_retries = 2
    return ChatGroq(
        model=modelo,
        temperature=0.0,
        api_key=settings.groq_api_key,
        timeout=config.timeout_juiz_segundos,
        max_retries=max_retries,
        max_tokens=max_tokens,
        **extras,
    )


def criar_avaliador(
    settings: Settings, config: ConfiguracaoAvaliacao, repositorio: CDCVectorRepository
) -> AvaliadorRagas:
    juiz = _criar_llm_juiz(settings, config, config.modelo_juiz)
    modelos_reserva = [
        modelo
        for modelo in (
            "openai/gpt-oss-safeguard-20b",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
        )
        if modelo != config.modelo_juiz
    ]
    fallbacks = [_criar_llm_juiz(settings, config, modelo) for modelo in modelos_reserva]
    return AvaliadorRagas(
        juiz,
        repositorio.embeddings,
        config.timeout_juiz_segundos,
        llms_fallback=fallbacks,
    )


def _hash_prompt(servico: AssistenteJuridicoService) -> str:
    modelo = servico.prompt.messages[0].prompt.template
    return hashlib.sha256(modelo.encode("utf-8")).hexdigest()[:12]


def descrever_configuracao(
    settings: Settings, config: ConfiguracaoAvaliacao, servico: AssistenteJuridicoService
) -> dict[str, str | int | float]:
    return {
        "modelo_geracao": settings.groq_modelo,
        "modelo_juiz": config.modelo_juiz,
        "modelo_embedding": settings.modelo_embedding,
        "colecao_qdrant": settings.qdrant_colecao,
        "documentos_recuperados_k": settings.retriever_k,
        "temperatura_geracao": settings.llm_temperatura,
        "prompt_sha256": _hash_prompt(servico),
        "ragas": version("ragas"),
        "langchain_core": version("langchain-core"),
        "python": sys.version.split()[0],
    }


def registrar_execucao(
    destino: Path, rotulo: str, conjunto: ConjuntoGroundTruth, configuracao: dict[str, str | int | float]
) -> Execucao:
    arquivo = destino / ARQUIVO_EXECUCAO
    if arquivo.exists():
        return carregar_objeto(arquivo, Execucao)

    execucao = Execucao(
        rotulo=rotulo,
        criada_em=datetime.now(timezone.utc),
        versao_ground_truth=conjunto.versao,
        total_casos=len(conjunto.casos),
        configuracao=configuracao,
    )
    salvar_json(arquivo, execucao)
    return execucao
