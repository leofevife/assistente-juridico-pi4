import { describe, expect, it } from 'vitest'
import { renderizarResposta } from '@/utils/markdown'

function montar(html: string): HTMLDivElement {
  const div = document.createElement('div')
  div.innerHTML = html
  return div
}

describe('renderizarResposta', () => {
  it('converte markdown básico', () => {
    const div = montar(renderizarResposta('**Prazo** de 7 dias.\n\n- item'))
    expect(div.querySelector('strong')?.textContent).toBe('Prazo')
    expect(div.querySelector('li')?.textContent).toBe('item')
  })

  it('remove scripts, handlers e URLs perigosas', () => {
    const html = renderizarResposta(
      '<script>alert(1)</script><img src=x onerror="alert(1)"><a href="javascript:alert(1)">x</a>',
    )
    expect(html).not.toContain('<script')
    expect(html).not.toContain('onerror')
    expect(html).not.toContain('<img')
    expect(html).not.toContain('javascript:')
  })

  it('vincula apenas citações de artigos presentes nas fontes', () => {
    const div = montar(renderizarResposta('Conforme o Art. 49 e o art. 18, mas não o Art. 100.', ['49', '18']))
    const citacoes = [...div.querySelectorAll<HTMLAnchorElement>('a.citacao')]

    expect(citacoes.map((c) => c.dataset.artigo)).toEqual(['49', '18'])
    expect(citacoes[0]?.getAttribute('href')).toBe('#fonte-art-49')
    expect(div.textContent).toContain('Art. 100')
  })

  it('reconhece variações como ordinal e "Artigo"', () => {
    const div = montar(renderizarResposta('Veja o Art. 6º e o Artigo 26.', ['6', '26']))
    expect(div.querySelectorAll('a.citacao')).toHaveLength(2)
  })

  it('não cria citações dentro de código', () => {
    const div = montar(renderizarResposta('`Art. 49`', ['49']))
    expect(div.querySelector('a.citacao')).toBeNull()
  })

  it('abre links externos com proteção de opener', () => {
    const div = montar(renderizarResposta('[Procon](https://www.procon.sp.gov.br)'))
    const link = div.querySelector('a')
    expect(link?.target).toBe('_blank')
    expect(link?.rel).toContain('noopener')
  })
})

