import statistics
from datetime import datetime

from avaliacao.ground_truth import ConjuntoGroundTruth
from avaliacao.modelos import Execucao, MetricasCaso, ResultadoGeracao

LIMITE_FAITHFULNESS = 0.85
LIMITE_ANSWER_RELEVANCY = 0.80
MENSAGEM_SEM_CONTEXTO = "não há informações suficientes"


def _formatar(valor: float | None) -> str:
    return "—" if valor is None else f"{valor:.3f}".replace(".", ",")


def resumir(valores: list[float]) -> dict[str, float] | None:
    if not valores:
        return None
    quartis = statistics.quantiles(valores, n=4, method="inclusive") if len(valores) > 1 else [valores[0]] * 3
    return {
        "media": statistics.fmean(valores),
        "minimo": min(valores),
        "q1": quartis[0],
        "mediana": quartis[1],
        "q3": quartis[2],
        "maximo": max(valores),
    }


def _valores(metricas: list[MetricasCaso], campo: str) -> list[float]:
    return [v for v in (getattr(m, campo) for m in metricas) if v is not None]


def _causa_provavel(metrica: MetricasCaso, resultado: ResultadoGeracao | None) -> str:
    if resultado is None or resultado.resposta is None:
        return "resposta não gerada"
    if MENSAGEM_SEM_CONTEXTO in resultado.resposta.lower():
        return "o modelo respondeu que não havia contexto suficiente"
    if metrica.recall_artigos is not None and metrica.recall_artigos < 1:
        return "artigo de referência não foi recuperado"
    if metrica.faithfulness is not None and metrica.faithfulness < LIMITE_FAITHFULNESS:
        return "resposta traz afirmações que o contexto recuperado não sustenta"
    return "resposta pouco aderente à pergunta"


def _tabela_indicadores(metricas: list[MetricasCaso]) -> list[str]:
    linhas = ["| Indicador | Média | Limite | Casos válidos | Situação |", "|---|---|---|---|---|"]
    for rotulo, campo, limite in (
        ("Faithfulness", "faithfulness", LIMITE_FAITHFULNESS),
        ("Answer Relevance", "answer_relevancy", LIMITE_ANSWER_RELEVANCY),
    ):
        valores = _valores(metricas, campo)
        resumo = resumir(valores)
        if resumo is None:
            linhas.append(f"| {rotulo} | — | > {_formatar(limite)} | 0/{len(metricas)} | Não avaliado |")
            continue
        situacao = "Atingido" if resumo["media"] > limite else "Não atingido"
        linhas.append(
            f"| {rotulo} | {_formatar(resumo['media'])} | > {_formatar(limite)} "
            f"| {len(valores)}/{len(metricas)} | {situacao} |"
        )
    return linhas


def _tabela_distribuicao(metricas: list[MetricasCaso]) -> list[str]:
    linhas = ["| Métrica | Mínimo | 1º quartil | Mediana | 3º quartil | Máximo |", "|---|---|---|---|---|---|"]
    for rotulo, campo in (
        ("Faithfulness", "faithfulness"),
        ("Answer Relevance", "answer_relevancy"),
        ("Recall dos artigos de referência", "recall_artigos"),
        ("Citação dos artigos de referência", "citacao_artigos"),
    ):
        resumo = resumir(_valores(metricas, campo))
        if resumo is None:
            linhas.append(f"| {rotulo} | — | — | — | — | — |")
        else:
            celulas = " | ".join(_formatar(resumo[k]) for k in ("minimo", "q1", "mediana", "q3", "maximo"))
            linhas.append(f"| {rotulo} | {celulas} |")
    return linhas


def montar_relatorio(
    execucao: Execucao,
    conjunto: ConjuntoGroundTruth,
    respostas: list[ResultadoGeracao],
    metricas: list[MetricasCaso],
) -> str:
    por_resposta = {r.id: r for r in respostas}
    por_metrica = {m.id: m for m in metricas}
    casos = {c.id: c for c in conjunto.casos}

    linhas = [
        f"# Relatório de avaliação: {execucao.rotulo}",
        "",
        f"- **Data da execução:** {execucao.criada_em.astimezone().strftime('%d/%m/%Y %H:%M')}",
        f"- **Ground Truth:** versão {execucao.versao_ground_truth} ({execucao.total_casos} casos)",
        f"- **Relatório gerado em:** {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M')}",
        "",
        "## Configuração",
        "",
        "| Parâmetro | Valor |",
        "|---|---|",
    ]
    linhas += [f"| {chave} | `{valor}` |" for chave, valor in execucao.configuracao.items()]

    linhas += ["", "## Indicadores do projeto", "", *_tabela_indicadores(metricas)]
    linhas += ["", "## Distribuição dos resultados", "", *_tabela_distribuicao(metricas)]

    falhas = [m for m in metricas if m.erros]
    if falhas:
        linhas += ["", "## Falhas registradas", "", "| Caso | Etapa | Erro |", "|---|---|---|"]
        for metrica in falhas:
            for etapa, erro in metrica.erros.items():
                linhas.append(f"| {metrica.id} | {etapa} | {erro.replace('|', '/')[:160]} |")

    abaixo = [
        m for m in metricas
        if (m.faithfulness is not None and m.faithfulness < LIMITE_FAITHFULNESS)
        or (m.answer_relevancy is not None and m.answer_relevancy < LIMITE_ANSWER_RELEVANCY)
        or (m.recall_artigos is not None and m.recall_artigos < 1)
    ]
    linhas += ["", "## Casos abaixo do esperado", ""]
    if abaixo:
        linhas += ["| Caso | Pergunta | Faith. | Relev. | Recall | Causa provável |", "|---|---|---|---|---|---|"]
        for metrica in abaixo:
            pergunta = casos[metrica.id].pergunta if metrica.id in casos else ""
            linhas.append(
                f"| {metrica.id} | {pergunta} | {_formatar(metrica.faithfulness)} | {_formatar(metrica.answer_relevancy)} "
                f"| {_formatar(metrica.recall_artigos)} | {_causa_provavel(metrica, por_resposta.get(metrica.id))} |"
            )
    else:
        linhas.append("Nenhum caso ficou abaixo dos limites.")

    linhas += ["", "## Resultados por caso", "", "| Caso | Tema | Faith. | Relev. | Recall | Citação | Duração (s) |", "|---|---|---|---|---|---|---|"]
    for caso in conjunto.casos:
        metrica = por_metrica.get(caso.id)
        resposta = por_resposta.get(caso.id)
        if metrica is None:
            continue
        duracao = _formatar(resposta.duracao_segundos) if resposta and resposta.duracao_segundos is not None else "—"
        linhas.append(
            f"| {caso.id} | {caso.tema} | {_formatar(metrica.faithfulness)} | {_formatar(metrica.answer_relevancy)} "
            f"| {_formatar(metrica.recall_artigos)} | {_formatar(metrica.citacao_artigos)} | {duracao} |"
        )

    return "\n".join(linhas) + "\n"
