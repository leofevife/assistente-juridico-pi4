import copy

import pytest

from avaliacao.ground_truth import (
    MINIMO_CASOS,
    ConjuntoGroundTruth,
    carregar_artigos_cdc,
    carregar_ground_truth,
    normalizar_numero_artigo,
    validar_ground_truth,
)


@pytest.fixture(scope="module")
def conjunto() -> ConjuntoGroundTruth:
    return carregar_ground_truth()


@pytest.fixture(scope="module")
def artigos_cdc() -> dict[str, str]:
    return carregar_artigos_cdc()


def test_conjunto_versionado_passa_na_validacao(conjunto, artigos_cdc):
    assert validar_ground_truth(conjunto, artigos_cdc) == []


def test_possui_ao_menos_o_minimo_de_casos(conjunto):
    assert len(conjunto.casos) >= MINIMO_CASOS


def test_cobre_variedade_de_temas(conjunto):
    assert len({caso.tema for caso in conjunto.casos}) >= 15


def test_artigos_do_cdc_ignoram_decretos_regulamentadores(artigos_cdc):
    assert artigos_cdc["49"].startswith("O consumidor pode desistir do contrato")
    assert artigos_cdc["18"].startswith("Os fornecedores de produtos de consumo")
    assert "42-A" in artigos_cdc
    assert "119" in artigos_cdc
    assert "120" not in artigos_cdc


def test_normaliza_numero_de_artigo():
    assert normalizar_numero_artigo(" 4º-a ") == "4-A"


def test_detecta_conjunto_pequeno(conjunto, artigos_cdc):
    reduzido = conjunto.model_copy(update={"casos": conjunto.casos[:5]})
    problemas = validar_ground_truth(reduzido, artigos_cdc)
    assert any("mínimo" in problema for problema in problemas)


def test_detecta_artigo_inexistente(conjunto, artigos_cdc):
    alterado = copy.deepcopy(conjunto)
    alterado.casos[0].artigos_referencia = ["999"]
    problemas = validar_ground_truth(alterado, artigos_cdc, minimo_casos=1)
    assert any("999" in problema for problema in problemas)


def test_detecta_resposta_que_nao_cita_o_artigo(conjunto, artigos_cdc):
    alterado = copy.deepcopy(conjunto)
    alterado.casos[0].resposta_esperada = "O consumidor pode desistir da compra em sete dias corridos."
    problemas = validar_ground_truth(alterado, artigos_cdc, minimo_casos=1)
    assert any("não cita" in problema for problema in problemas)


def test_detecta_perguntas_e_ids_repetidos(conjunto, artigos_cdc):
    alterado = copy.deepcopy(conjunto)
    alterado.casos[1].id = alterado.casos[0].id
    alterado.casos[1].pergunta = alterado.casos[0].pergunta.upper()
    problemas = validar_ground_truth(alterado, artigos_cdc, minimo_casos=1)
    assert any("identificadores" in problema for problema in problemas)
    assert any("perguntas repetidas" in problema for problema in problemas)
