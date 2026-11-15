import asyncio

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from backend.data.repositorio_vetorial import RetrieverCDC, eh_documento_cdc
from backend.services.rag_service import MENSAGEM_SEM_CONTEXTO, AssistenteJuridicoService, RespostaRAG
from backend.tests.fakes import RepositorioFalso, RetrieverFalso, documento_artigo

PERGUNTA = "Comprei uma geladeira pela internet e me arrependi. Qual o prazo para devolver?"


def _llm_que_captura(registro: list):
    def _responder(valor_prompt):
        registro.append(valor_prompt.to_messages())
        return AIMessage(content="Conforme o Art. 49, o prazo é de 7 dias.")
    return RunnableLambda(_responder)


def test_respeita_k_configurado(settings):
    repositorio = RepositorioFalso()
    settings.retriever_k = 4
    AssistenteJuridicoService(repositorio, settings=settings, llm=FakeListChatModel(responses=["x"]))
    assert repositorio.k_solicitado == 4


def test_obter_retriever_solicita_pool_completo_de_artigos():
    from unittest.mock import MagicMock
    from backend.data.repositorio_vetorial import CDCVectorRepository

    repo = object.__new__(CDCVectorRepository)
    repo.vector_store = MagicMock()
    repo.vector_store.as_retriever.return_value = RetrieverFalso()
    retriever = repo.obter_retriever(k=4)

    repo.vector_store.as_retriever.assert_called_once_with(
        search_type="similarity",
        search_kwargs={"k": 120},
    )
    assert isinstance(retriever, RetrieverCDC)
    assert retriever.k == 4


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


def test_eh_documento_cdc_filtra_decretos_e_portarias():
    cdc_comum = documento_artigo("6", "São direitos básicos do consumidor...")
    cdc_titulo_vi = Document(
        page_content="[Título Vi - Disposições Finais | Geral]\nArt. 117 Acrescente-se...",
        metadata={"titulo": "Título Vi - Disposições Finais", "artigo": "117"},
    )
    decreto_titulo_vi = Document(
        page_content="[Título Vi - Disposições Finais | Capítulo Iii]\nArt. 22 Será aplicada multa...",
        metadata={"titulo": "Título Vi - Disposições Finais", "artigo": "22"},
    )
    texto_decreto = Document(
        page_content="[Título I | Geral]\nArt. 5 Os termos deste decreto aplicam-se...",
        metadata={"titulo": "Título I", "artigo": "5"},
    )
    texto_portaria = Document(
        page_content="[Título I | Geral]\nArt. 3 Esta portaria entra em vigor...",
        metadata={"titulo": "Título I", "artigo": "3"},
    )

    assert eh_documento_cdc(cdc_comum) is True
    assert eh_documento_cdc(cdc_titulo_vi) is True
    assert eh_documento_cdc(decreto_titulo_vi) is False
    assert eh_documento_cdc(texto_decreto) is False
    assert eh_documento_cdc(texto_portaria) is False


def test_retriever_cdc_remove_decretos_e_limita_em_k():
    decreto = Document(
        page_content="[Título Vi - Disposições Finais]\nArt. 14 ...",
        metadata={"titulo": "Título Vi - Disposições Finais", "artigo": "14"},
    )
    artigos = [documento_artigo(str(n), f"Texto {n}") for n in (6, 18, 26, 39)]
    base = RetrieverFalso(documentos=[decreto, *artigos], consultas=[])
    retriever = RetrieverCDC(retriever=base, k=2)

    sincrono = retriever.invoke("inversão do ônus")
    assincrono = asyncio.run(retriever.ainvoke("inversão do ônus"))

    assert [d.metadata["artigo"] for d in sincrono] == ["6", "18"]
    assert [d.metadata["artigo"] for d in assincrono] == ["6", "18"]


def test_retriever_cdc_deduplica_e_prioriza_correspondencia_lexical():
    artigos = [
        documento_artigo("18", "Responsabilidade solidária por vícios."),
        documento_artigo("26", "Prazo decadencial para reclamar."),
        documento_artigo("18", "Duplicata do artigo 18."),
        documento_artigo("12", "Responsabilidade do fabricante."),
        documento_artigo("14", "Responsabilidade do prestador de serviços."),
        documento_artigo("6", "Facilitação da defesa com inversão do ônus da prova."),
    ]
    retriever = RetrieverCDC(retriever=RetrieverFalso(documentos=artigos, consultas=[]), k=4)

    resultado = retriever.invoke("Como funciona a inversão do ônus da prova?")

    ids = [d.metadata["artigo"] for d in resultado]
    assert len(ids) == 4
    assert ids[:2] == ["18", "26"]
    assert "6" in ids
    assert ids.count("18") == 1


def test_retriever_cdc_pondera_termos_raros_por_idf():
    artigos = [
        documento_artigo("1", "Regra geral de proteção."),
        documento_artigo("2", "Regra complementar de proteção."),
        documento_artigo("3", "Regra sobre prova documental comum."),
        documento_artigo("4", "Regra sobre prova pericial comum."),
        documento_artigo("5", "Regra sobre prova testemunhal comum."),
        documento_artigo("6", "Facilitação da defesa com inversão do ônus da prova."),
    ]
    retriever = RetrieverCDC(retriever=RetrieverFalso(documentos=artigos, consultas=[]), k=4)

    resultado = retriever.invoke("Como funciona a inversão do ônus da prova?")

    ids = [d.metadata["artigo"] for d in resultado]
    assert "6" in ids

