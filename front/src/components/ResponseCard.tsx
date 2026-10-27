import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Check, Copy } from "lucide-react";
import "./ResponseCard.css";

interface ResponseCardProps {
  resposta: string;
  tempoResposta: number; // Tempo em segundos
}

function formatarTempo(segundos: number): string {
  if (!Number.isFinite(segundos) || segundos < 0) {
    return "0s";
  }

  if (segundos < 60) {
    return `${Math.max(1, Math.ceil(segundos))}s`;
  }

  const minutos = Math.floor(segundos / 60);
  const segundosRestantes = Math.floor(segundos % 60);

  if (segundosRestantes === 0) {
    return `${minutos}min`;
  }

  return `${minutos}min ${segundosRestantes}s`;
}

export default function ResponseCard({
  resposta,
  tempoResposta,
}: ResponseCardProps) {
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    setCopiado(false);
  }, [resposta]);

  async function copiarResposta() {
    try {
      await navigator.clipboard.writeText(resposta);
      setCopiado(true);
    } catch (error) {
      console.error("Erro ao copiar resposta:", error);
      setCopiado(false);
    }
  }

  if (!resposta.trim()) {
    return null;
  }

  return (
    <section
      className="response-card"
      aria-label="Resposta do Assistente Jurídico"
    >
      <h2 className="response-card__title">Resposta do Assistente Jurídico</h2>

      <div className="response-card__content">
        <ReactMarkdown>{resposta}</ReactMarkdown>
      </div>

      <div className="response-card__actions">
        <span
          className="response-card__time"
          title="Tempo de processamento da consulta"
        >
          {formatarTempo(tempoResposta)}
        </span>

        <button
          type="button"
          className="response-card__copy"
          onClick={copiarResposta}
          title={copiado ? "Resposta copiada" : "Copiar resposta"}
          aria-label={copiado ? "Resposta copiada" : "Copiar resposta"}
        >
          {copiado ? <Check size={18} /> : <Copy size={18} />}
        </button>
      </div>
    </section>
  );
}
