import argparse
import asyncio
import logging
import sys
from functools import lru_cache
from pathlib import Path

from avaliacao.armazenamento import carregar_lista, carregar_objeto
from avaliacao.config import DIRETORIO_RESULTADOS, ConfiguracaoAvaliacao
from avaliacao.ground_truth import carregar_artigos_cdc, carregar_ground_truth, validar_ground_truth
from avaliacao.modelos import Execucao, MetricasCaso, ResultadoGeracao

ARQUIVO_RELATORIO = "relatorio.md"


def _validar() -> int:
    conjunto = carregar_ground_truth()
    problemas = validar_ground_truth(conjunto, carregar_artigos_cdc())
    if problemas:
        print(f"Ground Truth inválido ({len(problemas)} problema(s)):")
        for problema in problemas:
            print(f" - {problema}")
        return 1
    temas = len({caso.tema for caso in conjunto.casos})
    print(f"Ground Truth v{conjunto.versao} válido: {len(conjunto.casos)} casos em {temas} temas.")
    return 0


def _destino(rotulo: str) -> Path:
    return DIRETORIO_RESULTADOS / rotulo


@lru_cache(maxsize=1)
def _ambiente():
    from avaliacao.execucao import criar_servico
    from backend.core.config import obter_settings

    settings = obter_settings()
    servico, repositorio = criar_servico(settings)
    return settings, ConfiguracaoAvaliacao(), carregar_ground_truth(), servico, repositorio


async def _gerar(rotulo: str) -> None:
    from avaliacao.execucao import descrever_configuracao, registrar_execucao
    from avaliacao.executor import gerar_respostas

    settings, config, conjunto, servico, _ = _ambiente()
    destino = _destino(rotulo)
    registrar_execucao(destino, rotulo, conjunto, descrever_configuracao(settings, config, servico))

    resultados = await gerar_respostas(
        servico.responder_com_fontes,
        conjunto,
        destino,
        pausa_segundos=config.pausa_segundos,
        tentativas=config.tentativas,
    )
    falhas = [r.id for r in resultados if r.erro]
    print(f"Respostas geradas: {len(resultados) - len(falhas)}/{len(conjunto.casos)}. Falhas: {falhas or 'nenhuma'}.")


async def _avaliar(rotulo: str) -> None:
    from avaliacao.execucao import criar_avaliador
    from avaliacao.metricas import avaliar_execucao

    settings, config, conjunto, _, repositorio = _ambiente()
    avaliador = criar_avaliador(settings, config, repositorio)

    metricas = await avaliar_execucao(
        _destino(rotulo),
        conjunto,
        carregar_artigos_cdc(),
        avaliador,
        pausa_segundos=config.pausa_segundos,
    )
    pendentes = [m.id for m in metricas if m.erros]
    print(f"Casos avaliados: {len(metricas) - len(pendentes)}/{len(conjunto.casos)}. Com erro: {pendentes or 'nenhum'}.")


def _relatorio(rotulo: str) -> None:
    from avaliacao.executor import ARQUIVO_RESPOSTAS
    from avaliacao.execucao import ARQUIVO_EXECUCAO
    from avaliacao.metricas import ARQUIVO_METRICAS
    from avaliacao.relatorio import montar_relatorio

    destino = _destino(rotulo)
    texto = montar_relatorio(
        carregar_objeto(destino / ARQUIVO_EXECUCAO, Execucao),
        carregar_ground_truth(),
        carregar_lista(destino / ARQUIVO_RESPOSTAS, ResultadoGeracao),
        carregar_lista(destino / ARQUIVO_METRICAS, MetricasCaso),
    )
    (destino / ARQUIVO_RELATORIO).write_text(texto, encoding="utf-8")
    print(f"Relatório salvo em {destino / ARQUIVO_RELATORIO}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m avaliacao", description="Avaliação do assistente jurídico.")
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    subcomandos.add_parser("validar", help="Valida o conjunto Ground Truth contra o texto do CDC.")
    for nome, ajuda in (
        ("gerar", "Executa o pipeline RAG para cada caso e salva respostas e contextos."),
        ("avaliar", "Calcula Faithfulness e Answer Relevance com o RAGAS."),
        ("relatorio", "Gera o relatório em Markdown a partir dos resultados salvos."),
        ("executar", "Executa gerar, avaliar e relatorio em sequência."),
    ):
        comando = subcomandos.add_parser(nome, help=ajuda)
        comando.add_argument("--rotulo", required=True, help="Nome da execução; define a pasta em avaliacao/resultados.")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    for ruidosa in ("httpx", "httpcore", "huggingface_hub", "sentence_transformers", "ragas"):
        logging.getLogger(ruidosa).setLevel(logging.WARNING)

    if args.comando == "validar":
        return _validar()
    if args.comando in ("gerar", "executar"):
        asyncio.run(_gerar(args.rotulo))
    if args.comando in ("avaliar", "executar"):
        asyncio.run(_avaliar(args.rotulo))
    if args.comando in ("relatorio", "executar"):
        _relatorio(args.rotulo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
