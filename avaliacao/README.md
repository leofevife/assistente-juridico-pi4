# Avaliação do assistente jurídico

Conjunto Ground Truth e ferramentas para medir a qualidade do pipeline RAG sobre o Código de Defesa do Consumidor.

## Estrutura

```
avaliacao/
├── dados/
│   └── ground_truth.json    # Casos de avaliação versionados
├── resultados/              # Saídas geradas por execução (--rotulo)
├── tests/                   # Testes automatizados do módulo
├── armazenamento.py         # Leitura e gravação atômica em JSON
├── cli.py                   # Comandos: python -m avaliacao <comando>
├── cobertura.py             # Recall e citação dos artigos de referência
├── config.py                # Parâmetros e caminhos da avaliação (.env)
├── execucao.py              # Fábrica do RAG/juiz e metadados da execução
├── executor.py              # Execução do RAG sobre o Ground Truth com retomada
├── ground_truth.py          # Modelos, carga e validação do conjunto
├── metricas.py              # Avaliação com RAGAS (Faithfulness e Answer Relevance)
├── modelos.py               # Contratos Pydantic de resultados e métricas
├── relatorio.py             # Consolidação e análise em Markdown
└── __main__.py
```

## Ground Truth

[dados/ground_truth.json](dados/ground_truth.json) reúne perguntas representativas de situações reais de consumo. Cada caso possui:

| Campo | Descrição |
|---|---|
| `id` | Identificador estável (`gt-001`, `gt-002`, ...) |
| `tema` | Assunto do caso (arrependimento, garantia, vício oculto, cobrança, cláusulas abusivas, etc.) |
| `pergunta` | Dúvida escrita como um consumidor a faria |
| `resposta_esperada` | Resposta correta, redigida a partir do texto da lei, citando os artigos |
| `artigos_referencia` | Artigos do CDC que fundamentam a resposta |

### Validação

```powershell
python -m avaliacao validar
```

A validação garante que o conjunto:

- possui ao menos 30 casos, sem ids ou perguntas repetidos;
- referencia apenas artigos que existem no CDC (`scripts/resources/cdc_limpo.txt`, ignorando os decretos anexados ao arquivo);
- cita, na resposta esperada, cada artigo de referência.

Os mesmos critérios são executados em `python -m pytest`.

### Revisão jurídica

As respostas esperadas foram redigidas a partir do texto literal dos artigos e checadas automaticamente contra o CDC. A revisão final do conteúdo jurídico deve ser feita pela equipe antes de os resultados serem usados como evidência no relatório.

### Como adicionar casos

1. Inclua o novo objeto em `casos`, com o próximo `id` livre.
2. Cite na `resposta_esperada` todos os artigos listados em `artigos_referencia`.
3. Rode `python -m avaliacao validar` e `python -m pytest`.
4. Ao alterar casos existentes, incremente `versao`, pois os resultados de avaliação registram a versão usada.

## Avaliação automatizada com RAGAS

O módulo executa o conjunto Ground Truth contra o pipeline RAG real e calcula os indicadores de qualidade utilizando o RAGAS (`Faithfulness` e `ResponseRelevancy`/`Answer Relevance`), além do recall e da taxa de citação dos artigos de referência.

### Configuração

Os segredos de API (`GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`) e parâmetros do RAG são lidos de `backend/.env`. Os parâmetros específicos da avaliação podem ser ajustados no mesmo arquivo ou em variáveis de ambiente:

| Variável | Padrão | Descrição |
|---|---|---|
| `AVALIACAO_MODELO_JUIZ` | `openai/gpt-oss-120b` | Modelo usado pelo juiz RAGAS na Groq |
| `AVALIACAO_PAUSA_SEGUNDOS` | `0.0` | Pausa entre casos durante a geração de respostas |
| `AVALIACAO_TENTATIVAS` | `3` | Tentativas em caso de falha transitória na geração |
| `AVALIACAO_TIMEOUT_JUIZ_SEGUNDOS` | `120.0` | Tempo limite por chamada ao modelo juiz |

> **Nota para Python 3.14 no Windows:** a dependência opcional `scikit-network` do pacote `ragas` não possui wheel pré-compilada para Python 3.14 e não é utilizada pelas métricas `Faithfulness` e `ResponseRelevancy`. Nesse ambiente, instale com `pip install --no-deps ragas==0.4.4` e depois `pip install -r requirements-dev.txt`.

### Comandos

```powershell
# Valida o Ground Truth contra o texto do CDC
python -m avaliacao validar

# Executa todas as etapas em sequência (gerar -> avaliar -> relatorio)
python -m avaliacao executar --rotulo baseline

# Ou executa cada etapa separadamente (com suporte a retomada a partir do checkpoint)
python -m avaliacao gerar --rotulo baseline
python -m avaliacao avaliar --rotulo baseline
python -m avaliacao relatorio --rotulo baseline
```

### Artefatos gerados

Cada execução salva seus resultados em `avaliacao/resultados/<rotulo>/`:

| Arquivo | Conteúdo |
|---|---|
| `execucao.json` | Data, versão do Ground Truth e parâmetros/hash do prompt usados |
| `respostas.json` | Pergunta (por id), resposta gerada pelo RAG e trechos/metadados recuperados |
| `metricas.json` | Pontuações por caso (`faithfulness`, `answer_relevancy`, `recall_artigos`, `citacao_artigos`) e eventuais erros registrados |
| `relatorio.md` | Relatório consolidado comparando as médias às metas (`Faithfulness > 0,850` e `Answer Relevance > 0,800`) |
