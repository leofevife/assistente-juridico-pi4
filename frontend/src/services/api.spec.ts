import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErroApi, enviarPergunta } from '@/services/api'

function respostaJson(corpo: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('enviarPergunta', () => {
  it('envia a pergunta como JSON e retorna a resposta', async () => {
    const fetchFalso = vi.fn().mockResolvedValue(respostaJson({ resposta: 'ok', fontes: [] }))
    vi.stubGlobal('fetch', fetchFalso)

    const resultado = await enviarPergunta('Qual o prazo?')

    expect(resultado).toEqual({ resposta: 'ok', fontes: [] })
    const [url, init] = fetchFalso.mock.calls[0]!
    expect(url).toBe('/api/v1/chat')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ pergunta: 'Qual o prazo?' })
    expect(init.credentials).toBe('omit')
  })

  it('traduz 429 com Retry-After', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respostaJson({ detail: 'limite' }, 429, { 'Retry-After': '12' })))

    const erro = await enviarPergunta('Qual o prazo?').catch((e) => e)

    expect(erro).toBeInstanceOf(ErroApi)
    expect(erro.tipo).toBe('limite')
    expect(erro.tentarEmSegundos).toBe(12)
  })

  it('extrai a mensagem de validação do FastAPI', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(respostaJson({ detail: [{ msg: 'Value error, A pergunta deve conter ao menos 3 caracteres.' }] }, 422)),
    )

    const erro = await enviarPergunta('oi').catch((e) => e)

    expect(erro.tipo).toBe('validacao')
    expect(erro.message).toBe('A pergunta deve conter ao menos 3 caracteres.')
  })

  it('identifica falha de rede', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const erro = await enviarPergunta('Qual o prazo?').catch((e) => e)
    expect(erro.tipo).toBe('rede')
  })

  it('identifica tempo esgotado', async () => {
    vi.useFakeTimers()
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(new DOMException('abort', 'AbortError')))
        }),
      ),
    )

    const promessa = enviarPergunta('Qual o prazo?').catch((e) => e)
    await vi.advanceTimersByTimeAsync(60_000)

    expect((await promessa).tipo).toBe('tempo_esgotado')
  })

  it('repassa o cancelamento feito pelo usuário sem convertê-lo em erro da API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(new DOMException('abort', 'AbortError')))
        }),
      ),
    )
    const controlador = new AbortController()

    const promessa = enviarPergunta('Qual o prazo?', controlador.signal).catch((e) => e)
    controlador.abort()

    const erro = await promessa
    expect(erro).toBeInstanceOf(DOMException)
    expect(erro.name).toBe('AbortError')
  })
})

