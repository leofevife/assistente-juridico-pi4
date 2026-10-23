import sys
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parent.parent.parent
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from backend.data.repositorio_vetorial import CDCVectorRepository
from backend.services.rag_service import AssistenteJuridicoService

if __name__ == "__main__":
    print("Inicializando conexão com Qdrant e carregando BGE-M3...")
    repo = CDCVectorRepository()
    
    #Teste Recuperação
    pergunta_teste = "Comprei uma geladeira pela internet e me arrependi. Qual o prazo para devolver?"
    print(f"\n--- TESTE Busca Vetorial ---")
    trechos = repo.buscar_trechos(pergunta_teste, k=2)
    for i, doc in enumerate(trechos):
        print(f"Resultado {i+1}: Artigo {doc.metadata.get('artigo')} ({doc.metadata.get('capitulo')})")

    # Teste Geração com RAG
    print(f"\n--- TESTE Resposta do LLM ---")
    service = AssistenteJuridicoService(repository=repo)
    resposta = service.responder_duvida(pergunta_teste)
    print(resposta)