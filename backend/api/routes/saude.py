import asyncio
import logging

from fastapi import APIRouter, Request, Response, status

from backend.api.schemas import StatusProntidao, StatusSaude

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Saúde"])


@router.get("/health", response_model=StatusSaude)
async def health(request: Request) -> StatusSaude:
    return StatusSaude(status="ok", versao=request.app.version)


# Prontidão separada da liveness para orquestradores (ex: Kubernetes) não reiniciarem a API por falha externa
@router.get("/ready", response_model=StatusProntidao)
async def ready(request: Request, response: Response) -> StatusProntidao:
    repositorio = getattr(request.app.state, "repositorio", None)
    servico = getattr(request.app.state, "servico", None)

    banco_ok = False
    if repositorio is not None:
        try:
            banco_ok = await asyncio.to_thread(repositorio.verificar_conexao)
        except Exception:
            logger.warning("Banco vetorial inacessível no teste de prontidão", exc_info=True)

    pronto = servico is not None and banco_ok
    if not pronto:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return StatusProntidao(status="pronto" if pronto else "indisponivel", banco_vetorial=banco_ok)

