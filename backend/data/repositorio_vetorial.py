from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.vectorstores import VectorStoreRetriever

from backend.core.config import Settings, obter_settings


class CDCVectorRepository:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or obter_settings()
        self.qdrant_url = self.settings.qdrant_url
        self.qdrant_api_key = self.settings.qdrant_api_key.get_secret_value()
        self.collection_name = self.settings.qdrant_colecao

        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError("Credenciais do Qdrant ausentes no arquivo .env")

        #Inicializa o mesmo modelo usado na ingestão
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.settings.modelo_embedding,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        #Conecta à coleção existente sem recriá-la
        self.vector_store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            collection_name=self.collection_name
        )


    # Retorna o objeto Retriever configurado para buscar os 'k' artigos mais relevantes
    def obter_retriever(self, k: int = 4) -> VectorStoreRetriever:
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    # Método auxiliar caso precise testar a Issue #11 isoladamente retornando a lista de Documents!!
    def buscar_trechos(self, pergunta: str, k: int = 4):
        retriever = self.obter_retriever(k=k)
        return retriever.invoke(pergunta)

    # Usado pelo health check para confirmar que a coleção continua acessível
    def verificar_conexao(self) -> bool:
        return self.vector_store.client.collection_exists(self.collection_name)
