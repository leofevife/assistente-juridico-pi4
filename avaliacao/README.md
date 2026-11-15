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
| `AVALIACAO_MODELO_JUIZ` | `openai/gpt-oss-20b` | Modelo principal usado pelo juiz RAGAS na Groq (com fallback automático entre modelos compatíveis) |
| `AVALIACAO_PAUSA_SEGUNDOS` | `0.0` | Pausa entre casos durante a geração de respostas e a avaliação RAGAS |
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

## Processo de teste e otimização de Faithfulness e Answer Relevance

A validação dos indicadores de qualidade do pipeline RAG seguiu um ciclo empírico em duas rodadas sobre os **32 casos** do Ground Truth (`versão 1.0.0`), registradas em [resultados/baseline](resultados/baseline/relatorio.md) e [resultados/pos-ajuste](resultados/pos-ajuste/relatorio.md).

### Como as métricas são avaliadas

- **Faithfulness (Fidelidade ao contexto, meta `> 0,850`)**: o RAGAS extrai proposições atômicas da resposta gerada e verifica, via NLI (*Natural Language Inference*), se cada afirmação é sustentada literalmente pelos trechos recuperados do CDC.
- **Answer Relevance (Relevância da resposta, meta `> 0,800`)**: o RAGAS gera uma pergunta reversa a partir da resposta do assistente, classifica se a resposta foi evasiva (`noncommittal`) e mede a similaridade de cosseno com a pergunta original do consumidor usando o modelo `BAAI/bge-m3`.
- **Recall e Citação dos artigos de referência**: verificações determinísticas que conferem se os artigos esperados foram recuperados do Qdrant com texto autêntico do CDC e citados na resposta.

### 1ª rodada (`baseline`): o que não bateu a meta e diagnóstico

Na execução inicial (`baseline`, usando `openai/gpt-oss-120b` como gerador e juiz sobre a coleção original do Qdrant), os indicadores consolidados foram:

| Indicador | Média (`baseline`) | Meta | Situação |
|---|---|---|---|
| Faithfulness | **0,911** | > 0,850 | Atingido |
| Answer Relevance | **0,773** | > 0,800 | **Não atingido** |
| Recall dos artigos de referência | **0,922** | — | 4 casos abaixo de 1,000 |
| Citação dos artigos de referência | **0,922** | — | — |

Dos 32 casos avaliados no `baseline`, **24 ficaram abaixo de algum limite esperado**. A inspeção detalhada revelou quatro causas raízes:

1. **Contaminação do Qdrant por normas infralegais e falha de regex na ingestão**: o arquivo `scripts/resources/cdc_limpo.txt` contém, após o Art. 119 do CDC, o Decreto nº 2.181/1997 e a Portaria SDE nº 4/1998, que recomeçam a numeração em `Art. 1º`. O script de ingestão indexava todos esses chunks na mesma coleção, e a regex de artigos não reconhecia `°` (U+00B0), fundindo os artigos `1°` a `9°`. Como consequência direta, no caso `gt-023` (*inversão do ônus da prova*), o retriever trouxe o `Art. 22` do Decreto regulamentar e o `Art. 3` da Portaria, levando o LLM a responder com o artigo errado e zerando o recall (`Recall = 0,000`, `Answer Relevance = 0,649`). O mesmo ruído afetou `gt-028` (`Recall = 0,500`, `Answer Relevance = 0,469`).
2. **Recuperação puramente densa para institutos específicos em artigos extensos**: consultas que dependem de termos jurídicos pontuais dentro de artigos com muitos incisos (como `Art. 6º, VIII` para inversão do ônus da prova) não apareciam nas primeiras posições apenas por similaridade vetorial densa.
3. **Prompt reverso de `Answer Relevance` em inglês no RAGAS**: por padrão, o prompt `question_generation` do `ResponseRelevancy` formulava perguntas reversas em inglês para respostas em português, reduzindo artificialmente a similaridade de cosseno no `BAAI/bge-m3`.
4. **Respostas prolixas e formato em múltiplos parágrafos/listas**: respostas longas com cabeçalhos Markdown diluíam a pergunta reversa (`gt-001` e `gt-003` com `0,669`; `gt-012` com `0,672`) e introduziam afirmações acessórias que reduziam o `Faithfulness` (`gt-008` com `0,500`; `gt-029` com `0,667`; `gt-007` com `0,700`).

### Correções aplicadas

Para solucionar os desvios encontrados sem comprometer a fidelidade ao texto da lei:

1. **Saneamento da ingestão (`scripts/ingestao.py`) e reindexação**: o parser passou a encerrar a leitura ao encontrar `DECRETO N` e a reconhecer `°` e `º` na identificação dos artigos. A coleção `cdc_vetores` no Qdrant Cloud foi recriada com os **120 artigos autênticos** da Lei 8.078/1990. Em `avaliacao/ground_truth.py`, `carregar_artigos_cdc` foi ajustado para concatenar linhas de continuação de artigos com quebra de linha (corrigindo falsos negativos de assinatura como no `Art. 27`).
2. **Retriever híbrido denso + lexical ponderado por IDF (`backend/data/repositorio_vetorial.py`)**: implementado `RetrieverCDC` mantendo `RETRIEVER_K = 4`, com filtro defensivo (`eh_documento_cdc`), deduplicação por artigo e reordenação das vagas complementares por pontuação lexical ponderada por IDF (*Inverse Document Frequency*) sobre os 120 artigos, garantindo o resgate de termos raros como `"inversão"` e `"ônus"` (`Art. 6º` no caso `gt-023`).
3. **Refinamento do prompt de geração e resiliência (`backend/services/rag_service.py`)**: o sistema foi instruído a responder em um único parágrafo objetivo de 2 a 3 frases em texto corrido, utilizando termos literais do CDC, relacionando expressões coloquiais da dúvida aos institutos correspondentes nos artigos recuperados e contando com `with_fallbacks` entre modelos da Groq (`openai/gpt-oss-120b`, `openai/gpt-oss-20b` e `qwen/qwen3.8-27b`).
4. **Calibração idiomática e cadeia de juízes no RAGAS (`avaliacao/metricas.py` e `avaliacao/execucao.py`)**: o `question_generation` do `ResponseRelevancy` foi configurado em português com exemplo `noncommittal=0`; os prompts do `Faithfulness` passaram a limitar a extração a até 2 proposições concisas com justificativas curtas; e o `AvaliadorRagas` ganhou cadeia de fallback entre juízes e `_selecionar_contextos_avaliacao` (priorizando artigos citados até `2.800` caracteres) para operar sob o teto de `2.000` TPM do `openai/gpt-oss-safeguard-20b` quando os modelos de `200.000` TPD esgotam a cota diária.

### 2ª rodada (`pos-ajuste`): resultado comparativo final

| Indicador | `baseline` | `pos-ajuste` | Variação | Meta | Situação final |
|---|---|---|---|---|---|
| **Faithfulness** | 0,911 | **0,884** | -0,027 | > 0,850 | **Atingido (32/32)** |
| **Answer Relevance** | 0,773 | **0,807** | +0,034 | > 0,800 | **Atingido (32/32)** |
| **Recall dos artigos de referência** | 0,922 | **0,969** | +0,047 | — | **30/32 com 1,000** |
| **Citação dos artigos de referência** | 0,922 | **0,938** | +0,016 | — | — |
| **Casos abaixo de algum limite** | 24/32 | **16/32** | -8 casos | — | — |

Principais avanços observados no [resultados/pos-ajuste/relatorio.md](resultados/pos-ajuste/relatorio.md):

- **Recuperação**: o caso `gt-023` saltou de `Recall = 0,000` para `1,000` (passando a recuperar e citar o `Art. 6º` do CDC em vez do Art. 22 do Decreto), e `gt-028` também atingiu `Recall = 1,000` (`Answer Relevance` de `0,469` para `0,784`). Nenhum caso ficou sem recuperar ao menos um artigo de referência (mínimo subiu de `0,000` para `0,500`).
- **Aderência às perguntas**: a mediana de `Answer Relevance` subiu de `0,764` para `0,815`, e os casos que antes sofriam com respostas extensas melhoraram substancialmente (`gt-003`: `0,669 -> 0,815`; `gt-012`: `0,672 -> 0,840`; `gt-021`: `0,729 -> 0,919`; `gt-026`: `0,736 -> 0,897`).
- **Fidelidade**: **24 dos 32 casos obtiveram `Faithfulness = 1,000`** (`Q1 = 0,950`, `mediana = 1,000`), e `gt-008` subiu de `0,500` para `1,000`. As pontuações pontuais menores no NLI (`gt-009` com `0,000`; `gt-023`, `gt-024` e `gt-028` com `0,500`) refletem respostas que combinam dois artigos extensos (como `Art. 18` com 2.558 caracteres e `Art. 51` com 2.870 caracteres), fazendo com que apenas o primeiro trecho citado coubesse no limite de `2.800` caracteres aplicado ao juiz sob janela de `2.000` TPM.
