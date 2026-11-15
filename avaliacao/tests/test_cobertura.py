import pytest

from avaliacao.cobertura import artigos_do_cdc_recuperados, citacao_artigos, recall_artigos
from avaliacao.ground_truth import carregar_artigos_cdc
from avaliacao.modelos import FonteRecuperada


@pytest.fixture(scope="module")
def artigos_cdc():
    return carregar_artigos_cdc()


def _fonte(artigo: str, corpo: str) -> FonteRecuperada:
    return FonteRecuperada(artigo=artigo, trecho=f"[Título I | Capítulo VI]\nArt. {artigo} {corpo}")


def test_reconhece_artigo_do_cdc_pelo_texto(artigos_cdc):
    fonte = _fonte("49", artigos_cdc["49"])
    assert artigos_do_cdc_recuperados([fonte], artigos_cdc) == {"49"}


def test_ignora_artigo_de_decreto_com_mesma_numeracao(artigos_cdc):
    fonte = _fonte("18", "A inobservância das normas contidas na Lei nº 8.078, de 1990, constituirá prática infrativa")
    assert artigos_do_cdc_recuperados([fonte], artigos_cdc) == set()


def test_reconhece_artigo_com_ordinal_e_sufixo(artigos_cdc):
    fontes = [_fonte("1", f"° {artigos_cdc['1']}"), _fonte("42-A", artigos_cdc["42-A"])]
    assert artigos_do_cdc_recuperados(fontes, artigos_cdc) == {"1", "42-A"}


def test_recall_considera_fracao_dos_artigos_de_referencia():
    assert recall_artigos(["30", "35"], {"30"}) == 0.5
    assert recall_artigos(["49"], {"49", "18"}) == 1.0
    assert recall_artigos(["49"], set()) == 0.0


def test_citacao_considera_fracao_dos_artigos_citados_na_resposta():
    resposta = "Conforme o Art. 30, a oferta obriga o fornecedor."
    assert citacao_artigos(["30", "35"], resposta) == 0.5
    assert citacao_artigos(["6"], "Previsto no art. 6º, VIII.") == 1.0
