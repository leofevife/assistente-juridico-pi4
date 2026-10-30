import { afterEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { useConsulta } from '@/composables/useConsulta'
import { ErroApi, enviarPergunta } from '@/services/api'
import type { RespostaChat } from '@/types/api'

vi.mock('@/services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/services/api')>()),
  enviarPergunta: vi.fn(),
}))

const enviarFalso = vi.mocked(enviarPergunta)

afterEach(() => enviarFalso.mockReset())

function criar() {
  const escopo = effectScope()
  const consulta = escopo.run(() => useConsulta())!
  return { escopo, consulta }
}

describe('useConsulta', () => {
  it('passa por carregando e termina em sucesso', async () => {
    enviarFalso.mockResolvedValue({ resposta: 'ok', fontes: [] })
    const { consulta } = criar()

    const promessa = consulta.consultar('  Qual o prazo?  ')
    expect(consulta.estado.value).toBe('carregando')
    expect(consulta.perguntaEnviada.value).toBe('Qual o prazo?')

    await promessa
    expect(consulta.estado.value).toBe('sucesso')
    expect(consulta.resultado.value?.resposta).toBe('ok')
    expect(consulta.duracaoMs.value).not.toBeNull()
  })

  it('registra o erro da API', async () => {
    enviarFalso.mockRejectedValue(new ErroApi('indisponivel', 'fora do ar', 503))
    const { consulta } = criar()

    await consulta.consultar('Qual o prazo?')

    expect(consulta.estado.value).toBe('erro')
    expect(consulta.erro.value?.tipo).toBe('indisponivel')
  })

  it('ignora perguntas vazias', async () => {
    const { consulta } = criar()

    await consulta.consultar('   ')

    expect(enviarFalso).not.toHaveBeenCalled()
    expect(consulta.estado.value).toBe('ocioso')
  })

  it('descarta a resposta de uma consulta substituída por outra', async () => {
    let resolverPrimeira: (valor: RespostaChat) => void = () => {}
    enviarFalso
      .mockImplementationOnce(() => new Promise<RespostaChat>((resolve) => (resolverPrimeira = resolve)))
      .mockResolvedValueOnce({ resposta: 'segunda', fontes: [] })
    const { consulta } = criar()

    const primeira = consulta.consultar('primeira pergunta')
    await consulta.consultar('segunda pergunta')
    resolverPrimeira({ resposta: 'primeira', fontes: [] })
    await primeira

    expect(consulta.resultado.value?.resposta).toBe('segunda')
  })

  it('cancelar volta ao estado anterior e aborta a requisição', () => {
    enviarFalso.mockImplementation(() => new Promise(() => {}))
    const { consulta } = criar()

    consulta.consultar('Qual o prazo?')
    const sinal = enviarFalso.mock.calls[0]?.[1]
    consulta.cancelar()

    expect(consulta.estado.value).toBe('ocioso')
    expect(sinal?.aborted).toBe(true)
  })

  it('aborta a requisição pendente quando o escopo é descartado', () => {
    enviarFalso.mockImplementation(() => new Promise(() => {}))
    const { escopo, consulta } = criar()

    consulta.consultar('Qual o prazo?')
    escopo.stop()

    expect(enviarFalso.mock.calls[0]?.[1]?.aborted).toBe(true)
  })
})
