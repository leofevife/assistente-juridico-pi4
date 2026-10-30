import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ConsultaFormulario from '@/components/ConsultaFormulario.vue'

describe('ConsultaFormulario', () => {
  it('desabilita o envio para perguntas curtas', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: 'oi' } })
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })

  it('emite a pergunta sem espaços extras ao enviar', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: '  Qual o prazo?  ' } })
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('enviar')?.[0]).toEqual(['Qual o prazo?'])
  })

  it('envia com Ctrl+Enter', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: 'Qual o prazo?' } })
    await wrapper.get('textarea').trigger('keydown', { key: 'Enter', ctrlKey: true })
    expect(wrapper.emitted('enviar')).toHaveLength(1)
  })

  it('bloqueia perguntas acima do limite', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: 'x'.repeat(11), limiteCaracteres: 10 } })
    expect(wrapper.get('textarea').attributes('aria-invalid')).toBe('true')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })

  it('mostra o botão de cancelar durante o carregamento', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: 'Qual o prazo?', carregando: true } })
    await wrapper.get('button.botao--secundario').trigger('click')
    expect(wrapper.emitted('cancelar')).toHaveLength(1)
  })

  it('envia o exemplo escolhido', async () => {
    const wrapper = mount(ConsultaFormulario, { props: { modelValue: '', exemplos: ['Prazo de arrependimento'] } })
    await wrapper.get('button.exemplo').trigger('click')
    expect(wrapper.emitted('enviar')?.[0]).toEqual(['Prazo de arrependimento'])
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['Prazo de arrependimento'])
  })
})

