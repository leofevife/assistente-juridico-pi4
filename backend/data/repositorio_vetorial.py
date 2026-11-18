import math
import re
import unicodedata

from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings
from langchain_qdrant import QdrantVectorStore

from backend.core.config import Settings, obter_settings

REGEX_NUMERO_ARTIGO = re.compile(r"^(\d+)")
REGEX_TERMOS = re.compile(r"[a-z0-9]+")
STOPWORDS_CONSULTA = frozenset({
    "para", "pelo", "pela", "pelos", "pelas", "como", "qual", "quais", "quando",
    "onde", "porque", "sobre", "mais", "menos", "muito", "isso", "isto", "esse",
    "essa", "este", "esta", "pode", "posso", "tenho", "deve", "devo", "fazer",
    "uma", "uns", "umas", "entre", "apos", "antes", "sempre", "nunca", "tudo",
    "nada", "outro", "outra", "outros", "outras", "mesmo", "mesma", "sendo",
    "seria", "tinha", "foram", "estao", "consumidor", "produto", "produtos",
    "servico", "servicos", "codigo", "defesa", "loja", "empresa",
})


def _extrair_termos(texto: str) -> list[str]:
    normalizado = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    ).lower()
    return [termo for termo in REGEX_TERMOS.findall(normalizado) if len(termo) >= 4]


def _peso_correspondencia(termo: str, palavras_doc: set[str]) -> float:
    if termo in palavras_doc:
        return 2.0
    if len(termo) >= 6 and any(palavra.startswith(termo[:5]) for palavra in palavras_doc):
        return 1.0
    return 0.0


def _calcular_idf(palavras_docs: list[set[str]], termos: set[str]) -> dict[str, float]:
    total = len(palavras_docs)
    return {
        termo: math.log((total + 1) / (sum(1 for palavras in palavras_docs if _peso_correspondencia(termo, palavras) > 0) + 1)) + 1.0
        for termo in termos
    }


def _pontuacao_lexical(palavras_doc: set[str], pesos_idf: dict[str, float]) -> float:
    if not pesos_idf or not palavras_doc:
        return 0.0
    return sum(_peso_correspondencia(termo, palavras_doc) * idf for termo, idf in pesos_idf.items())


def _chave_deduplicacao(doc: Document) -> tuple[str, str]:
    artigo = str((doc.metadata or {}).get("artigo") or "").strip()
    if artigo:
        return ("artigo", artigo)
    return ("conteudo", doc.page_content)


def eh_documento_cdc(doc: Document) -> bool:
    conteudo = doc.page_content.lower()
    if "deste decreto" in conteudo or "esta portaria" in conteudo:
        return False
    metadata = doc.metadata or {}
    titulo = str(metadata.get("titulo") or "").strip().lower()
    artigo = str(metadata.get("artigo") or "").strip()
    if titulo.startswith("título vi") or titulo.startswith("titulo vi"):
        correspondencia = REGEX_NUMERO_ARTIGO.match(artigo)
        return bool(correspondencia and int(correspondencia.group(1)) >= 107)
    return True


class RetrieverCDC(BaseRetriever):
    retriever: BaseRetriever
    k: int = 4

    def _selecionar_documentos(self, query: str, documentos: list[Document]) -> list[Document]:
        filtrados: list[Document] = []
        vistos: set[tuple[str, str]] = set()
        for doc in documentos:
            if not eh_documento_cdc(doc):
                continue
            chave = _chave_deduplicacao(doc)
            if chave in vistos:
                continue
            vistos.add(chave)
            filtrados.append(doc)

        preservados = max(self.k - 2, 1)
        selecionados = filtrados[:preservados]
        if len(selecionados) >= self.k or len(filtrados) <= preservados:
            return selecionados[: self.k]

        termos_brutos = set(_extrair_termos(query))
        termos = termos_brutos - STOPWORDS_CONSULTA or termos_brutos
        palavras_docs = [set(_extrair_termos(doc.page_content)) for doc in filtrados]
        pesos_idf = _calcular_idf(palavras_docs, termos)
        ordenados = sorted(
            range(preservados, len(filtrados)),
            key=lambda indice: (-_pontuacao_lexical(palavras_docs[indice], pesos_idf), indice),
        )
        vagas = self.k - len(selecionados)
        return selecionados + [filtrados[indice] for indice in ordenados[:vagas]]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> list[Document]:
        documentos = self.retriever.invoke(query)
        return self._selecionar_documentos(query, documentos)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun | None = None
    ) -> list[Document]:
        documentos = await self.retriever.ainvoke(query)
        return self._selecionar_documentos(query, documentos)


class CDCVectorRepository:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or obter_settings()
        self.qdrant_url = self.settings.qdrant_url
        self.qdrant_api_key = self.settings.qdrant_api_key.get_secret_value()
        self.collection_name = self.settings.qdrant_colecao

        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError("Credenciais do Qdrant ausentes no arquivo .env")

        self.embeddings = self._criar_embeddings()

        self.vector_store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            collection_name=self.collection_name,
            validate_collection_config=not self.settings.usar_embedding_remoto,
        )

    def _criar_embeddings(self) -> Embeddings:
        if self.settings.usar_embedding_remoto:
            token = self.settings.hf_api_token.get_secret_value().strip() if self.settings.hf_api_token else ""
            if not token:
                raise ValueError("HF_API_TOKEN ausente no arquivo .env para uso do endpoint de embeddings da Hugging Face")
            return HuggingFaceEndpointEmbeddings(
                model=self.settings.modelo_embedding,
                provider="hf-inference",
                huggingfacehub_api_token=token,
            )

        return HuggingFaceEmbeddings(
            model_name=self.settings.modelo_embedding,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def obter_retriever(self, k: int = 4) -> BaseRetriever:
        base = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": max(k * 20, 120)},
        )
        return RetrieverCDC(retriever=base, k=k)

    def buscar_trechos(self, pergunta: str, k: int = 4):
        retriever = self.obter_retriever(k=k)
        return retriever.invoke(pergunta)

    def verificar_conexao(self) -> bool:
        return self.vector_store.client.collection_exists(self.collection_name)
