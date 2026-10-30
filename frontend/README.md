# Frontend — Assistente Jurídico CDC

Interface web editorial em **Vue 3 + TypeScript + Vite** para consultas sobre o Código de Defesa do Consumidor (Lei nº 8.078/1990), integrada à API FastAPI do backend.

## Stack e Arquitetura

- **Vue 3** (`<script setup lang="ts">`) + **Vite 7** + **TypeScript 5.8**
- **Tipografia editorial**: *Newsreader Variable* (serifa literária para leitura e títulos), *Instrument Sans Variable* (interface) e *IBM Plex Mono* (metadados, contadores e referências legais), servidas localmente via `@fontsource`.
- **Renderização segura**: Markdown convertido com `marked` e sanitizado com `DOMPurify`, com vinculação automática de citações (`Art. 49`, `Art. 18`, etc.) aos cartões da fundamentação legal.
- **Testes automatizados**: `Vitest` + `@vue/test-utils` + `jsdom`.

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── AppCabecalho.vue          # Cabeçalho e indicador de conexão com a API
│   │   ├── ConsultaFormulario.vue    # Entrada de texto, contador, atalhos e exemplos
│   │   ├── FonteArtigo.vue           # Cartão individual de artigo citado e hierarquia legal
│   │   └── RespostaPainel.vue        # Painel de resposta, estados (ocioso/loading/erro) e citações
│   ├── composables/
│   │   ├── useConsulta.ts            # Ciclo de requisição, cancelamento (AbortController) e tempo
│   │   └── useStatusApi.ts           # Sondagem periódica de prontidão (/api/v1/ready)
│   ├── services/
│   │   └── api.ts                    # Cliente HTTP com timeout, cancelamento e tradução de erros
│   ├── styles/
│   │   ├── tokens.css                # Paleta papel/tinta (claro e escuro automático) e tipografia
│   │   └── base.css                  # Reset, foco acessível e utilitários tipográficos
│   ├── types/
│   │   └── api.ts                    # Contratos TypeScript espelhados do backend
│   ├── utils/
│   │   ├── fontes.ts                 # Limpeza e deduplicação dos trechos do CDC
│   │   └── markdown.ts               # Sanitização HTML e linkagem das citações de artigos
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Como executar

1. Instale as dependências:
   ```powershell
   cd frontend
   npm install
   ```

2. Inicie o servidor de desenvolvimento (com o backend rodando na porta `8000`):
   ```powershell
   npm run dev
   ```
   Acesse: **http://localhost:5173**

   > Em desenvolvimento, o Vite faz proxy automático de `/api` para `http://localhost:8000`, evitando problemas de CORS.

## Comandos disponíveis

| Comando | Descrição |
|---|---|
| `npm run dev` | Servidor de desenvolvimento em `http://localhost:5173` |
| `npm test` | Executa os 32 testes automatizados com Vitest |
| `npm run typecheck` | Verificação estrita de tipos com `vue-tsc` |
| `npm run build` | Gera o bundle otimizado de produção em `dist/` |
| `npm run preview` | Visualiza o build de produção localmente |

