import { useRef, useState, type FormEvent } from "react";
import { Search } from "lucide-react";
import { useNotification } from "./Notification";
import { consultarRAG, type ConsultaResponse } from "../services/api";

// Propriedades recebidas do App.tsx
interface SearchBarProps {
  onResultado: (resultado: ConsultaResponse, tempoResposta: number) => void;
  onInicioPesquisa: () => void;
  onErro: (mensagem: string) => void;
}

export default function SearchBar({
  onResultado,
  onInicioPesquisa,
  onErro,
}: SearchBarProps) {
  const notify = useNotification();

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // Impede envios simultaneos mesmo antes do React renderizar.
  const enviandoRef = useRef(false);

  // =========================================================
  // ENVIO DA PERGUNTA PARA A FASTAPI
  // =========================================================

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (enviandoRef.current) {
      return;
    }

    const pergunta = query.trim();

    if (!pergunta) {
      notify("Digite uma pergunta para iniciar a pesquisa jurídica.");
      return;
    }

    if (pergunta.length < 5) {
      notify("A pergunta deve conter pelo menos 5 caracteres.");
      return;
    }

    if (pergunta.length > 2000) {
      notify("A pergunta deve conter no máximo 2000 caracteres.");
      return;
    }

    enviandoRef.current = true;
    setLoading(true);

    // Inicia a contagem imediatamente antes da pesquisa.
    const inicio = performance.now();

    try {
      // Limpa a resposta anterior e o erro anterior.
      onInicioPesquisa();

      // Consulta o backend FastAPI.
      const resultado = await consultarRAG(pergunta);

      // Calcula a duracao total da requisicao em segundos.
      const tempoResposta = (performance.now() - inicio) / 1000;

      // Atualiza a resposta no App.tsx.
      onResultado(resultado, tempoResposta);

      // Limpa o campo somente depois do sucesso.
      setQuery("");
    } catch (error) {
      console.error("Erro ao consultar o assistente jurídico:", error);

      const mensagem =
        error instanceof Error
          ? error.message
          : "Erro inesperado ao consultar o assistente.";

      onErro(mensagem);

      notify("Não foi possível concluir a pesquisa jurídica.");

      // Mantem a pergunta para uma nova tentativa.
    } finally {
      enviandoRef.current = false;
      setLoading(false);
    }
  };

  // =========================================================
  // INTERFACE DA BARRA DE PESQUISA
  // =========================================================

  return (
    <form className="search-bar" onSubmit={handleSubmit} role="search">
      <div className="search-field">
        <Search className="search-icon" size={20} aria-hidden="true" />

        <input
          type="text"
          name="pesquisa"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Digite sua pergunta ou o tema que deseja pesquisar..."
          aria-label="Digite sua pergunta ou o tema que deseja pesquisar"
          autoComplete="off"
          disabled={loading}
          maxLength={2000}
        />
      </div>

      <button
        type="submit"
        className="search-button"
        disabled={loading}
        aria-busy={loading}
      >
        {loading ? "Pesquisando..." : "Pesquisar"}
      </button>
    </form>
  );
}
