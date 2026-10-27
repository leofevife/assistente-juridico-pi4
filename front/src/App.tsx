import { useCallback, useState } from "react";

import Header from "./components/Header";
// import Sidebar from "./components/Sidebar";
import SearchBar from "./components/SearchBar";
import ResponseCard from "./components/ResponseCard";

import { NotificationProvider } from "./components/Notification";

import type { ConsultaResponse } from "./services/api";

import justiceScales from "./assets/justice-scales.png";

// ============================================================
// VERIFICACAO DE DISPOSITIVO MOVEL
// ============================================================

/*
function isMobileViewport(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(max-width: 768px)").matches
  );
}
*/

// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

export default function App() {
  // Controle do menu lateral temporariamente desativado
  // const [sidebarOpen, setSidebarOpen] = useState(() => !isMobileViewport());

  // Resultado retornado pelo RAG
  const [resultado, setResultado] = useState<ConsultaResponse | null>(null);

  // Tempo da consulta em segundos
  const [tempoResposta, setTempoResposta] = useState(0);

  // Mensagem de erro
  const [erro, setErro] = useState<string | null>(null);

  // ==========================================================
  // CONTROLE DO MENU LATERAL
  // ==========================================================

  /*
  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen((current) => !current);
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);
  */

  // ==========================================================
  // CONTROLE DA PESQUISA
  // ==========================================================

  const handleInicioPesquisa = useCallback(() => {
    setResultado(null);
    setTempoResposta(0);
    setErro(null);
  }, []);

  const handleResultado = useCallback(
    (dados: ConsultaResponse, tempo: number) => {
      setResultado(dados);
      setTempoResposta(tempo);
      setErro(null);
    },
    [],
  );

  const handleErro = useCallback((mensagem: string) => {
    setResultado(null);
    setTempoResposta(0);
    setErro(mensagem);
  }, []);

  // ==========================================================
  // INTERFACE PRINCIPAL
  // ==========================================================

  return (
    <NotificationProvider>
      <div className="app-shell">
        {/* CABECALHO */}
        <Header sidebarOpen={false} onToggleSidebar={() => {}} />

        <div className="app-body">
          {/* MENU LATERAL TEMPORARIAMENTE DESATIVADO */}
          {/*
          <Sidebar
            open={sidebarOpen}
            onClose={handleCloseSidebar}
          />
          */}

          <main className="main-area" id="conteudo-principal">
            <div className="hero">
              {/* IMAGEM ORIGINAL DA BALANCA */}
              <img className="justice-scales" src={justiceScales} alt="" />

              {/* BARRA DE PESQUISA */}
              <SearchBar
                onInicioPesquisa={handleInicioPesquisa}
                onResultado={handleResultado}
                onErro={handleErro}
              />

              {/* MENSAGEM DE ERRO */}
              {erro && (
                <section
                  className="rag-error"
                  role="alert"
                  style={{
                    width: "min(100%, 760px)",
                    marginTop: "24px",
                    padding: "20px",
                    backgroundColor: "#2B1820",
                    border: "1px solid #B45353",
                    borderRadius: "12px",
                    color: "#F5F7FA",
                  }}
                >
                  <strong>Erro na pesquisa</strong>
                  <p>{erro}</p>
                </section>
              )}

              {/* RESPOSTA DO ASSISTENTE */}
              {resultado && (
                <div
                  className="rag-result"
                  aria-live="polite"
                  style={{
                    width: "min(100%, 760px)",
                    marginTop: "24px",
                    textAlign: "left",
                  }}
                >
                  <ResponseCard
                    resposta={resultado.resposta}
                    tempoResposta={tempoResposta}
                  />

                  {/* FONTES JURIDICAS */}
                  {resultado.fontes?.length > 0 && (
                    <section
                      className="rag-sources"
                      aria-label="Fontes jurídicas consultadas"
                    >
                      <h3>Fontes consultadas</h3>

                      {resultado.fontes.map((fonte, index) => (
                        <div
                          className="rag-source"
                          key={`${fonte.documento}-${fonte.artigo ?? ""}-${index}`}
                        >
                          <strong>{fonte.documento}</strong>

                          {fonte.artigo && <p>Artigo: {fonte.artigo}</p>}

                          {fonte.trecho && (
                            <p className="rag-source__excerpt">
                              {fonte.trecho}
                            </p>
                          )}
                        </div>
                      ))}
                    </section>
                  )}

                  {/* AVISO LEGAL */}
                  <p className="rag-disclaimer">
                    Resposta informativa baseada no Código de Defesa do
                    Consumidor. Não substitui orientação jurídica profissional.
                  </p>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </NotificationProvider>
  );
}
