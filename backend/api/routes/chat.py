import logging

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.documents import Document

from backend.api.dependencies import aplicar_rate_limit, obter_servico
from backend.api.schemas import ErroResposta, FonteLegal, PerguntaRequest, RespostaChat
from backend.services.rag_service import AssistenteJuridicoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def _converter_fonte(documento: Document) -> FonteLegal:
    metadados = documento.metadata or {}
    return FonteLegal(
        lei=metadados.get("lei"),
        titulo=metadados.get("titulo"),
        capitulo=metadados.get("capitulo"),
        secao=metadados.get("secao"),
        artigo=metadados.get("artigo"),
        trecho=documento.page_content,
    )


@router.post(
    "",
    response_model=RespostaChat,
    dependencies=[Depends(aplicar_rate_limit)],
    responses={
        429: {"model": ErroResposta},
        503: {"model": ErroResposta},
    },
)
async def perguntar(
    payload: PerguntaRequest,
    servico: AssistenteJuridicoService = Depends(obter_servico),
) -> RespostaChat:
    try:
        resultado = await servico.responder_com_fontes(payload.pergunta)
    except Exception:
        # Detalhes da falha ficam apenas no log para não expor informações internas ao cliente
        logger.exception("Falha ao processar pergunta no pipeline RAG")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível gerar a resposta no momento. Tente novamente mais tarde.",
        )

    return RespostaChat(
        resposta=resultado.resposta,
        fontes=[_converter_fonte(doc) for doc in resultado.fontes],
    )

