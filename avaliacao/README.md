# Avaliação do assistente jurídico

Conjunto Ground Truth e ferramentas para medir a qualidade do pipeline RAG sobre o Código de Defesa do Consumidor.

## Estrutura

```
avaliacao/
├── dados/
│   └── ground_truth.json    # Casos de avaliação versionados
├── tests/                   # Testes automatizados do módulo
├── ground_truth.py          # Modelos, carga e validação do conjunto
├── cli.py                   # Comandos: python -m avaliacao <comando>
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
