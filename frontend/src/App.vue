<script setup lang="ts">
import { ref } from 'vue'
import AppCabecalho from '@/components/AppCabecalho.vue'
import ConsultaFormulario from '@/components/ConsultaFormulario.vue'
import RespostaPainel from '@/components/RespostaPainel.vue'
import { useConsulta } from '@/composables/useConsulta'
import { useStatusApi } from '@/composables/useStatusApi'

const EXEMPLOS = [
  'Qual o prazo para desistir de uma compra feita pela internet?',
  'O produto apresentou defeito na garantia. Quais são meus direitos?',
  'Fui cobrado por um valor que não devia. Tenho direito à devolução em dobro?',
  'A loja pode se recusar a trocar um produto com vício oculto?',
]

const pergunta = ref('')
const { status } = useStatusApi()
const { estado, carregando, perguntaEnviada, resultado, erro, duracaoMs, consultar, cancelar } = useConsulta()

function tentarNovamente(): void {
  consultar(perguntaEnviada.value)
}
</script>

<template>
  <div class="pagina">
    <AppCabecalho :status="status" />

    <main class="conteudo">
      <aside class="coluna-consulta">
        <div class="coluna-consulta__fixa">
          <p class="rotulo">Código de Defesa do Consumidor</p>
          <h1 class="titulo">Pergunte à lei, <em>não</em> a um palpite.</h1>
          <p class="subtitulo">
            Cada resposta é construída apenas com os artigos do CDC recuperados para a sua dúvida, e as fontes
            ficam logo abaixo para você conferir.
          </p>

          <ConsultaFormulario
            v-model="pergunta"
            :carregando="carregando"
            :exemplos="EXEMPLOS"
            @enviar="consultar"
            @cancelar="cancelar"
          />
        </div>
      </aside>

      <div class="coluna-resposta">
        <RespostaPainel
          :estado="estado"
          :pergunta="perguntaEnviada"
          :resultado="resultado"
          :erro="erro"
          :duracao-ms="duracaoMs"
          @tentar-novamente="tentarNovamente"
        />
      </div>
    </main>

    <footer class="rodape">
      <p class="rotulo">Conteúdo informativo. Não substitui a orientação de um advogado ou do Procon.</p>
      <p class="rotulo">Projeto Integrador 4 · FAESA</p>
    </footer>
  </div>
</template>

<style scoped>
.pagina {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  max-width: var(--largura-max);
  margin: 0 auto;
  padding-inline: var(--margem);
}

.conteudo {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
}

.coluna-consulta {
  padding: clamp(2rem, 5vw, 4rem) clamp(2rem, 4vw, 4rem) 3rem 0;
}

.coluna-consulta__fixa {
  position: sticky;
  top: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.titulo {
  font-family: var(--fonte-serifa);
  font-weight: 400;
  font-size: clamp(2.25rem, 4.2vw, 3.5rem);
  line-height: 1.02;
  letter-spacing: -0.025em;
  text-wrap: balance;
}

.titulo em {
  color: var(--acento);
}

.subtitulo {
  max-width: 34rem;
  margin-bottom: 1rem;
  color: var(--tinta-2);
  text-wrap: pretty;
}

.coluna-resposta {
  padding: clamp(2rem, 5vw, 4rem) 0 4rem clamp(2rem, 4vw, 4rem);
  border-left: 1px solid var(--linha);
}

.rodape {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem 2rem;
  padding-block: 1.25rem;
  border-top: 1px solid var(--linha);
}

@media (max-width: 960px) {
  .conteudo {
    grid-template-columns: minmax(0, 1fr);
  }

  .coluna-consulta {
    padding-right: 0;
  }

  .coluna-consulta__fixa {
    position: static;
  }

  .coluna-resposta {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid var(--linha);
  }
}
</style>

