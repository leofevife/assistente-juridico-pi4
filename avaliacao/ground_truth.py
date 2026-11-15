import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_GROUND_TRUTH = Path(__file__).resolve().parent / "dados" / "ground_truth.json"
CAMINHO_CDC = RAIZ_PROJETO / "scripts" / "resources" / "cdc_limpo.txt"

MINIMO_CASOS = 30

REGEX_ARTIGO = re.compile(r"^Art\.\s*(\d+)\s*[º°o]?(?:\s*-\s*([A-Z]))?\.?\s*(.*)$")
REGEX_INICIO_DECRETOS = re.compile(r"^DECRETO\s+N", re.IGNORECASE)


class CasoGroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tema: str
    pergunta: str = Field(min_length=10)
    resposta_esperada: str = Field(min_length=30)
    artigos_referencia: list[str] = Field(min_length=1)


class ConjuntoGroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    versao: str
    lei: str
    casos: list[CasoGroundTruth]


def normalizar_numero_artigo(numero: str) -> str:
    return re.sub(r"[º°\s]", "", numero).upper()


def carregar_ground_truth(caminho: Path = CAMINHO_GROUND_TRUTH) -> ConjuntoGroundTruth:
    return ConjuntoGroundTruth.model_validate(json.loads(caminho.read_text(encoding="utf-8")))


def carregar_artigos_cdc(caminho: Path = CAMINHO_CDC) -> dict[str, str]:
    # O arquivo traz o CDC seguido de decretos regulamentadores, que repetem a numeração dos artigos
    artigos: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if REGEX_INICIO_DECRETOS.match(linha):
            break
        correspondencia = REGEX_ARTIGO.match(linha)
        if not correspondencia:
            continue
        numero, sufixo, corpo = correspondencia.groups()
        chave = f"{numero}-{sufixo}" if sufixo else numero
        artigos.setdefault(chave, corpo)
    return artigos


def cita_artigo(texto: str, numero: str) -> bool:
    padrao = rf"\bart(?:s)?\.?\s*{re.escape(numero)}(?!\d)"
    return re.search(padrao, texto, re.IGNORECASE) is not None


def validar_ground_truth(
    conjunto: ConjuntoGroundTruth,
    artigos_cdc: dict[str, str],
    minimo_casos: int = MINIMO_CASOS,
) -> list[str]:
    problemas: list[str] = []

    if len(conjunto.casos) < minimo_casos:
        problemas.append(f"O conjunto possui {len(conjunto.casos)} casos; o mínimo é {minimo_casos}.")

    ids = [caso.id for caso in conjunto.casos]
    perguntas = [" ".join(caso.pergunta.lower().split()) for caso in conjunto.casos]
    if len(set(ids)) != len(ids):
        problemas.append("Existem identificadores de caso repetidos.")
    if len(set(perguntas)) != len(perguntas):
        problemas.append("Existem perguntas repetidas.")

    for caso in conjunto.casos:
        for referencia in caso.artigos_referencia:
            numero = normalizar_numero_artigo(referencia)
            if numero not in artigos_cdc:
                problemas.append(f"{caso.id}: o artigo {referencia} não existe no texto do CDC.")
            elif not cita_artigo(caso.resposta_esperada, numero):
                problemas.append(f"{caso.id}: a resposta esperada não cita o artigo {referencia}.")

    return problemas
