export interface ConsultaFonte {
  documento: string;
  artigo?: string | null;
  trecho?: string | null;
}

export interface ConsultaResponse {
  resposta: string;
  fontes: ConsultaFonte[];
}

interface ApiError {
  detail?: unknown;
  message?: unknown;
}

const API_URL = (
  import.meta.env.VITE_API_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const CONSULTA_ENDPOINT = "/api/v1/consultas";

// =========================================================
// TRATAMENTO DE ERROS DA API
// =========================================================

function extrairMensagemErro(dados: ApiError | null, status: number): string {
  if (dados && typeof dados.detail === "string" && dados.detail.trim()) {
    return dados.detail;
  }

  if (dados && typeof dados.message === "string" && dados.message.trim()) {
    return dados.message;
  }

  if (status === 400) {
    return "A pergunta enviada é inválida.";
  }

  if (status === 404) {
    return "O serviço de consultas não foi encontrado.";
  }

  if (status === 422) {
    return "A pergunta não foi aceita pelo servidor.";
  }

  if (status === 429) {
    return "Limite de requisições atingido. Tente novamente mais tarde.";
  }

  if (status >= 500) {
    return "O servidor encontrou um erro ao processar a consulta.";
  }

  return `Erro HTTP ${status} ao consultar o assistente.`;
}

// =========================================================
// CONSULTA AO ASSISTENTE JURIDICO RAG
// =========================================================

export async function consultarRAG(
  pergunta: string,
): Promise<ConsultaResponse> {
  const perguntaTratada = pergunta.trim();

  if (!perguntaTratada) {
    throw new Error("A pergunta não pode estar vazia.");
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${CONSULTA_ENDPOINT}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        pergunta: perguntaTratada,
      }),
    });
  } catch (error) {
    console.error("Falha na comunicação com a API:", error);

    throw new Error(
      "Não foi possível conectar ao servidor. Verifique se o backend está em execução.",
    );
  }

  // =========================================================
  // VERIFICACAO DO STATUS HTTP
  // =========================================================

  if (!response.ok) {
    const dados = (await response.json().catch(() => null)) as ApiError | null;

    throw new Error(extrairMensagemErro(dados, response.status));
  }

  // =========================================================
  // VALIDACAO DA RESPOSTA
  // =========================================================

  let dados: unknown;

  try {
    dados = await response.json();
  } catch {
    throw new Error("O servidor retornou uma resposta JSON inválida.");
  }

  if (
    typeof dados !== "object" ||
    dados === null ||
    !("resposta" in dados) ||
    typeof dados.resposta !== "string" ||
    !dados.resposta.trim()
  ) {
    throw new Error("O servidor retornou uma resposta vazia ou inválida.");
  }

  // Preserva o campo fontes quando fornecido pela API.
  const fontes =
    "fontes" in dados && Array.isArray(dados.fontes)
      ? dados.fontes
          .filter(
            (fonte): fonte is ConsultaFonte =>
              typeof fonte === "object" &&
              fonte !== null &&
              "documento" in fonte &&
              typeof fonte.documento === "string",
          )
          .map((fonte) => ({
            documento: fonte.documento,
            artigo: typeof fonte.artigo === "string" ? fonte.artigo : null,
            trecho: typeof fonte.trecho === "string" ? fonte.trecho : null,
          }))
      : [];

  return {
    resposta: dados.resposta,
    fontes,
  };
}
