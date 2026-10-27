
import logging

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.services.rag_service import AssistenteJuridicoService
from backend.data.repositorio_vetorial import CDCVectorRepository


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/consultas",
    tags=["Consultas Jurídicas"]
)


class PerguntaRequest(BaseModel):
    pergunta: str = Field(
        min_length=5,
        max_length=2000
    )


class PerguntaResponse(BaseModel):
    resposta: str
    fontes: list = Field(default_factory=list)


@lru_cache(maxsize=1)
def obter_servico_rag() -> AssistenteJuridicoService:
    repository = CDCVectorRepository()
    return AssistenteJuridicoService(repository)


@router.post(
    "",
    response_model=PerguntaResponse
)
def consultar(
    dados: PerguntaRequest,
    service: AssistenteJuridicoService = Depends(obter_servico_rag)
):
    pergunta = dados.pergunta.strip()

    if len(pergunta) < 5:
        raise HTTPException(
            status_code=422,
            detail="Pergunta muito curta."
        )

    try:
        resposta = service.responder_duvida(pergunta)

        return PerguntaResponse(
            resposta=resposta,
            fontes=[]
        )

    except Exception:
        logger.exception("Falha na consulta RAG")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar o assistente jurídico."
        )
