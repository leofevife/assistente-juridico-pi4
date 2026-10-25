import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

caminho_env = Path(__file__).resolve().parent.parent / ".env"
if not caminho_env.exists():
    caminho_env = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=caminho_env)

chave = os.getenv("GROQ_API_KEY")

if not chave:
    print(f"Erro: Variável GROQ_API_KEY não foi encontrada em: {caminho_env}")
    exit(1)

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=chave
)

resposta = llm.invoke("Teste de ligação. Devolve apenas a palavra OK.")
print(resposta.content)