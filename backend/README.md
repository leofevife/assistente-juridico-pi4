# Backend - Assistente Jurídico CDC

API FastAPI que orquestra o pipeline RAG (Qdrant + BAAI/bge-m3 + Groq via LangChain).

## Estrutura

```
backend/
├── api/
│   ├── dependencies.py     # Injeção do serviço e rate limit
│   ├── schemas.py          # Contratos de entrada/saída (Pydantic)
│   └── routes/
│       ├── chat.py         # POST /api/v1/chat
│       └── saude.py        # GET /api/v1/health e /api/v1/ready
├── core/
│   ├── config.py           # Configurações centralizadas (.env)
│   ├── logging_config.py
│   └── rate_limit.py       # Limitador por IP (janela deslizante)
├── data/
│   └── repositorio_vetorial.py
├── services/
│   └── rag_service.py
├── tests/                  # test_*.py = automatizados | teste_*.py = scripts manuais com rede
└── main.py                 # create_app() + lifespan
```

## Configuração

```powershell
# Ambiente completo (desenvolvimento, embeddings locais, ingestão, testes e RAGAS)
pip install -r requirements-dev.txt

# Ou apenas dependências enxutas de produção da API (requer EMBEDDING_PROVEDOR=api e HF_API_TOKEN)
pip install -r requirements.txt

Copy-Item backend/.env.example backend/.env   # preencha as chaves
```

### Modo de Embedding (`EMBEDDING_PROVEDOR`)

- `auto` *(padrão)*: utiliza `HuggingFaceEndpointEmbeddings` (provedor `hf-inference` via HTTP) se `HF_API_TOKEN` (ou `HUGGINGFACEHUB_API_TOKEN` / `HF_TOKEN`) estiver preenchido; caso contrário, carrega o `BAAI/bge-m3` localmente via `sentence-transformers`.
- `api`: força o uso do endpoint HTTP da Hugging Face (exige `HF_API_TOKEN`), eliminando a necessidade de instalar `sentence-transformers`/`torch` ou carregar o modelo na memória RAM em produção.
- `local`: força o carregamento local via `HuggingFaceEmbeddings` em CPU.

## Execução (a partir da raiz do projeto)

```powershell
python -m uvicorn backend.main:app --reload
```

Documentação interativa: http://localhost:8000/docs (desabilitada quando `AMBIENTE=producao`).

Em produção, rode atrás de um proxy reverso com `--proxy-headers --forwarded-allow-ips=<ip-do-proxy>` para que o rate limit identifique o IP real do cliente.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/health` | Liveness: a API está no ar |
| GET | `/api/v1/ready` | Readiness: serviço carregado e Qdrant acessível (503 caso contrário) |
| POST | `/api/v1/chat` | Recebe `{"pergunta": "..."}` e retorna `{"resposta": "...", "fontes": [...]}` |

Exemplo de resposta do chat:

```json
{
  "resposta": "Conforme o Art. 49, o consumidor pode desistir...",
  "fontes": [
    {
      "lei": "Lei 8.078/1990 (CDC)",
      "titulo": "Título I - Dos Direitos do Consumidor",
      "capitulo": "Capítulo VI - Da Proteção Contratual",
      "secao": "Seção I - Disposições Gerais",
      "artigo": "49",
      "trecho": "[...] Art. 49 O consumidor pode desistir do contrato..."
    }
  ]
}
```

## Testes

```powershell
python -m pytest
```

Os testes automatizados usam retriever e LLM falsos, portanto não consomem a API da Groq nem o Qdrant.

## Avaliação de Qualidade (RAGAS)

O pipeline foi submetido a testes automatizados em [avaliacao](../avaliacao/README.md) sobre 32 casos de Ground Truth do CDC para validar os indicadores `Faithfulness` (`> 0,850`) e `Answer Relevance` (`> 0,800`):

- **Diagnóstico do `baseline`**: atingiu `Faithfulness = 0,911`, mas não bateu a meta de `Answer Relevance` (`0,773`). A análise identificou decretos/portarias anexados após o Art. 119 no texto extraído do PDF (fazendo o retriever confundir artigos infralegais com o CDC em casos como `gt-023` e `gt-028`), falha na regex para artigos com `°` (`1°` a `9°`), busca puramente densa em artigos longos com múltiplos incisos (`Art. 6º, VIII`), respostas extensas em múltiplos parágrafos/listas e o prompt reverso do `ResponseRelevancy` configurado em inglês.
- **Correções aplicadas no backend e na ingestão**:
  - `scripts/ingestao.py` foi corrigido para interromper antes dos decretos anexos e reconhecer `[º°]`, reindexando os **120 artigos** exclusivos do CDC no Qdrant Cloud.
  - `backend/data/repositorio_vetorial.py` passou a usar `RetrieverCDC` híbrido com filtro defensivo (`eh_documento_cdc`), deduplicação por artigo e desempate lexical ponderado por IDF sobre os 120 artigos, mantendo `RETRIEVER_K=4`.
  - `backend/services/rag_service.py` teve o prompt ajustado para respostas em parágrafo único objetivo (2 a 3 frases em texto corrido, mapeando termos coloquiais aos institutos do CDC) e cadeia `with_fallbacks` entre modelos da Groq (`openai/gpt-oss-120b`, `openai/gpt-oss-20b` e `qwen/qwen3.8-27b`).
  - `avaliacao/metricas.py` adaptou o prompt de `Answer Relevance` para português e adicionou seleção priorizada de contexto e fallback de juízes.

| Indicador | `baseline` | `pos-ajuste` | Meta | Situação |
|---|---|---|---|---|
| Faithfulness | 0,911 | **0,884** | > 0,850 | Atingido (32/32) |
| Answer Relevance | 0,773 | **0,807** | > 0,800 | Atingido (32/32) |
| Recall dos artigos de referência | 0,922 | **0,969** | — | 30/32 casos = 1,000 |
| Citação dos artigos de referência | 0,922 | **0,938** | — | — |

O detalhamento por caso e os relatórios completos estão em [avaliacao/README.md](../avaliacao/README.md).

## Segurança e escalabilidade

- Segredos lidos via `pydantic-settings` como `SecretStr` (não aparecem em logs/repr).
- CORS restrito às origens de `CORS_ORIGENS`, apenas `GET`/`POST`.
- Validação de entrada: tamanho mínimo/máximo, normalização de espaços e rejeição de campos extras.
- Rate limit por IP (`RATE_LIMIT_REQUISICOES` por `RATE_LIMIT_JANELA_SEGUNDOS`), com `Retry-After`.
- Erros internos são registrados em log e o cliente recebe apenas mensagens genéricas.
- Cabeçalhos de segurança (`nosniff`, `X-Frame-Options`, `no-store`).
- Prompt instrui o LLM a ignorar tentativas de alterar suas regras (mitigação de prompt injection).
- Cliente de embedding e conexões são inicializados uma única vez no startup (lifespan); em modo remoto (`EMBEDDING_PROVEDOR=api` ou `auto` com `HF_API_TOKEN`), o servidor não carrega `BAAI/bge-m3` na memória RAM local.
- O rate limit é em memória (por instância). Para múltiplas réplicas, substituir por armazenamento compartilhado (ex: Redis).

