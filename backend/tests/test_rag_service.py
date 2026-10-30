import asyncio

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from backend.services.rag_service import MENSAGEM_SEM_CONTEXTO, AssistenteJuridicoService, RespostaRAG
from backend.tests.fakes import RepositorioFalso, documento_artigo

PERGUNTA = "Comprei uma geladeira pela internet e me arrependi. Qual o prazo para devolver?"


def _llm_que_captura(registro: list):
    def _responder(valor_prompt):
        registro.append(valor_prompt.to_messages())
        return AIMessage(content="Conforme o Art. 49, o prazo é de 7 dias.")
    return RunnableLambda(_responder)


def test_respeita_k_configurado(settings):
    repositorio = RepositorioFalso()
    settings.retriever_k = 6
    AssistenteJuridicoService(repositorio, settings=settings, llm=FakeListChatModel(responses=["x"]))
    assert repositorio.k_solicitado == 6


def test_responde_com_fontes_recuperadas(settings):
    documentos = [documento_artigo("49", "O consumidor pode desistir do contrato, no prazo de 7 dias...")]
    servico = AssistenteJuridicoService(
        RepositorioFalso(documentos), settings=settings, llm=FakeListChatModel(responses=["Resposta do Art. 49"])
    )

    resultado = asyncio.run(servico.responder_com_fontes(PERGUNTA))

    assert isinstance(resultado, RespostaRAG)
    assert resultado.resposta == "Resposta do Art. 49"
    assert [doc.metadata["artigo"] for doc in resultado.fontes] == ["49"]


def test_contexto_e_pergunta_chegam_ao_prompt(settings):
    registro: list = []
    documentos = [
        documento_artigo("49", "O consumidor pode desistir do contrato."),
        documento_artigo("26", "O direito de reclamar caduca em trinta dias."),
    ]
    servico = AssistenteJuridicoService(RepositorioFalso(documentos), settings=settings, llm=_llm_que_captura(registro))

    asyncio.run(servico.responder_com_fontes(PERGUNTA))

    mensagens = registro[0]
    assert "Art. 49" in mensagens[0].content
    assert "Art. 26" in mensagens[0].content
    assert PERGUNTA in mensagens[1].content


def test_sem_documentos_nao_chama_llm(settings):
    registro: list = []
    servico = AssistenteJuridicoService(RepositorioFalso([]), settings=settings, llm=_llm_que_captura(registro))

    resultado = asyncio.run(servico.responder_com_fontes(PERGUNTA))

    assert resultado.resposta == MENSAGEM_SEM_CONTEXTO
    assert resultado.fontes == []
    assert registro == []


def test_responder_duvida_sincrono_mantem_compatibilidade(settings):
    servico = AssistenteJuridicoService(
        RepositorioFalso([documento_artigo("49", "Prazo de reflexão.")]),
        settings=settings,
        llm=FakeListChatModel(responses=["ok"]),
    )
    assert servico.responder_duvida(PERGUNTA) == "ok"


def test_formatar_documentos_separa_artigos():
    texto = AssistenteJuridicoService._formatar_documentos([
        documento_artigo("1", "A"),
        documento_artigo("2", "B"),
    ])
    assert texto.count("---") == 1
    assert "Art. 1 A" in texto and "Art. 2 B" in texto

