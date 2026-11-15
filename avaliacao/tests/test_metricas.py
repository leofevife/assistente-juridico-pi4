import asyncio

import pytest

from avaliacao.armazenamento import carregar_lista, salvar_json
from avaliacao.executor import ARQUIVO_RESPOSTAS
from avaliacao.ground_truth import carregar_artigos_cdc, carregar_ground_truth
from avaliacao.metricas import ARQUIVO_METRICAS, _selecionar_contextos_avaliacao, avaliar_execucao
from avaliacao.modelos import FonteRecuperada, MetricasCaso, ResultadoGeracao


class AvaliadorFalso:
    def __init__(self, retornos):
        self.retornos = retornos
        self.chamadas: list[str] = []

    async def avaliar(self, pergunta, resposta, contextos):
        self.chamadas.append(pergunta)
        return self.retornos(pergunta)


@pytest.fixture(scope="module")
def artigos_cdc():
    return carregar_artigos_cdc()


@pytest.fixture
def conjunto():
    completo = carregar_ground_truth()
    return completo.model_copy(update={"casos": completo.casos[:2]})


@pytest.fixture
def destino(tmp_path, conjunto, artigos_cdc):
    resultados = []
    for caso in conjunto.casos:
        referencia = caso.artigos_referencia[0]
        resultados.append(
            ResultadoGeracao(
                id=caso.id,
                resposta=f"Segundo o Art. {referencia}, é assim.",
                fontes=[FonteRecuperada(artigo=referencia, trecho=f"Art. {referencia} {artigos_cdc[referencia]}")],
                tentativas=1,
            )
        )
    salvar_json(tmp_path / ARQUIVO_RESPOSTAS, resultados)
    return tmp_path


def _avaliar(destino, conjunto, artigos_cdc, avaliador):
    return asyncio.run(avaliar_execucao(destino, conjunto, artigos_cdc, avaliador))


def test_combina_metricas_ragas_e_cobertura(destino, conjunto, artigos_cdc):
    avaliador = AvaliadorFalso(lambda pergunta: {"faithfulness": 0.9, "answer_relevancy": 0.8})

    metricas = _avaliar(destino, conjunto, artigos_cdc, avaliador)

    assert [m.faithfulness for m in metricas] == [0.9, 0.9]
    assert [m.answer_relevancy for m in metricas] == [0.8, 0.8]
    assert all(m.recall_artigos == 1.0 and m.citacao_artigos == 1.0 for m in metricas)
    assert all(m.erros == {} for m in metricas)


def test_registra_erro_da_metrica_sem_ocultar_o_caso(destino, conjunto, artigos_cdc):
    def retorno(pergunta):
        if pergunta == conjunto.casos[0].pergunta:
            return {"faithfulness": "TimeoutError: juiz demorou", "answer_relevancy": 0.7}
        return {"faithfulness": 0.9, "answer_relevancy": 0.7}

    metricas = _avaliar(destino, conjunto, artigos_cdc, AvaliadorFalso(retorno))

    assert metricas[0].faithfulness is None
    assert "TimeoutError" in metricas[0].erros["faithfulness"]
    assert metricas[0].answer_relevancy == 0.7
    assert metricas[1].erros == {}


def test_reavalia_apenas_metricas_pendentes(destino, conjunto, artigos_cdc):
    primeira = AvaliadorFalso(lambda pergunta: {"faithfulness": "erro", "answer_relevancy": 0.7})
    _avaliar(destino, conjunto, artigos_cdc, primeira)

    segunda = AvaliadorFalso(lambda pergunta: {"faithfulness": 0.95, "answer_relevancy": 0.1})
    metricas = _avaliar(destino, conjunto, artigos_cdc, segunda)

    assert [m.faithfulness for m in metricas] == [0.95, 0.95]
    assert [m.answer_relevancy for m in metricas] == [0.7, 0.7]
    assert all(m.erros == {} for m in metricas)


def test_caso_sem_resposta_gerada_fica_com_erro_de_geracao(destino, conjunto, artigos_cdc):
    respostas = carregar_lista(destino / ARQUIVO_RESPOSTAS, ResultadoGeracao)
    respostas[0] = ResultadoGeracao(id=respostas[0].id, erro="RuntimeError: falha", tentativas=3)
    salvar_json(destino / ARQUIVO_RESPOSTAS, respostas)
    avaliador = AvaliadorFalso(lambda pergunta: {"faithfulness": 0.9, "answer_relevancy": 0.8})

    metricas = _avaliar(destino, conjunto, artigos_cdc, avaliador)

    assert "falha" in metricas[0].erros["geracao"]
    assert metricas[0].faithfulness is None
    assert len(avaliador.chamadas) == 1


def test_calcula_cobertura_sem_avaliador(destino, conjunto, artigos_cdc):
    metricas = _avaliar(destino, conjunto, artigos_cdc, None)

    assert all(m.recall_artigos == 1.0 for m in metricas)
    assert all(m.faithfulness is None for m in metricas)
    salvos = carregar_lista(destino / ARQUIVO_METRICAS, MetricasCaso)
    assert len(salvos) == 2


def test_selecionar_contextos_avaliacao_prioriza_artigos_citados_e_limita_tamanho():
    contextos = [
        "[Título I]\nArt. 10 " + "a" * 1600,
        "[Título I]\nArt. 49 " + "b" * 1600,
        "[Título I]\nArt. 18 " + "c" * 600,
    ]
    selecionados = _selecionar_contextos_avaliacao("Conforme o Art. 49 e o Art. 18 do CDC.", contextos, limite_caracteres=2800)

    assert len(selecionados) == 2
    assert "Art. 49" in selecionados[0]
    assert "Art. 18" in selecionados[1]
