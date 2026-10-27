
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import router as consulta_router


app = FastAPI(
    title="Assistente Jurídico PI4",
    description="API de integração entre o frontend e o assistente RAG do CDC.",
    version="1.0.0"
)
    
# Permite comunicação com o frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

# Registra as rotas de consulta
app.include_router(
    consulta_router,
    prefix="/api/v1"
)


@app.get("/health", tags=["Sistema"])
async def health():
    return {
        "status": "online",
        "aplicacao": "Assistente Jurídico PI4",
        "versao": "1.0.0"
    }
