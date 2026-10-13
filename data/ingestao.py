import os
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# 1. Carrega variáveis de ambiente e define o caminho do arquivo
load_dotenv()
diretorio_atual = Path(__file__).resolve().parent
caminho_txt = diretorio_atual / "resources" / "cdc_limpo.txt"

# 2. Lê o texto limpo gerado pelo seu script de extração
try:
    texto_completo = caminho_txt.read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"Erro: Arquivo não encontrado em {caminho_txt}")
    print("Rode o seu script de extração do PDF primeiro!")
    exit(1)

# 3. Função de Chunking Estruturado (Mantém Título, Capítulo e Seção)
def extrair_artigos_estruturados(texto: str) -> list[Document]:
    # Limpeza de artefatos residuais de PDF (ex: marca d'água CÓDIGO invertida)
    texto = re.sub(r"\bOGIDÓC\b", "", texto)

    # Regex para a estrutura legal
    re_titulo = re.compile(r"^(TÍTULO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_capitulo = re.compile(r"^(CAPÍTULO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_secao = re.compile(r"^(SEÇÃO\s+[IVXLCDM]+)(.*)$", re.IGNORECASE)
    re_artigo = re.compile(r"^Art\.\s*(\d+[º\dA-Za-z-]*)\.?\s*(.*)$")

    linhas = [linha.strip() for linha in texto.split("\n") if linha.strip()]
    documentos = []
    
    # Variáveis de estado
    titulo_atual = "Disposições Preliminares"
    capitulo_atual = "Geral"
    secao_atual = "Geral"
    
    artigo_numero = None
    buffer_artigo = []

    def salvar_artigo_atual():
        if artigo_numero and buffer_artigo:
            corpo = " ".join(buffer_artigo)
            
            # Prefixo contextual inserido no texto para o modelo de embedding
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
                    "tipo": "Artigo"
                }
            )
            documentos.append(doc)

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        # Identifica Título
        match_tit = re_titulo.match(linha)
        if match_tit:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_tit.group(1).title()
            complemento = match_tit.group(2).strip()
            # Se o complemento está vazio, o nome do título provavelmente está na linha de baixo
            if not complemento and i + 1 < len(linhas) and not re_capitulo.match(linhas[i+1]) and not re_artigo.match(linhas[i+1]):
                i += 1
                complemento = " - " + linhas[i]
            titulo_atual = f"{rotulo}{complemento}"
            capitulo_atual = "Geral"
            secao_atual = "Geral"
            i += 1
            continue

        # Identifica Capítulo
        match_cap = re_capitulo.match(linha)
        if match_cap:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_cap.group(1).title()
            complemento = match_cap.group(2).strip()
            if not complemento and i + 1 < len(linhas) and not re_secao.match(linhas[i+1]) and not re_artigo.match(linhas[i+1]):
                i += 1
                complemento = " - " + linhas[i]
            capitulo_atual = f"{rotulo}{complemento}"
            secao_atual = "Geral"
            i += 1
            continue

        # Identifica Seção
        match_sec = re_secao.match(linha)
        if match_sec:
            salvar_artigo_atual()
            buffer_artigo = []
            artigo_numero = None
            rotulo = match_sec.group(1).title()
            complemento = match_sec.group(2).strip()
            if not complemento and i + 1 < len(linhas) and not re_artigo.match(linhas[i+1]):
                i += 1
                complemento = " - " + linhas[i]
            secao_atual = f"{rotulo}{complemento}"
            i += 1
            continue

        # Identifica o início de um novo Artigo
        match_art = re_artigo.match(linha)
        if match_art:
            salvar_artigo_atual() # Salva o anterior antes de começar o novo
            artigo_numero = match_art.group(1).replace("°", "").replace("º", "")
            buffer_artigo = [match_art.group(2).strip()]
            i += 1
            continue

        # Se já estivermos dentro de um artigo, anexa as linhas (parágrafos, incisos)
        if artigo_numero is not None:
            buffer_artigo.append(linha)

        i += 1

    # Garante que o último artigo do arquivo seja salvo
    salvar_artigo_atual()
    
    return documentos

# 4. Executa a extração
print("Segmentando a lei e mapeando a hierarquia jurídica...")
chunks = extrair_artigos_estruturados(texto_completo)
print(f"Total de artigos extraídos: {len(chunks)}\n")

# 5. Inicializa o modelo de Embedding
print("Carregando modelo BAAI/bge-m3...")
gerador_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cpu'}, 
    encode_kwargs={'normalize_embeddings': True}
)

# 6. Conecta e envia para o Qdrant Cloud
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_url or not qdrant_api_key:
    print("Erro: Variáveis QDRANT_URL e QDRANT_API_KEY não encontradas no .env")
    exit(1)

nome_colecao = "cdc_vetores"

print(f"Calculando embeddings e enviando para o Qdrant Cloud ({nome_colecao})...")
QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=gerador_embeddings,
    url=qdrant_url,
    api_key=qdrant_api_key,
    collection_name=nome_colecao,
    force_recreate=True  # ATENÇÃO: Recria a coleção inteira a cada execução
)

print("\nIngestão finalizada com sucesso! Seu banco vetorial está pronto.")