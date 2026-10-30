from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from backend.core.config import Settings


def criar_settings(**sobrescritas) -> Settings:
    valores = {
        "QDRANT_URL": "http://qdrant.teste",
        "QDRANT_API_KEY": "chave-qdrant-teste",
        "GROQ_API_KEY": "chave-groq-teste",
        "AMBIENTE": "teste",
    }
    valores.update(sobrescritas)
    return Settings(_env_file=None, **valores)


class RetrieverFalso(BaseRetriever):
    documentos: list[Document] = []
    consultas: list[str] = []

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        self.consultas.append(query)
        return list(self.documentos)


class RepositorioFalso:
    def __init__(self, documentos: list[Document] | None = None, conectado: bool = True):
        self.retriever = RetrieverFalso(documentos=documentos or [], consultas=[])
        self.conectado = conectado
        self.k_solicitado = None

    def obter_retriever(self, k: int = 4) -> RetrieverFalso:
        self.k_solicitado = k
        return self.retriever

    def verificar_conexao(self) -> bool:
        if isinstance(self.conectado, Exception):
            raise self.conectado
        return self.conectado


def documento_artigo(numero: str, texto: str) -> Document:
    return Document(
        page_content=f"[Título I | Capítulo VI]\nArt. {numero} {texto}",
        metadata={
            "lei": "Lei 8.078/1990 (CDC)",
            "titulo": "Título I",
            "capitulo": "Capítulo VI",
            "secao": "Geral",
            "artigo": numero,
            "tipo": "Artigo",
        },
    )
