import asyncio
import logging
import math
import re
import warnings
from pathlib import Path
from typing import Protocol

from avaliacao.armazenamento import carregar_lista, salvar_json
from avaliacao.cobertura import artigos_do_cdc_recuperados, citacao_artigos, recall_artigos
from avaliacao.executor import ARQUIVO_RESPOSTAS
from avaliacao.ground_truth import ConjuntoGroundTruth, cita_artigo
from avaliacao.modelos import MetricasCaso, ResultadoGeracao

logger = logging.getLogger(__name__)

ARQUIVO_METRICAS = "metricas.json"
REGEX_ARTIGO_TRECHO = re.compile(r"\bArt\.\s*(\d+[A-Za-z-]*)", re.IGNORECASE)


def _selecionar_contextos_avaliacao(
    resposta: str, contextos: list[str], limite_caracteres: int = 2800
) -> list[str]:
    if not contextos:
        return []

    def prioridade(item: tuple[int, str]) -> tuple[int, int]:
        indice, trecho = item
        correspondencia = REGEX_ARTIGO_TRECHO.search(trecho)
        citado = bool(correspondencia and cita_artigo(resposta, correspondencia.group(1)))
        return (0 if citado else 1, indice)

    ordenados = [trecho for _, trecho in sorted(enumerate(contextos), key=prioridade)]
    selecionados: list[str] = []
    total = 0
    for trecho in ordenados:
        if not selecionados or total + len(trecho) <= limite_caracteres:
            selecionados.append(trecho)
            total += len(trecho)
    return selecionados


class AvaliadorLLM(Protocol):
    async def avaliar(self, pergunta: str, resposta: str, contextos: list[str]) -> dict[str, float | str]: ...


class AvaliadorRagas:
    def __init__(
        self,
        llm_juiz,
        embeddings,
        timeout_segundos: float = 120.0,
        llms_fallback: list | None = None,
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ragas.embeddings import LangchainEmbeddingsWrapper
            from ragas.run_config import RunConfig

        self._configuracao = RunConfig(timeout=timeout_segundos, max_retries=3, max_workers=1)
        self._vetores = LangchainEmbeddingsWrapper(embeddings, run_config=self._configuracao)

        self._faithfulness, self._relevancia = self._criar_par_metricas(llm_juiz)
        nome_principal = str(getattr(llm_juiz, "model_name", "") or "")
        self._juizes = [(nome_principal, "safeguard" in nome_principal, self._faithfulness, self._relevancia)]
        for llm_fb in llms_fallback or []:
            faith_fb, rel_fb = self._criar_par_metricas(llm_fb)
            nome_fb = str(getattr(llm_fb, "model_name", "") or "")
            self._juizes.append((nome_fb, "safeguard" in nome_fb, faith_fb, rel_fb))

    def _criar_par_metricas(self, llm_juiz):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ragas.llms import LangchainLLMWrapper
            from ragas.metrics import Faithfulness, ResponseRelevancy
            from ragas.metrics._answer_relevance import ResponseRelevanceInput, ResponseRelevanceOutput
            from ragas.metrics._faithfulness import (
                NLIStatementInput,
                NLIStatementOutput,
                StatementFaithfulnessAnswer,
                StatementGeneratorInput,
                StatementGeneratorOutput,
            )

        juiz = LangchainLLMWrapper(llm_juiz, run_config=self._configuracao, bypass_n=True)
        faithfulness = Faithfulness(llm=juiz)
        relevancia = ResponseRelevancy(llm=juiz, embeddings=self._vetores, strictness=1)
        faithfulness.init(self._configuracao)
        relevancia.init(self._configuracao)

        faithfulness.statement_generator_prompt.instruction += " Extract at most 2 concise atomic statements."
        faithfulness.statement_generator_prompt.examples = [
            (
                StatementGeneratorInput(
                    question="Qual é o prazo de arrependimento?",
                    answer="O consumidor pode desistir em 7 dias, com reembolso imediato.",
                ),
                StatementGeneratorOutput(
                    statements=[
                        "O consumidor pode desistir em 7 dias.",
                        "Há reembolso imediato.",
                    ]
                ),
            )
        ]
        faithfulness.nli_statements_prompt.instruction += " Keep each reason concise (under 10 words)."
        faithfulness.nli_statements_prompt.examples = [
            (
                NLIStatementInput(
                    context="Art. 49. O consumidor pode desistir no prazo de 7 dias.",
                    statements=["O prazo é de 7 dias."],
                ),
                NLIStatementOutput(
                    statements=[
                        StatementFaithfulnessAnswer(
                            statement="O prazo é de 7 dias.",
                            reason="Art. 49.",
                            verdict=1,
                        )
                    ]
                ),
            )
        ]
        relevancia.question_generation.language = "portuguese"
        relevancia.question_generation.instruction = (
            "Gere uma pergunta em português claro e natural, formulada do ponto de vista de um consumidor, "
            "que seja diretamente respondida pelo texto fornecido. Não inclua números de artigos ou parágrafos na pergunta. "
            "Defina noncommittal como 1 apenas quando a resposta for evasiva ou disser que não há informações suficientes "
            "para responder, e 0 quando o texto trouxer uma resposta jurídica objetiva."
        )
        relevancia.question_generation.examples = [
            (
                ResponseRelevanceInput(
                    response=(
                        "O consumidor pode desistir do contrato no prazo de sete dias a contar da assinatura "
                        "ou do recebimento do produto quando a compra ocorrer fora do estabelecimento comercial, "
                        "com devolução imediata dos valores pagos."
                    )
                ),
                ResponseRelevanceOutput(
                    question="Qual é o prazo para desistir de uma compra feita fora da loja e receber o reembolso?",
                    noncommittal=0,
                ),
            )
        ]
        return faithfulness, relevancia

    async def avaliar(
        self,
        pergunta: str,
        resposta: str,
        contextos: list[str],
        metricas: tuple[str, ...] = ("faithfulness", "answer_relevancy"),
    ) -> dict[str, float | str]:
        from ragas import SingleTurnSample

        contextos_avaliacao = _selecionar_contextos_avaliacao(resposta, contextos)
        amostra = SingleTurnSample(user_input=pergunta, response=resposta, retrieved_contexts=contextos_avaliacao)
        resultados: dict[str, float | str] = {}
        pendentes = list(metricas)

        for nome_modelo, esperar_safeguard, metric_faith, metric_rel in self._juizes:
            if not pendentes:
                break
            metricas_por_nome = {"faithfulness": metric_faith, "answer_relevancy": metric_rel}
            ainda_pendentes: list[str] = []
            for nome in pendentes:
                if esperar_safeguard:
                    await asyncio.sleep(5.0)
                try:
                    valor = float(await metricas_por_nome[nome].single_turn_ascore(amostra))
                    if math.isnan(valor):
                        resultados[nome] = f"valor indefinido (NaN) ({nome_modelo})"
                        ainda_pendentes.append(nome)
                    else:
                        resultados[nome] = valor
                except Exception as erro:
                    resultados[nome] = f"{type(erro).__name__}: {erro}"
                    ainda_pendentes.append(nome)
            pendentes = ainda_pendentes

        return resultados


def _ordenadas(conjunto: ConjuntoGroundTruth, metricas: dict[str, MetricasCaso]) -> list[MetricasCaso]:
    return [metricas[c.id] for c in conjunto.casos if c.id in metricas]


async def avaliar_execucao(
    destino: Path,
    conjunto: ConjuntoGroundTruth,
    artigos_cdc: dict[str, str],
    avaliador: AvaliadorLLM | None,
    *,
    pausa_segundos: float = 0.0,
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
        avaliou_nesta_passagem = False
        if avaliador and pendentes:
            contextos = [fonte.trecho for fonte in resultado.fontes]
            if isinstance(avaliador, AvaliadorRagas):
                retorno = await avaliador.avaliar(caso.pergunta, resultado.resposta, contextos, metricas=tuple(pendentes))
            else:
                retorno = await avaliador.avaliar(caso.pergunta, resultado.resposta, contextos)
            for nome in pendentes:
                valor = retorno.get(nome)
                if isinstance(valor, float):
                    setattr(atual, nome, valor)
                    atual.erros.pop(nome, None)
                else:
                    atual.erros[nome] = str(valor)
            logger.info("%s: %s", caso.id, {n: getattr(atual, n) for n in ("faithfulness", "answer_relevancy")})
            avaliou_nesta_passagem = True

        salvar_json(arquivo, _ordenadas(conjunto, metricas))
        if avaliou_nesta_passagem and pausa_segundos:
            await asyncio.sleep(pausa_segundos)

    return _ordenadas(conjunto, metricas)
