import { describe, expect, it } from 'vitest'
import type { FonteLegal } from '@/types/api'
import { caminhoHierarquico, idFonte, limparTrecho, normalizarArtigo, removerFontesDuplicadas } from '@/utils/fontes'

const fonte = (sobrescrita: Partial<FonteLegal> = {}): FonteLegal => ({
  lei: 'Lei 8.078/1990 (CDC)',
  titulo: 'Título I - Dos Direitos do Consumidor',
  capitulo: 'Capítulo VI - Da Proteção Contratual',
  secao: 'Geral',
  artigo: '49',
  trecho: '[Título I | Capítulo VI]\nArt. 49 O consumidor pode desistir do contrato.',
  ...sobrescrita,
})

describe('fontes', () => {
  it('remove o prefixo de hierarquia e o número do artigo do trecho', () => {
    expect(limparTrecho(fonte().trecho)).toBe('O consumidor pode desistir do contrato.')
  })

  it('ignora níveis genéricos no caminho hierárquico', () => {
    expect(caminhoHierarquico(fonte())).toEqual([
      'Título I - Dos Direitos do Consumidor',
      'Capítulo VI - Da Proteção Contratual',
    ])
  })

  it('normaliza números de artigo e gera ids seguros', () => {
    expect(normalizarArtigo('4º-a')).toBe('4-A')
    expect(idFonte('49"><script>')).toBe('fonte-art-49SCRIPT')
  })

  it('remove artigos repetidos', () => {
    const resultado = removerFontesDuplicadas([fonte(), fonte(), fonte({ artigo: '18' })])
    expect(resultado.map((f) => f.artigo)).toEqual(['49', '18'])
  })
})

