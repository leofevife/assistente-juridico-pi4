import type { FonteLegal } from '@/types/api'

const VALOR_GENERICO = 'geral'

export function normalizarArtigo(artigo: string): string {
  return artigo.replace(/[º°]/g, '').replace(/\s+/g, '').toUpperCase()
}

export function idFonte(artigo: string): string {
  return `fonte-art-${normalizarArtigo(artigo).replace(/[^0-9A-Z-]/g, '')}`
}

export function rotuloArtigo(fonte: FonteLegal): string {
  return fonte.artigo ? `Art. ${fonte.artigo}` : 'Trecho'
}

// Remove o prefixo de hierarquia "[Título | Capítulo]" e o "Art. N" inseridos na ingestão,
// já que essas informações são exibidas separadamente na interface
export function limparTrecho(trecho: string): string {
  return trecho
    .replace(/^\s*\[[^\]]*\]\s*/, '')
    .replace(/^Art\.\s*[\dA-Za-z-]+\s*[º°]?\s*\.?\s*/, '')
    .trim()
}

export function caminhoHierarquico(fonte: FonteLegal): string[] {
  return [fonte.titulo, fonte.capitulo, fonte.secao]
    .filter((parte): parte is string => !!parte && parte.trim().toLowerCase() !== VALOR_GENERICO)
    .map((parte) => parte.trim())
}

export function removerFontesDuplicadas(fontes: FonteLegal[]): FonteLegal[] {
  const vistos = new Set<string>()
  return fontes.filter((fonte) => {
    const chave = fonte.artigo ? normalizarArtigo(fonte.artigo) : fonte.trecho
    if (vistos.has(chave)) return false
    vistos.add(chave)
    return true
  })
}

