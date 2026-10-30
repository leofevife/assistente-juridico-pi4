import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import RespostaPainel from '@/components/RespostaPainel.vue'
import { ErroApi } from '@/services/api'
import type { RespostaChat } from '@/types/api'

const resultado: RespostaChat = {
  resposta: 'Conforme o **Art. 49**, o prazo é de 7 dias. <img src=x onerror=alert(1)>',
  fontes: [
    {
      lei: 'Lei 8.078/1990 (CDC)',
      titulo: 'Título I',
      capitulo: 'Capítulo VI',
      secao: 'Geral',
      artigo: '49',
      trecho: '[Título I | Capítulo VI]\nArt. 49 O consumidor pode desistir do contrato.',
    },
  ],
}

const base = { pergunta: 'Qual o prazo?', resultado: null, erro: null, duracaoMs: null }

describe('RespostaPainel', () => {
  it('mostra o estado inicial', () => {
    const wrapper = mount(RespostaPainel, { props: { ...base, estado: 'ocioso' } })
    expect(wrapper.text()).toContain('A resposta aparece aqui')
  })

  it('renderiza resposta sanitizada, citação e fontes', () => {
    const wrapper = mount(RespostaPainel, {
      props: { ...base, estado: 'sucesso', resultado, duracaoMs: 2100 },
    })

    expect(wrapper.html()).not.toContain('onerror')
    expect(wrapper.find('a.citacao').attributes('href')).toBe('#fonte-art-49')
    expect(wrapper.find('#fonte-art-49').exists()).toBe(true)
    expect(wrapper.text()).toContain('O consumidor pode desistir do contrato.')
    expect(wrapper.text()).toContain('1 artigo')
  })

  it('exibe erro com tempo de espera e permite tentar novamente', async () => {
    const erro = new ErroApi('limite', 'Muitas consultas.', 429, 8)
    const wrapper = mount(RespostaPainel, { props: { ...base, estado: 'erro', erro } })

    expect(wrapper.get('[role="alert"]').text()).toContain('8 s')
    await wrapper.get('button.link').trigger('click')
    expect(wrapper.emitted('tentarNovamente')).toHaveLength(1)
  })

  it('não oferece nova tentativa para erro de validação', () => {
    const erro = new ErroApi('validacao', 'Pergunta inválida.', 422)
    const wrapper = mount(RespostaPainel, { props: { ...base, estado: 'erro', erro } })
    expect(wrapper.find('button.link').exists()).toBe(false)
  })
})

