import logging
import math
import warnings
from pathlib import Path
from typing import Protocol

from avaliacao.armazenamento import carregar_lista, salvar_json
from avaliacao.cobertura import artigos_do_cdc_recuperados, citacao_artigos, recall_artigos
from avaliacao.executor import ARQUIVO_RESPOSTAS
from avaliacao.ground_truth import ConjuntoGroundTruth
from avaliacao.modelos import MetricasCaso, ResultadoGeracao

logger = logging.getLogger(__name__)

ARQUIVO_METRICAS = "metricas.json"


class AvaliadorLLM(Protocol):
    async def avaliar(self, pergunta: str, resposta: str, contextos: list[str]) -> dict[str, float | str]: ...


class AvaliadorRagas:
    def __init__(self, llm_juiz, embeddings, timeout_segundos: float = 120.0):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ragas.embeddings import LangchainEmbeddingsWrapper
            from ragas.llms import LangchainLLMWrapper
            from ragas.metrics import Faithfulness, ResponseRelevancy
            from ragas.run_config import RunConfig

        configuracao = RunConfig(timeout=timeout_segundos, max_retries=2, max_workers=1)
        juiz = LangchainLLMWrapper(llm_juiz, run_config=configuracao, bypass_n=True)
        vetores = LangchainEmbeddingsWrapper(embeddings, run_config=configuracao)

        self._faithfulness = Faithfulness(llm=juiz)
        self._relevancia = ResponseRelevancy(llm=juiz, embeddings=vetores, strictness=1)
        self._faithfulness.init(configuracao)
        self._relevancia.init(configuracao)

    async def avaliar(self, pergunta: str, resposta: str, contextos: list[str]) -> dict[str, float | str]:
        from ragas import SingleTurnSample

        amostra = SingleTurnSample(user_input=pergunta, response=resposta, retrieved_contexts=contextos)
        resultados: dict[str, float | str] = {}
        for nome, metrica in (("faithfulness", self._faithfulness), ("answer_relevancy", self._relevancia)):
            try:
                valor = float(await metrica.single_turn_ascore(amostra))
                resultados[nome] = valor if not math.isnan(valor) else "valor indefinido (NaN)"
            except Exception as erro:
                resultados[nome] = f"{type(erro).__name__}: {erro}"
        return resultados


def _ordenadas(conjunto: ConjuntoGroundTruth, metricas: dict[str, MetricasCaso]) -> list[MetricasCaso]:
    return [metricas[c.id] for c in conjunto.casos if c.id in metricas]


async def avaliar_execucao(
    destino: Path,
    conjunto: ConjuntoGroundTruth,
    artigos_cdc: dict[str, str],
    avaliador: AvaliadorLLM | None,
) -> list[MetricasCaso]:
    respostas = {r.id: r for r in carregar_lista(destino / ARQUIVO_RESPOSTAS, ResultadoGeracao)}
    arquivo = destino / ARQUIVO_METRICAS
    metricas = {m.id: m for m in carregar_lista(arquivo, MetricasCaso)}

    for caso in conjunto.casos:
        resultado = respostas.get(caso.id)
        atual = metricas.get(caso.id) or MetricasCaso(id=caso.id)
        metricas[caso.id] = atual

        if resultado is None or resultado.erro is not None or resultado.resposta is None:
            atual.erros = {"geracao": resultado.erro if resultado and resultado.erro else "resposta não gerada"}
            continue

        atual.erros.pop("geracao", None)
        recuperados = artigos_do_cdc_recuperados(resultado.fontes, artigos_cdc)
        atual.recall_artigos = recall_artigos(caso.artigos_referencia, recuperados)
        atual.citacao_artigos = citacao_artigos(caso.artigos_referencia, resultado.resposta)

        pendentes = [n for n in ("faithfulness", "answer_relevancy") if getattr(atual, n) is None]
        if avaliador and pendentes:
            retorno = await avaliador.avaliar(
                caso.pergunta, resultado.resposta, [fonte.trecho for fonte in resultado.fontes]
            )
            for nome in pendentes:
                valor = retorno.get(nome)
                if isinstance(valor, float):
                    setattr(atual, nome, valor)
                    atual.erros.pop(nome, None)
                else:
                    atual.erros[nome] = str(valor)
            logger.info("%s: %s", caso.id, {n: getattr(atual, n) for n in ("faithfulness", "answer_relevancy")})

        salvar_json(arquivo, _ordenadas(conjunto, metricas))

    return _ordenadas(conjunto, metricas)
