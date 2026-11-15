from datetime import datetime, timezone

from avaliacao.ground_truth import carregar_ground_truth
from avaliacao.modelos import Execucao, MetricasCaso, ResultadoGeracao
from avaliacao.relatorio import montar_relatorio, resumir


def _execucao(total: int) -> Execucao:
    return Execucao(
        rotulo="teste",
        criada_em=datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
        versao_ground_truth="1.0.0",
        total_casos=total,
        configuracao={"modelo_geracao": "modelo-x", "documentos_recuperados_k": 4},
    )


def _conjunto():
    completo = carregar_ground_truth()
    return completo.model_copy(update={"casos": completo.casos[:3]})


def test_resumir_calcula_estatisticas_da_distribuicao():
    resumo = resumir([0.2, 0.4, 0.6, 0.8, 1.0])
    assert resumo["media"] == 0.6
    assert resumo["mediana"] == 0.6
    assert resumo["minimo"] == 0.2 and resumo["maximo"] == 1.0
    assert resumir([]) is None


def test_relatorio_compara_medias_com_os_limites():
    conjunto = _conjunto()
    ids = [c.id for c in conjunto.casos]
    metricas = [
        MetricasCaso(id=ids[0], faithfulness=0.95, answer_relevancy=0.9, recall_artigos=1.0, citacao_artigos=1.0),
        MetricasCaso(id=ids[1], faithfulness=0.9, answer_relevancy=0.7, recall_artigos=1.0, citacao_artigos=1.0),
        MetricasCaso(id=ids[2], faithfulness=0.9, answer_relevancy=0.7, recall_artigos=1.0, citacao_artigos=1.0),
    ]

    texto = montar_relatorio(_execucao(3), conjunto, [], metricas)

    assert "| Faithfulness | 0,917 | > 0,850 | 3/3 | Atingido |" in texto
    assert "| Answer Relevance | 0,767 | > 0,800 | 3/3 | Não atingido |" in texto
    assert "`modelo-x`" in texto


def test_relatorio_lista_falhas_e_casos_abaixo_do_esperado():
    conjunto = _conjunto()
    ids = [c.id for c in conjunto.casos]
    metricas = [
        MetricasCaso(id=ids[0], faithfulness=0.4, answer_relevancy=0.9, recall_artigos=0.0, citacao_artigos=0.0),
        MetricasCaso(id=ids[1], erros={"faithfulness": "TimeoutError: juiz demorou"}, answer_relevancy=0.9),
    ]
    respostas = [ResultadoGeracao(id=ids[0], resposta="Texto qualquer.", duracao_segundos=2.5)]

    texto = montar_relatorio(_execucao(3), conjunto, respostas, metricas)

    assert "## Falhas registradas" in texto
    assert "TimeoutError: juiz demorou" in texto
    assert "artigo de referência não foi recuperado" in texto
    assert f"| {ids[0]} |" in texto


def test_relatorio_indica_quando_nao_ha_casos_abaixo_do_limite():
    conjunto = _conjunto()
    metricas = [
        MetricasCaso(id=c.id, faithfulness=0.95, answer_relevancy=0.9, recall_artigos=1.0, citacao_artigos=1.0)
        for c in conjunto.casos
    ]
    texto = montar_relatorio(_execucao(3), conjunto, [], metricas)
    assert "Nenhum caso ficou abaixo dos limites." in texto
    assert "## Falhas registradas" not in texto
