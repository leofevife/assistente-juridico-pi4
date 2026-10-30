import { onMounted, onUnmounted, ref } from 'vue'
import { verificarProntidao } from '@/services/api'

export type StatusApi = 'verificando' | 'online' | 'offline'

const INTERVALO_MS = 60_000

export function useStatusApi() {
  const status = ref<StatusApi>('verificando')
  let timer: ReturnType<typeof setInterval> | undefined
  let controlador: AbortController | undefined

  async function verificar(): Promise<void> {
    controlador?.abort()
    controlador = new AbortController()
    try {
      const resposta = await verificarProntidao(controlador.signal)
      status.value = resposta.status === 'pronto' ? 'online' : 'offline'
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return
      status.value = 'offline'
    }
  }

  // Só verifica com a aba visível, evitando chamadas ao Qdrant enquanto ninguém está olhando
  function aoMudarVisibilidade(): void {
    if (document.visibilityState === 'visible') verificar()
  }

  onMounted(() => {
    verificar()
    timer = setInterval(() => {
      if (document.visibilityState === 'visible') verificar()
    }, INTERVALO_MS)
    document.addEventListener('visibilitychange', aoMudarVisibilidade)
  })

  onUnmounted(() => {
    clearInterval(timer)
    controlador?.abort()
    document.removeEventListener('visibilitychange', aoMudarVisibilidade)
  })

  return { status, verificar }
}

