import { Menu, Scale, User, X } from "lucide-react";
import { useNotification } from "./Notification";

type HeaderProps = {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
};

export default function Header({ sidebarOpen, onToggleSidebar }: HeaderProps) {
  const notify = useNotification();

  return (
    <header className="app-header">
      <button
        type="button"
        className="icon-button"
        onClick={onToggleSidebar}
        aria-label={sidebarOpen ? "Recolher menu lateral" : "Abrir menu lateral"}
        aria-expanded={sidebarOpen}
        aria-controls="sidebar-menu"
      >
        {sidebarOpen ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
      </button>

      <div className="brand">
        <Scale size={18} className="brand-mark" aria-hidden="true" />
        <span className="brand-text">
          <span className="brand-name">Assistente Jurídico</span>
          <span className="brand-sub">Código e Defesa do Consumidor</span>
        </span>
      </div>

      <div className="header-actions">
        <button
          type="button"
          className="icon-button"
          onClick={() => notify("O perfil do usuário estará disponível em breve.")}
          aria-label="Abrir perfil do usuário"
        >
          <User size={20} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
