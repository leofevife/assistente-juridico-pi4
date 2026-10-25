import { useState, type FormEvent } from "react";
import { Search } from "lucide-react";
import { useNotification } from "./Notification";

export default function SearchBar() {
  const notify = useNotification();
  const [query, setQuery] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!query.trim()) {
      notify("Digite uma pergunta ou um tema para iniciar a pesquisa.");
      return;
    }

    notify("Funcionalidade em desenvolvimento. A pesquisa jurídica estará disponível em breve.");
  };

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
        />
      </div>

      <button type="submit" className="search-button">
        Pesquisar
      </button>
    </form>
  );
}
