import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

caminho_env = Path(__file__).resolve().parent.parent / ".env"
if not caminho_env.exists():
    caminho_env = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=caminho_env)

cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

modelos = cliente.models.list()
print("Modelos disponíveis na sua conta:")
for m in modelos.data:
    print(f"- {m.id}")