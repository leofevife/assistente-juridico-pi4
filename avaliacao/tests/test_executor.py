import asyncio

import pytest
from langchain_core.documents import Document

from avaliacao.armazenamento import carregar_lista
from avaliacao.executor import ARQUIVO_RESPOSTAS, gerar_respostas
from avaliacao.ground_truth import carregar_ground_truth
from avaliacao.modelos import ResultadoGeracao
from backend.services.rag_service import RespostaRAG


@pytest.fixture
def conjunto():
    completo = carregar_ground_truth()
    return completo.model_copy(update={"casos": completo.casos[:3]})


def _resposta(texto: str = "Conforme o Art. 49, são 7 dias.") -> RespostaRAG:
    documento = Document(
        page_content="[Título I | Capítulo VI]\nArt. 49 O consumidor pode desistir.",
        metadata={"artigo": "49", "titulo": "Título I", "capitulo": "Capítulo VI", "secao": "Geral"},
    )
    return RespostaRAG(resposta=texto, fontes=[documento])


def _executar(consultar, conjunto, destino, **kwargs):
    return asyncio.run(
        gerar_respostas(consultar, conjunto, destino, espera_segundos=0, **kwargs)
    )


def test_gera_e_persiste_respostas_com_contextos(conjunto, tmp_path):
    async def consultar(pergunta):
        return _resposta()

    resultados = _executar(consultar, conjunto, tmp_path)

    assert [r.id for r in resultados] == [c.id for c in conjunto.casos]
    assert all(r.erro is None and r.resposta for r in resultados)
    assert resultados[0].fontes[0].artigo == "49"
    assert "Art. 49" in resultados[0].fontes[0].trecho
    salvos = carregar_lista(tmp_path / ARQUIVO_RESPOSTAS, ResultadoGeracao)
    assert len(salvos) == 3


def test_repete_a_consulta_quando_ocorre_falha_temporaria(conjunto, tmp_path):
    chamadas = {"total": 0}

    async def consultar(pergunta):
        chamadas["total"] += 1
        if chamadas["total"] == 1:
            raise RuntimeError("limite de taxa")
        return _resposta()

    resultados = _executar(consultar, conjunto, tmp_path, tentativas=3)

    assert resultados[0].erro is None
    assert resultados[0].tentativas == 2


def test_registra_falha_persistente_sem_interromper_a_execucao(conjunto, tmp_path):
    async def consultar(pergunta):
        if pergunta == conjunto.casos[1].pergunta:
            raise RuntimeError("modelo indisponível")
        return _resposta()

    resultados = _executar(consultar, conjunto, tmp_path, tentativas=2)

    assert [r.erro is None for r in resultados] == [True, False, True]
    assert "modelo indisponível" in resultados[1].erro
    assert resultados[1].resposta is None


def test_retoma_sem_repetir_casos_concluidos(conjunto, tmp_path):
    async def falha_no_segundo(pergunta):
        if pergunta == conjunto.casos[1].pergunta:
            raise RuntimeError("falha")
        return _resposta()

    _executar(falha_no_segundo, conjunto, tmp_path, tentativas=1)

    perguntas: list[str] = []

    async def consultar(pergunta):
        perguntas.append(pergunta)
        return _resposta()

    resultados = _executar(consultar, conjunto, tmp_path)

    assert perguntas == [conjunto.casos[1].pergunta]
    assert all(r.erro is None for r in resultados)
