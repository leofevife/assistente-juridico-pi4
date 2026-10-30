<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FonteLegal } from '@/types/api'
import { caminhoHierarquico, idFonte, limparTrecho, normalizarArtigo } from '@/utils/fontes'

const props = defineProps<{
  fonte: FonteLegal
  destacada?: boolean
}>()

const expandida = ref(false)
const trecho = computed(() => limparTrecho(props.fonte.trecho))
const caminho = computed(() => caminhoHierarquico(props.fonte))
const id = computed(() => (props.fonte.artigo ? idFonte(props.fonte.artigo) : undefined))
const numero = computed(() => (props.fonte.artigo ? normalizarArtigo(props.fonte.artigo) : '—'))
const longo = computed(() => trecho.value.length > 280)

// Ao clicar numa citação da resposta, o artigo correspondente é aberto por completo
watch(
  () => props.destacada,
  (valor) => {
    if (valor) expandida.value = true
  },
)
</script>

<template>
  <article :id="id" class="fonte" :class="{ 'fonte--destacada': destacada }" tabindex="-1">
    <div class="fonte__numero" aria-hidden="true">
      <span class="rotulo">Art.</span>
      <span class="fonte__digitos">{{ numero }}</span>
    </div>

    <div class="fonte__corpo">
      <h3 class="visualmente-oculto">Artigo {{ fonte.artigo ?? 'sem número' }}</h3>
      <p v-if="caminho.length" class="rotulo fonte__caminho">
        <template v-for="(parte, indice) in caminho" :key="parte">
          <span>{{ parte }}</span>
          <span v-if="indice < caminho.length - 1" class="fonte__separador" aria-hidden="true">/</span>
        </template>
      </p>

      <p class="fonte__trecho" :class="{ 'fonte__trecho--recolhido': longo && !expandida }">
        {{ trecho }}
      </p>

      <button
        v-if="longo"
        type="button"
        class="fonte__alternar rotulo"
        :aria-expanded="expandida"
        @click="expandida = !expandida"
      >
        {{ expandida ? 'Recolher' : 'Ler artigo completo' }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.fonte {
  display: grid;
  grid-template-columns: 5.5rem minmax(0, 1fr);
  gap: 1.25rem;
  padding: 1.5rem 0;
  border-top: 1px solid var(--linha);
  scroll-margin-top: 2rem;
  transition: background-color 600ms var(--curva);
}

.fonte:focus {
  outline: none;
}

.fonte--destacada {
  animation: destacar 2.4s var(--curva);
}

@keyframes destacar {
  0%,
  40% {
    background: var(--acento-suave);
    box-shadow: -1rem 0 0 var(--acento-suave), 1rem 0 0 var(--acento-suave);
  }
  100% {
    background: transparent;
    box-shadow: none;
  }
}

.fonte__numero {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.fonte__digitos {
  font-family: var(--fonte-serifa);
  font-size: 2.5rem;
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: lining-nums;
}

.fonte--destacada .fonte__digitos {
  color: var(--acento);
}

.fonte__caminho {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.5rem;
  margin-bottom: 0.625rem;
  line-height: 1.5;
}

.fonte__separador {
  color: var(--linha);
}

.fonte__trecho {
  font-family: var(--fonte-serifa);
  font-size: 1.0625rem;
  line-height: 1.6;
  color: var(--tinta-2);
  white-space: pre-line;
}

.fonte__trecho--recolhido {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.fonte__alternar {
  margin-top: 0.75rem;
  padding: 0;
  border: 0;
  background: none;
  color: var(--tinta);
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-color: var(--linha);
}

.fonte__alternar:hover {
  text-decoration-color: var(--acento);
}

@media (max-width: 560px) {
  .fonte {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.5rem;
  }

  .fonte__numero {
    flex-direction: row;
    align-items: baseline;
    gap: 0.5rem;
  }

  .fonte__digitos {
    font-size: 1.75rem;
  }
}
</style>

