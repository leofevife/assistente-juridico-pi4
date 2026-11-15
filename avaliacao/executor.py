import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from avaliacao.armazenamento import carregar_lista, salvar_json
from avaliacao.ground_truth import ConjuntoGroundTruth
from avaliacao.modelos import FonteRecuperada, ResultadoGeracao
from backend.services.rag_service import RespostaRAG

logger = logging.getLogger(__name__)

ARQUIVO_RESPOSTAS = "respostas.json"

Consultar = Callable[[str], Awaitable[RespostaRAG]]


def _converter(resposta: RespostaRAG) -> tuple[str, list[FonteRecuperada]]:
    fontes = [
        FonteRecuperada(
            artigo=(doc.metadata or {}).get("artigo"),
            titulo=(doc.metadata or {}).get("titulo"),
            capitulo=(doc.metadata or {}).get("capitulo"),
            secao=(doc.metadata or {}).get("secao"),
            trecho=doc.page_content,
        )
        for doc in resposta.fontes
    ]
    return resposta.resposta, fontes


async def _consultar_com_tentativas(
    consultar: Consultar, pergunta: str, tentativas: int, espera_segundos: float
) -> ResultadoGeracao:
    ultimo_erro = ""
    for tentativa in range(1, tentativas + 1):
        inicio = time.perf_counter()
        try:
            texto, fontes = _converter(await consultar(pergunta))
            return ResultadoGeracao(
                id="",
                resposta=texto,
                fontes=fontes,
                duracao_segundos=round(time.perf_counter() - inicio, 2),
                tentativas=tentativa,
            )
        except Exception as erro:
            ultimo_erro = f"{type(erro).__name__}: {erro}"
            logger.warning("Tentativa %s/%s falhou: %s", tentativa, tentativas, ultimo_erro)
            if tentativa < tentativas:
                await asyncio.sleep(espera_segundos * tentativa)
    return ResultadoGeracao(id="", tentativas=tentativas, erro=ultimo_erro)


async def gerar_respostas(
    consultar: Consultar,
    conjunto: ConjuntoGroundTruth,
    destino: Path,
    *,
    pausa_segundos: float = 0.0,
    tentativas: int = 3,
    espera_segundos: float = 20.0,
) -> list[ResultadoGeracao]:
    arquivo = destino / ARQUIVO_RESPOSTAS
    existentes = {r.id: r for r in carregar_lista(arquivo, ResultadoGeracao)}

    for caso in conjunto.casos:
        anterior = existentes.get(caso.id)
        if anterior and anterior.erro is None:
            continue

        resultado = await _consultar_com_tentativas(consultar, caso.pergunta, tentativas, espera_segundos)
        resultado.id = caso.id
        existentes[caso.id] = resultado
        salvar_json(arquivo, [existentes[c.id] for c in conjunto.casos if c.id in existentes])
        logger.info("%s: %s", caso.id, "ok" if resultado.erro is None else f"falhou ({resultado.erro})")

        if pausa_segundos:
            await asyncio.sleep(pausa_segundos)

    return [existentes[c.id] for c in conjunto.casos if c.id in existentes]
