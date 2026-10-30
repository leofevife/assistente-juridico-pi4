import type { RespostaChat, StatusProntidao, TipoErroApi } from '@/types/api'

const URL_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')
const TIMEOUT_PADRAO_MS = 60_000

export class ErroApi extends Error {
  constructor(
    public readonly tipo: TipoErroApi,
    message: string,
    public readonly status?: number,
    public readonly tentarEmSegundos?: number,
  ) {
    super(message)
    this.name = 'ErroApi'
  }
}

interface OpcoesRequisicao {
  metodo?: 'GET' | 'POST'
  corpo?: unknown
  sinal?: AbortSignal
  timeoutMs?: number
}

// Une o cancelamento feito pelo usuário com o timeout, para que qualquer um deles aborte o fetch
function combinarSinais(sinalExterno: AbortSignal | undefined, timeoutMs: number) {
  const controlador = new AbortController()
  let expirou = false

  const timer = setTimeout(() => {
    expirou = true
    controlador.abort()
  }, timeoutMs)

  const repassarAbort = () => controlador.abort()
  sinalExterno?.addEventListener('abort', repassarAbort, { once: true })

  return {
    sinal: controlador.signal,
    expirou: () => expirou,
    limpar: () => {
      clearTimeout(timer)
      sinalExterno?.removeEventListener('abort', repassarAbort)
    },
  }
}

async function extrairDetalhe(resposta: Response): Promise<string | undefined> {
  try {
    const corpo = await resposta.json()
    if (typeof corpo?.detail === 'string') return corpo.detail
    // Erros de validação do FastAPI chegam como lista
    if (Array.isArray(corpo?.detail) && typeof corpo.detail[0]?.msg === 'string') {
      return corpo.detail[0].msg.replace(/^Value error,\s*/i, '')
    }
  } catch {
    return undefined
  }
  return undefined
}

async function converterErroHttp(resposta: Response): Promise<ErroApi> {
  const detalhe = await extrairDetalhe(resposta)

  if (resposta.status === 422) {
    return new ErroApi('validacao', detalhe ?? 'A pergunta enviada não é válida.', 422)
  }
  if (resposta.status === 429) {
    const tentarEm = Number(resposta.headers.get('Retry-After')) || undefined
    return new ErroApi(
      'limite',
      'Muitas consultas em pouco tempo. Aguarde um instante antes de tentar novamente.',
      429,
      tentarEm,
    )
  }
  if (resposta.status === 503) {
    return new ErroApi(
      'indisponivel',
      detalhe ?? 'O serviço de respostas está indisponível no momento.',
      503,
    )
  }
  return new ErroApi('desconhecido', 'Ocorreu um erro inesperado no servidor.', resposta.status)
}

async function requisitar<T>(caminho: string, opcoes: OpcoesRequisicao = {}): Promise<T> {
  const { metodo = 'GET', corpo, sinal, timeoutMs = TIMEOUT_PADRAO_MS } = opcoes
  const controle = combinarSinais(sinal, timeoutMs)

  try {
    const resposta = await fetch(`${URL_BASE}${caminho}`, {
      method: metodo,
      headers: corpo !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
      signal: controle.sinal,
      credentials: 'omit',
    })

    if (!resposta.ok) throw await converterErroHttp(resposta)
    return (await resposta.json()) as T
  } catch (erro) {
    if (erro instanceof ErroApi) throw erro
    if (erro instanceof DOMException && erro.name === 'AbortError') {
      if (controle.expirou()) {
        throw new ErroApi('tempo_esgotado', 'A resposta demorou mais do que o esperado. Tente novamente.')
      }
      throw erro
    }
    throw new ErroApi('rede', 'Não foi possível conectar ao servidor. Verifique se a API está em execução.')
  } finally {
    controle.limpar()
  }
}

export function enviarPergunta(pergunta: string, sinal?: AbortSignal): Promise<RespostaChat> {
  return requisitar<RespostaChat>('/api/v1/chat', { metodo: 'POST', corpo: { pergunta }, sinal })
}

export function verificarProntidao(sinal?: AbortSignal): Promise<StatusProntidao> {
  return requisitar<StatusProntidao>('/api/v1/ready', { sinal, timeoutMs: 10_000 })
}

