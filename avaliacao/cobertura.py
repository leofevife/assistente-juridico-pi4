import re
import unicodedata

from avaliacao.ground_truth import cita_artigo, normalizar_numero_artigo
from avaliacao.modelos import FonteRecuperada

TAMANHO_ASSINATURA = 40

REGEX_PREFIXO_TRECHO = re.compile(r"^\s*(?:\[[^\]]*\]\s*)?Art\.\s*[\dA-Za-z-]+\s*")


def _assinatura(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9]", "", sem_acentos)[:TAMANHO_ASSINATURA]


def artigos_do_cdc_recuperados(fontes: list[FonteRecuperada], artigos_cdc: dict[str, str]) -> set[str]:
    # O artigo só conta se o texto também for o do CDC, pois os decretos anexados à base repetem a numeração
    assinaturas = {numero: _assinatura(corpo) for numero, corpo in artigos_cdc.items()}
    encontrados: set[str] = set()
    for fonte in fontes:
        if not fonte.artigo:
            continue
        numero = normalizar_numero_artigo(fonte.artigo)
        corpo = REGEX_PREFIXO_TRECHO.sub("", fonte.trecho)
        if numero in assinaturas and _assinatura(corpo) == assinaturas[numero]:
            encontrados.add(numero)
    return encontrados


def recall_artigos(referencia: list[str], recuperados: set[str]) -> float:
    esperados = {normalizar_numero_artigo(artigo) for artigo in referencia}
    return len(esperados & recuperados) / len(esperados)


def citacao_artigos(referencia: list[str], resposta: str) -> float:
    esperados = {normalizar_numero_artigo(artigo) for artigo in referencia}
    return sum(cita_artigo(resposta, artigo) for artigo in esperados) / len(esperados)
