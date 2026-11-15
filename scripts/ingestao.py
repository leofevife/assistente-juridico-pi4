import os
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")
diretorio_atual = Path(__file__).resolve().parent
caminho_txt = diretorio_atual / "resources" / "cdc_limpo.txt"

try:
    texto_completo = caminho_txt.read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"Erro: Arquivo não encontrado em {caminho_txt}")
    print("Rode o seu script de extração do PDF primeiro!")
    exit(1)


def extrair_artigos_estruturados(texto: str) -> list[Document]:
    texto = re.sub(r"\bOGIDÓC\b", "", texto)

    re_titulo = re.compile(r"^(TÍTULO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_capitulo = re.compile(r"^(CAPÍTULO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_secao = re.compile(r"^(SEÇÃO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_artigo = re.compile(r"^Art\.\s*(\d+[º°\dA-Za-z-]*)\.?\s*(.*)$")
    re_decreto = re.compile(r"^DECRETO\s+N", re.IGNORECASE)

    linhas = []
    for bruto in texto.split("\n"):
        linha = bruto.strip()
        if not linha:
            continue
        if re_decreto.match(linha):
            break
        linhas.append(linha)

    documentos = []

    titulo_atual = "Disposições Preliminares"
    capitulo_atual = "Geral"
    secao_atual = "Geral"

    artigo_numero = None
    buffer_artigo = []

    def salvar_artigo_atual():
        if artigo_numero and buffer_artigo:
            corpo = " ".join(buffer_artigo)

            conteudo_completo = (
                f"[{titulo_atual} | {capitulo_atual}"
                + (f" | {secao_atual}" if secao_atual != "Geral" else "")
                + f"]\nArt. {artigo_numero} {corpo}"
            )

            doc = Document(
                page_content=conteudo_completo,
                metadata={
                    "lei": "Lei 8.078/1990 (CDC)",
                    "titulo": titulo_atual.strip(),
                    "capitulo": capitulo_atual.strip(),
                    "secao": secao_atual.strip(),
                    "artigo": artigo_numero.strip(),
                    "tipo": "Artigo",
                },
            )
            documentos.append(doc)

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        match_tit = re_titulo.match(linha)
        if match_tit:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_tit.group(1).title()
            complemento = match_tit.group(2).strip()
            if not complemento and i + 1 < len(linhas) and not re_capitulo.match(linhas[i + 1]) and not re_artigo.match(linhas[i + 1]):
                i += 1
                complemento = " - " + linhas[i]
            titulo_atual = f"{rotulo}{complemento}"
            capitulo_atual = "Geral"
            secao_atual = "Geral"
            i += 1
            continue

        match_cap = re_capitulo.match(linha)
        if match_cap:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_cap.group(1).title()
            complemento = match_cap.group(2).strip()
            if not complemento and i + 1 < len(linhas) and not re_secao.match(linhas[i + 1]) and not re_artigo.match(linhas[i + 1]):
                i += 1
                complemento = " - " + linhas[i]
            capitulo_atual = f"{rotulo}{complemento}"
            secao_atual = "Geral"
            i += 1
            continue

        match_sec = re_secao.match(linha)
        if match_sec:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_sec.group(1).title()
            complemento = match_sec.group(2).strip()
            if not complemento and i + 1 < len(linhas) and not re_artigo.match(linhas[i + 1]):
                i += 1
                complemento = " - " + linhas[i]
            secao_atual = f"{rotulo}{complemento}"
            i += 1
            continue

        match_art = re_artigo.match(linha)
        if match_art:
            salvar_artigo_atual()
            artigo_numero = match_art.group(1).replace("°", "").replace("º", "")
            buffer_artigo = [match_art.group(2).strip()]
            i += 1
            continue

        if artigo_numero is not None:
            buffer_artigo.append(linha)

        i += 1

    salvar_artigo_atual()

    return documentos


if __name__ == "__main__":
    print("Segmentando a lei e mapeando a hierarquia jurídica...")
    chunks = extrair_artigos_estruturados(texto_completo)
    print(f"Total de artigos extraídos: {len(chunks)}\n")

    print("Carregando modelo BAAI/bge-m3...")
    gerador_embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()

    if not qdrant_url or not qdrant_api_key:
        print("Erro: Variáveis QDRANT_URL e QDRANT_API_KEY não encontradas no .env")
        exit(1)

    qdrant_url_limpa = qdrant_url.replace(":6333", "")

    nome_colecao = "cdc_vetores"

    print(f"Testando conexão com Qdrant Cloud em: {qdrant_url_limpa} ...")

    cliente = QdrantClient(
        url=qdrant_url_limpa,
        api_key=qdrant_api_key,
        port=443,
        https=True,
        timeout=120.0,
    )

    try:
        if cliente.collection_exists(collection_name=nome_colecao):
            print(f"Coleção '{nome_colecao}' já existe. Recriando...")
            cliente.delete_collection(collection_name=nome_colecao)

        cliente.create_collection(
            collection_name=nome_colecao,
            vectors_config=models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE,
            ),
        )
        print(f"Coleção '{nome_colecao}' criada com sucesso no Qdrant Cloud!")
    except Exception as e:
        print("\nFalha ao conectar no Qdrant Cloud. Verifique:")
        print("1. Se o cluster está ATIVO (não pausado) no site do Qdrant Cloud.")
        print("2. Se a URL no .env começa com https://")
        print(f"Detalhes técnicos do erro: {e}")
        exit(1)

    vector_store = QdrantVectorStore(
        client=cliente,
        collection_name=nome_colecao,
        embedding=gerador_embeddings,
    )

    tamanho_lote = 50
    print(f"Calculando embeddings e enviando {len(chunks)} artigos em lotes de {tamanho_lote}...")

    for i in range(0, len(chunks), tamanho_lote):
        lote = chunks[i : i + tamanho_lote]
        vector_store.add_documents(lote)
        print(f" -> Lote enviado: {min(i + tamanho_lote, len(chunks))}/{len(chunks)} artigos processados.")

    print("\nIngestão finalizada com sucesso!")
