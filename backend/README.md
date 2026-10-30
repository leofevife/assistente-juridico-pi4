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
pip install -r requirements-dev.txt
Copy-Item backend/.env.example backend/.env   # preencha as chaves
```

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

## Segurança e escalabilidade

- Segredos lidos via `pydantic-settings` como `SecretStr` (não aparecem em logs/repr).
- CORS restrito às origens de `CORS_ORIGENS`, apenas `GET`/`POST`.
- Validação de entrada: tamanho mínimo/máximo, normalização de espaços e rejeição de campos extras.
- Rate limit por IP (`RATE_LIMIT_REQUISICOES` por `RATE_LIMIT_JANELA_SEGUNDOS`), com `Retry-After`.
- Erros internos são registrados em log e o cliente recebe apenas mensagens genéricas.
- Cabeçalhos de segurança (`nosniff`, `X-Frame-Options`, `no-store`).
- Prompt instrui o LLM a ignorar tentativas de alterar suas regras (mitigação de prompt injection).
- Modelo de embedding e conexões são carregados uma única vez no startup (lifespan).
- O rate limit é em memória (por instância). Para múltiplas réplicas, substituir por armazenamento compartilhado (ex: Redis).

