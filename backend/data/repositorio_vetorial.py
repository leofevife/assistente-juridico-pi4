import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.vectorstores import VectorStoreRetriever

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

class CDCVectorRepository:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "cdc_vetores"
        
        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError("Credenciais do Qdrant ausentes no arquivo .env")

        #Inicializa o mesmo modelo usado na ingestão
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
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