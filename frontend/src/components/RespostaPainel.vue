<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import FonteArtigo from '@/components/FonteArtigo.vue'
import type { EstadoConsulta } from '@/composables/useConsulta'
import type { ErroApi } from '@/services/api'
import type { RespostaChat } from '@/types/api'
import { idFonte, normalizarArtigo, removerFontesDuplicadas } from '@/utils/fontes'
import { renderizarResposta } from '@/utils/markdown'

const props = defineProps<{
  estado: EstadoConsulta
  pergunta: string
  resultado: RespostaChat | null
  erro: ErroApi | null
  duracaoMs: number | null
}>()

const emit = defineEmits<{ tentarNovamente: [] }>()

const artigoDestacado = ref<string | null>(null)
const copiado = ref(false)
const segundosDecorridos = ref(0)
let timerCarregamento: ReturnType<typeof setInterval> | undefined
let timerCopiado: ReturnType<typeof setTimeout> | undefined

const fontes = computed(() => removerFontesDuplicadas(props.resultado?.fontes ?? []))

const htmlResposta = computed(() => {
  if (!props.resultado) return ''
  const artigos = fontes.value.map((f) => f.artigo).filter((a): a is string => !!a)
  return renderizarResposta(props.resultado.resposta, artigos)
})

const duracaoFormatada = computed(() =>
  props.duracaoMs === null ? '' : `${(props.duracaoMs / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s`,
)

const tituloErro = computed(() => {
  switch (props.erro?.tipo) {
    case 'validacao':
      return 'Revise a pergunta'
    case 'limite':
      return 'Muitas consultas seguidas'
    case 'rede':
      return 'Sem conexão com a API'
    case 'tempo_esgotado':
      return 'A consulta demorou demais'
    default:
      return 'Não foi possível consultar'
  }
})

watch(
  () => props.estado,
  (estado) => {
    clearInterval(timerCarregamento)
    if (estado !== 'carregando') return
    segundosDecorridos.value = 0
    timerCarregamento = setInterval(() => {
      segundosDecorridos.value += 1
    }, 1000)
  },
  { immediate: true },
)

watch(
  () => props.resultado,
  () => {
    artigoDestacado.value = null
  },
)

// Delegação de eventos: os links de citação são gerados dentro do HTML renderizado da resposta
function aoClicarResposta(evento: MouseEvent): void {
  const alvo = (evento.target as HTMLElement | null)?.closest<HTMLAnchorElement>('a.citacao')
  if (!alvo?.dataset.artigo) return
  evento.preventDefault()
  destacarFonte(alvo.dataset.artigo)
}

function destacarFonte(artigo: string): void {
  artigoDestacado.value = null
  // Aguarda um frame para reiniciar a animação caso o mesmo artigo seja clicado novamente
  requestAnimationFrame(() => {
    artigoDestacado.value = artigo
    const elemento = document.getElementById(idFonte(artigo))
    const reduzirMovimento = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    elemento?.scrollIntoView({ behavior: reduzirMovimento ? 'auto' : 'smooth', block: 'center' })
    elemento?.focus({ preventScroll: true })
  })
}

async function copiarResposta(): Promise<void> {
  if (!props.resultado) return
  try {
    await navigator.clipboard.writeText(props.resultado.resposta)
    copiado.value = true
    clearTimeout(timerCopiado)
    timerCopiado = setTimeout(() => (copiado.value = false), 2000)
  } catch {
    copiado.value = false
  }
}

onUnmounted(() => {
  clearInterval(timerCarregamento)
  clearTimeout(timerCopiado)
})
</script>

<template>
  <section class="painel" aria-labelledby="titulo-painel" aria-live="polite" :aria-busy="estado === 'carregando'">
    <h2 id="titulo-painel" class="visualmente-oculto">Resposta</h2>

    <div v-if="estado === 'ocioso'" class="vazio">
      <span class="vazio__marca" aria-hidden="true">§</span>
      <p class="vazio__texto">
        A resposta aparece aqui, acompanhada dos artigos do Código de Defesa do Consumidor que a fundamentam.
      </p>
    </div>

    <div v-else-if="estado === 'carregando'" class="carregando">
      <div class="meta">
        <span class="rotulo">Consultando o CDC</span>
        <span class="rotulo meta__tempo">{{ segundosDecorridos }} s</span>
      </div>
      <div class="barra" aria-hidden="true"><span /></div>
      <blockquote class="pergunta">{{ pergunta }}</blockquote>
      <div class="esqueleto" aria-hidden="true">
        <span v-for="n in 5" :key="n" :style="{ width: `${[96, 88, 92, 70, 40][n - 1]}%` }" />
      </div>
      <p class="visualmente-oculto">Buscando artigos relevantes e gerando a resposta.</p>
    </div>

    <div v-else-if="estado === 'erro' && erro" class="erro" role="alert">
      <p class="rotulo erro__codigo">{{ erro.status ? `Erro ${erro.status}` : 'Falha' }}</p>
      <h3 class="erro__titulo">{{ tituloErro }}</h3>
      <p class="erro__mensagem">
        {{ erro.message }}
        <template v-if="erro.tentarEmSegundos">Tente novamente em {{ erro.tentarEmSegundos }} s.</template>
      </p>
      <button v-if="erro.tipo !== 'validacao'" type="button" class="link" @click="emit('tentarNovamente')">
        Tentar novamente
      </button>
    </div>

    <article v-else-if="estado === 'sucesso' && resultado" class="resultado">
      <div class="meta">
        <span class="rotulo">
          Resposta
          <template v-if="fontes.length"> · {{ fontes.length }} {{ fontes.length === 1 ? 'artigo' : 'artigos' }}</template>
          <template v-if="duracaoFormatada"> · {{ duracaoFormatada }}</template>
        </span>
        <button type="button" class="link rotulo" @click="copiarResposta">
          {{ copiado ? 'Copiado' : 'Copiar' }}
        </button>
      </div>

      <blockquote class="pergunta">{{ pergunta }}</blockquote>

      <!-- HTML sanitizado com DOMPurify em renderizarResposta -->
      <div class="prosa" v-html="htmlResposta" @click="aoClicarResposta" />

      <section v-if="fontes.length" class="fundamentacao" aria-labelledby="titulo-fundamentacao">
        <h3 id="titulo-fundamentacao" class="rotulo fundamentacao__titulo">Fundamentação legal</h3>
        <FonteArtigo
          v-for="fonte in fontes"
          :key="fonte.artigo ?? fonte.trecho"
          :fonte="fonte"
          :destacada="!!fonte.artigo && artigoDestacado === normalizarArtigo(fonte.artigo)"
        />
      </section>
    </article>
  </section>
</template>

<style scoped>
.painel {
  min-height: 24rem;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.75rem;
}

.meta__tempo {
  font-variant-numeric: tabular-nums;
}

.pergunta {
  margin: 1.5rem 0 2rem;
  padding-left: 1.25rem;
  border-left: 2px solid var(--linha-forte);
  font-family: var(--fonte-serifa);
  font-style: italic;
  font-size: 1.375rem;
  line-height: 1.4;
  color: var(--tinta-2);
  overflow-wrap: anywhere;
}

.vazio {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding-top: 1rem;
  max-width: 34rem;
}

.vazio__marca {
  font-family: var(--fonte-serifa);
  font-size: 7rem;
  line-height: 0.8;
  color: var(--linha);
}

.vazio__texto {
  font-family: var(--fonte-serifa);
  font-size: 1.25rem;
  line-height: 1.5;
  color: var(--tinta-3);
}

.barra {
  position: relative;
  height: 1px;
  overflow: hidden;
  background: var(--linha);
}

.barra span {
  position: absolute;
  inset: 0 auto 0 0;
  width: 30%;
  background: var(--acento);
  animation: deslizar 1.4s var(--curva) infinite;
}

@keyframes deslizar {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(340%);
  }
}

.esqueleto {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.esqueleto span {
  height: 0.875rem;
  border-radius: var(--raio);
  background: var(--papel-3);
  animation: pulsar 1.6s ease-in-out infinite;
}

.esqueleto span:nth-child(2n) {
  animation-delay: 160ms;
}

@keyframes pulsar {
  50% {
    opacity: 0.45;
  }
}

.erro {
  padding: 1.5rem 0 1.5rem 1.5rem;
  border-left: 2px solid var(--acento);
  max-width: 36rem;
}

.erro__codigo {
  color: var(--acento);
}

.erro__titulo {
  margin: 0.5rem 0 0.75rem;
  font-family: var(--fonte-serifa);
  font-weight: 400;
  font-size: 1.75rem;
  line-height: 1.2;
}

.erro__mensagem {
  color: var(--tinta-2);
}

.link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--tinta);
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-color: var(--linha);
  transition: text-decoration-color var(--duracao) var(--curva);
}

.link:hover {
  text-decoration-color: var(--acento);
}

.erro .link {
  margin-top: 1.25rem;
}

.prosa {
  max-width: 66ch;
  font-family: var(--fonte-serifa);
  font-size: 1.1875rem;
  line-height: 1.65;
  overflow-wrap: break-word;
}

.prosa :deep(> * + *) {
  margin-top: 1em;
}

.prosa :deep(h1),
.prosa :deep(h2),
.prosa :deep(h3),
.prosa :deep(h4) {
  margin-top: 1.75em;
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.3;
}

.prosa :deep(strong) {
  font-weight: 600;
}

.prosa :deep(ul),
.prosa :deep(ol) {
  padding-left: 1.25em;
}

.prosa :deep(li + li) {
  margin-top: 0.375em;
}

.prosa :deep(li::marker) {
  color: var(--tinta-3);
}

.prosa :deep(blockquote) {
  margin-inline: 0;
  padding: 0.25em 0 0.25em 1.25em;
  border-left: 1px solid var(--linha);
  color: var(--tinta-2);
}

.prosa :deep(code) {
  font-family: var(--fonte-mono);
  font-size: 0.85em;
}

.prosa :deep(hr) {
  border: 0;
  border-top: 1px solid var(--linha);
}

.prosa :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95em;
}

.prosa :deep(th),
.prosa :deep(td) {
  padding: 0.5em 0.75em 0.5em 0;
  border-bottom: 1px solid var(--linha);
  text-align: left;
  vertical-align: top;
}

.prosa :deep(a) {
  color: inherit;
  text-underline-offset: 3px;
}

.prosa :deep(a.citacao) {
  color: var(--acento);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-decoration-color: color-mix(in srgb, var(--acento) 40%, transparent);
  white-space: nowrap;
}

.prosa :deep(a.citacao:hover) {
  text-decoration-color: var(--acento);
}

.fundamentacao {
  margin-top: 3.5rem;
}

.fundamentacao__titulo {
  padding-bottom: 0.75rem;
  color: var(--tinta);
}
</style>
