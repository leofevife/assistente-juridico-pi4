from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.config import obter_settings


class PerguntaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pergunta: str = Field(
        min_length=3,
        description="Dúvida do usuário sobre o Código de Defesa do Consumidor.",
        examples=["Comprei um produto pela internet e me arrependi. Qual o prazo para devolver?"],
    )

    # O limite vem da configuração para permitir ajuste sem alterar o código
    @field_validator("pergunta")
    @classmethod
    def _validar_pergunta(cls, valor: str) -> str:
        valor = " ".join(valor.split())
        if len(valor) < 3:
            raise ValueError("A pergunta deve conter ao menos 3 caracteres.")
        limite = obter_settings().pergunta_tamanho_maximo
        if len(valor) > limite:
            raise ValueError(f"A pergunta deve conter no máximo {limite} caracteres.")
        return valor


class FonteLegal(BaseModel):
    lei: str | None = None
    titulo: str | None = None
    capitulo: str | None = None
    secao: str | None = None
    artigo: str | None = None
    trecho: str


class RespostaChat(BaseModel):
    resposta: str
    fontes: list[FonteLegal]


class StatusSaude(BaseModel):
    status: str
    versao: str


class StatusProntidao(BaseModel):
    status: str
    banco_vetorial: bool


class ErroResposta(BaseModel):
    detail: str
