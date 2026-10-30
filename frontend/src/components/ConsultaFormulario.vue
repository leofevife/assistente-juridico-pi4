<script setup lang="ts">
import { computed, ref, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    carregando?: boolean
    limiteCaracteres?: number
    exemplos?: string[]
  }>(),
  { carregando: false, limiteCaracteres: 1000, exemplos: () => [] },
)

const emit = defineEmits<{
  enviar: [pergunta: string]
  cancelar: []
}>()

const pergunta = defineModel<string>({ default: '' })
const campo = ref<HTMLTextAreaElement | null>(null)
const idCampo = useId()
const idDica = useId()

const tamanho = computed(() => pergunta.value.trim().length)
const excedeuLimite = computed(() => tamanho.value > props.limiteCaracteres)
const podeEnviar = computed(() => tamanho.value >= 3 && !excedeuLimite.value && !props.carregando)

function enviar(): void {
  if (!podeEnviar.value) return
  emit('enviar', pergunta.value.trim())
}

function aoPressionarTecla(evento: KeyboardEvent): void {
  if (evento.key === 'Enter' && (evento.ctrlKey || evento.metaKey)) {
    evento.preventDefault()
    enviar()
  }
}

function usarExemplo(exemplo: string): void {
  pergunta.value = exemplo
  campo.value?.focus()
  emit('enviar', exemplo)
}

defineExpose({ focar: () => campo.value?.focus() })
</script>

<template>
  <form class="formulario" novalidate @submit.prevent="enviar">
    <div class="formulario__topo">
      <label :for="idCampo" class="rotulo">Sua dúvida</label>
      <span class="rotulo contador" :class="{ 'contador--excedido': excedeuLimite }" aria-live="polite">
        {{ tamanho }}/{{ limiteCaracteres }}
      </span>
    </div>

    <textarea
      :id="idCampo"
      ref="campo"
      v-model="pergunta"
      class="formulario__campo"
      rows="5"
      placeholder="Ex.: Comprei um celular que parou de funcionar em 20 dias. A loja é obrigada a trocar?"
      :aria-describedby="idDica"
      :aria-invalid="excedeuLimite"
      :readonly="carregando"
      autocomplete="off"
      spellcheck="true"
      @keydown="aoPressionarTecla"
    />

    <div class="formulario__acoes">
      <span :id="idDica" class="rotulo dica">
        <kbd>Ctrl</kbd> + <kbd>Enter</kbd> envia
      </span>

      <button v-if="carregando" type="button" class="botao botao--secundario" @click="emit('cancelar')">
        Cancelar
      </button>
      <button v-else type="submit" class="botao" :disabled="!podeEnviar">
        Consultar
        <span aria-hidden="true" class="botao__seta">→</span>
      </button>
    </div>

    <div v-if="exemplos.length" class="exemplos">
      <p class="rotulo">Experimente</p>
      <ul class="exemplos__lista">
        <li v-for="exemplo in exemplos" :key="exemplo">
          <button type="button" class="exemplo" :disabled="carregando" @click="usarExemplo(exemplo)">
            <span>{{ exemplo }}</span>
            <span aria-hidden="true" class="exemplo__seta">→</span>
          </button>
        </li>
      </ul>
    </div>
  </form>
</template>

<style scoped>
.formulario {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.formulario__topo,
.formulario__acoes {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.contador {
  font-variant-numeric: tabular-nums;
}

.contador--excedido {
  color: var(--acento);
}

.formulario__campo {
  width: 100%;
  min-height: 9rem;
  padding: 1rem 1.125rem;
  border: 1px solid var(--linha-forte);
  border-radius: var(--raio);
  background: transparent;
  font-family: var(--fonte-serifa);
  font-size: 1.125rem;
  line-height: 1.5;
  resize: vertical;
  transition: background-color var(--duracao) var(--curva);
}

.formulario__campo::placeholder {
  color: var(--tinta-3);
  font-style: italic;
}

.formulario__campo:focus {
  outline: none;
  background: var(--papel-2);
  box-shadow: inset 0 0 0 1px var(--linha-forte);
}

.formulario__campo[aria-invalid='true'] {
  border-color: var(--acento);
}

.formulario__campo:read-only {
  color: var(--tinta-2);
}

kbd {
  font-family: inherit;
  padding: 0 0.3em;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
}

.botao {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem 1.25rem;
  border: 1px solid var(--linha-forte);
  border-radius: var(--raio);
  background: var(--tinta);
  color: var(--papel);
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: background-color var(--duracao) var(--curva), color var(--duracao) var(--curva);
}

.botao:hover:not(:disabled) {
  background: var(--acento);
  border-color: var(--acento);
}

.botao:disabled {
  cursor: not-allowed;
  opacity: 0.35;
}

.botao__seta {
  transition: transform var(--duracao) var(--curva);
}

.botao:hover:not(:disabled) .botao__seta {
  transform: translateX(3px);
}

.botao--secundario {
  background: transparent;
  color: var(--tinta);
}

.botao--secundario:hover:not(:disabled) {
  color: var(--papel);
}

.exemplos {
  margin-top: 2rem;
}

.exemplos__lista {
  list-style: none;
  margin: 0.75rem 0 0;
  padding: 0;
  border-bottom: 1px solid var(--linha);
}

.exemplo {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 0;
  border: 0;
  border-top: 1px solid var(--linha);
  background: none;
  text-align: left;
  color: var(--tinta-2);
  transition: color var(--duracao) var(--curva), padding var(--duracao) var(--curva);
}

.exemplo:hover:not(:disabled) {
  color: var(--tinta);
  padding-left: 0.5rem;
}

.exemplo:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.exemplo__seta {
  color: var(--tinta-3);
  opacity: 0;
  transition: opacity var(--duracao) var(--curva);
}

.exemplo:hover:not(:disabled) .exemplo__seta {
  opacity: 1;
  color: var(--acento);
}
</style>

