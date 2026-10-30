import { computed, onScopeDispose, ref, shallowRef } from 'vue'
import { ErroApi, enviarPergunta } from '@/services/api'
import type { RespostaChat } from '@/types/api'

export type EstadoConsulta = 'ocioso' | 'carregando' | 'sucesso' | 'erro'

export function useConsulta() {
  const estado = ref<EstadoConsulta>('ocioso')
  const perguntaEnviada = ref('')
  const resultado = shallowRef<RespostaChat | null>(null)
  const erro = shallowRef<ErroApi | null>(null)
  const duracaoMs = ref<number | null>(null)

  let controladorAtual: AbortController | null = null

  const carregando = computed(() => estado.value === 'carregando')

  async function consultar(pergunta: string): Promise<void> {
    const texto = pergunta.trim()
    if (!texto) return

    // Uma nova pergunta cancela a anterior para evitar respostas fora de ordem
    controladorAtual?.abort()
    const controlador = new AbortController()
    controladorAtual = controlador

    estado.value = 'carregando'
    perguntaEnviada.value = texto
    erro.value = null
    const inicio = performance.now()

    try {
      const resposta = await enviarPergunta(texto, controlador.signal)
      if (controlador.signal.aborted) return
      resultado.value = resposta
      duracaoMs.value = Math.round(performance.now() - inicio)
      estado.value = 'sucesso'
    } catch (e) {
      if (controlador.signal.aborted) return
      erro.value = e instanceof ErroApi ? e : new ErroApi('desconhecido', 'Ocorreu um erro inesperado.')
      estado.value = 'erro'
    } finally {
      if (controladorAtual === controlador) controladorAtual = null
    }
  }

  function cancelar(): void {
    if (!controladorAtual) return
    controladorAtual.abort()
    controladorAtual = null
    estado.value = resultado.value ? 'sucesso' : 'ocioso'
  }

  onScopeDispose(() => controladorAtual?.abort())

  return { estado, carregando, perguntaEnviada, resultado, erro, duracaoMs, consultar, cancelar }
}

