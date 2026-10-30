import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { idFonte, normalizarArtigo } from '@/utils/fontes'

const TAGS_PERMITIDAS = [
  'p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'blockquote',
  'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'hr', 'a',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
]

// Reconhece "Art. 49", "art. 5º", "Artigo 18" e variações com sufixo, como "Art. 4º-A"
const REGEX_CITACAO = /\b(Art(?:igo)?s?\.?)\s*(\d+)\s*[º°o]?(?:\s*-\s*([A-Z])\b)?/gi

function vincularCitacoes(raiz: HTMLElement, artigosDisponiveis: Set<string>): void {
  const percorredor = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT)
  const nos: Text[] = []

  while (percorredor.nextNode()) {
    const no = percorredor.currentNode as Text
    // Não cria links dentro de links ou blocos de código
    if (no.parentElement?.closest('a, code, pre')) continue
    nos.push(no)
  }

  for (const no of nos) {
    const texto = no.textContent ?? ''
    REGEX_CITACAO.lastIndex = 0
    if (!REGEX_CITACAO.test(texto)) continue
    REGEX_CITACAO.lastIndex = 0

    const fragmento = document.createDocumentFragment()
    let ultimoIndice = 0

    for (const correspondencia of texto.matchAll(REGEX_CITACAO)) {
      const numero = correspondencia[2] ?? ''
      const sufixo = correspondencia[3]
      const chave = normalizarArtigo(sufixo ? `${numero}-${sufixo}` : numero)
      if (!artigosDisponiveis.has(chave)) continue

      const inicio = correspondencia.index ?? 0
      fragmento.append(texto.slice(ultimoIndice, inicio))

      const link = document.createElement('a')
      link.className = 'citacao'
      link.href = `#${idFonte(chave)}`
      link.dataset.artigo = chave
      link.textContent = correspondencia[0]
      fragmento.append(link)

      ultimoIndice = inicio + correspondencia[0].length
    }

    if (ultimoIndice === 0) continue
    fragmento.append(texto.slice(ultimoIndice))
    no.replaceWith(fragmento)
  }
}

function protegerLinksExternos(raiz: HTMLElement): void {
  raiz.querySelectorAll<HTMLAnchorElement>('a:not(.citacao)').forEach((link) => {
    link.target = '_blank'
    link.rel = 'noopener noreferrer nofollow'
  })
}

// O texto vem do LLM, então é tratado como não confiável: o HTML é sanitizado antes de qualquer manipulação
export function renderizarResposta(markdown: string, artigosDisponiveis: Iterable<string> = []): string {
  const htmlBruto = marked.parse(markdown, { async: false, gfm: true, breaks: false }) as string
  const htmlSeguro = DOMPurify.sanitize(htmlBruto, {
    ALLOWED_TAGS: TAGS_PERMITIDAS,
    ALLOWED_ATTR: ['href', 'title'],
    ALLOWED_URI_REGEXP: /^(?:https?:|mailto:|#)/i,
  })

  const container = document.createElement('div')
  container.innerHTML = htmlSeguro

  vincularCitacoes(container, new Set(Array.from(artigosDisponiveis, normalizarArtigo)))
  protegerLinksExternos(container)

  return container.innerHTML
}

