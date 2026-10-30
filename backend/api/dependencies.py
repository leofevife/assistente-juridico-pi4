from fastapi import HTTPException, Request, status

from backend.core.rate_limit import LimitadorRequisicoes
from backend.services.rag_service import AssistenteJuridicoService


def obter_servico(request: Request) -> AssistenteJuridicoService:
    servico = getattr(request.app.state, "servico", None)
    if servico is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de respostas indisponível no momento.",
        )
    return servico


def _identificar_cliente(request: Request) -> str:
    # Atrás de proxy reverso, configure o uvicorn com --proxy-headers para que o IP real chegue aqui
    return request.client.host if request.client else "desconhecido"


async def aplicar_rate_limit(request: Request) -> None:
    limitador: LimitadorRequisicoes = request.app.state.limitador
    permitido, tentar_em = await limitador.permitir(_identificar_cliente(request))
    if not permitido:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite de requisições excedido. Tente novamente em instantes.",
            headers={"Retry-After": str(tentar_em)},
        )

