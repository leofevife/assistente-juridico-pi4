import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path mesmo ao executar diretamente o arquivo
raiz_projeto = Path(__file__).resolve().parent.parent
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import chat, saude
from backend.core.config import Settings, obter_settings
from backend.core.logging_config import configurar_logging
from backend.core.rate_limit import LimitadorRequisicoes

logger = logging.getLogger(__name__)

CABECALHOS_SEGURANCA = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def _inicializar_servicos(app: FastAPI, settings: Settings) -> None:
    # Imports tardios: o carregamento do modelo de embedding é pesado e só deve ocorrer quando a API sobe de fato
    from backend.data.repositorio_vetorial import CDCVectorRepository
    from backend.services.rag_service import AssistenteJuridicoService

    logger.info("Carregando modelo de embedding e conectando ao Qdrant...")
    repositorio = CDCVectorRepository(settings=settings)
    app.state.repositorio = repositorio
    app.state.servico = AssistenteJuridicoService(repository=repositorio, settings=settings)
    logger.info("Pipeline RAG pronto.")


def create_app(settings: Settings | None = None, inicializar_servicos: bool = True) -> FastAPI:
    settings = settings or obter_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Repositório e serviço são criados uma única vez e compartilhados entre as requisições
        if inicializar_servicos and getattr(app.state, "servico", None) is None:
            _inicializar_servicos(app, settings)
        yield

    app = FastAPI(
        title=settings.app_nome,
        version=settings.app_versao,
        lifespan=lifespan,
        docs_url=None if settings.em_producao else "/docs",
        redoc_url=None if settings.em_producao else "/redoc",
        openapi_url=None if settings.em_producao else "/openapi.json",
    )

    app.state.settings = settings
    app.state.servico = None
    app.state.repositorio = None
    app.state.limitador = LimitadorRequisicoes(
        max_requisicoes=settings.rate_limit_requisicoes,
        janela_segundos=settings.rate_limit_janela_segundos,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origens,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def adicionar_cabecalhos_seguranca(request: Request, call_next):
        resposta = await call_next(request)
        for nome, valor in CABECALHOS_SEGURANCA.items():
            resposta.headers.setdefault(nome, valor)
        return resposta

    @app.exception_handler(Exception)
    async def tratar_erro_inesperado(request: Request, exc: Exception):
        logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno no servidor."},
        )

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(saude.router)
    api_v1.include_router(chat.router)
    app.include_router(api_v1)

    return app


configurar_logging()
app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Permite iniciar o servidor executando diretamente este arquivo
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


