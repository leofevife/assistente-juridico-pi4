<script setup lang="ts">
import { computed } from 'vue'
import type { StatusApi } from '@/composables/useStatusApi'

const props = defineProps<{ status: StatusApi }>()

const textoStatus = computed(() => ({
  verificando: 'Verificando API',
  online: 'API conectada',
  offline: 'API indisponível',
})[props.status])
</script>

<template>
  <header class="cabecalho">
    <div class="marca">
      <span class="marca__nome">Consulta</span>
      <span class="marca__lei rotulo">CDC · Lei nº 8.078/1990</span>
    </div>

    <p class="status" :data-status="status" role="status">
      <span class="status__ponto" aria-hidden="true" />
      <span class="rotulo">{{ textoStatus }}</span>
    </p>
  </header>
</template>

<style scoped>
.cabecalho {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 1.25rem;
  border-bottom: 1px solid var(--linha);
}

.marca {
  display: flex;
  align-items: baseline;
  gap: 0.875rem;
  flex-wrap: wrap;
}

.marca__nome {
  font-family: var(--fonte-serifa);
  font-style: italic;
  font-size: 1.5rem;
  line-height: 1;
  letter-spacing: -0.01em;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.status__ponto {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--tinta-3);
}

.status[data-status='online'] .status__ponto {
  background: var(--sucesso);
}

.status[data-status='offline'] .status__ponto {
  background: var(--acento);
}

.status[data-status='verificando'] .status__ponto {
  animation: piscar 1.2s ease-in-out infinite;
}

@keyframes piscar {
  50% {
    opacity: 0.25;
  }
}
</style>

