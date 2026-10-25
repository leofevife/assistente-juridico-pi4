import { useEffect } from "react";
import {
  BookOpen,
  History,
  House,
  Info,
  Search,
  Star,
  type LucideIcon,
} from "lucide-react";
import { useNotification } from "./Notification";

type MenuItem = {
  id: string;
  label: string;
  icon: LucideIcon;
  message?: string;
};

const MENU_ITEMS: MenuItem[] = [
  { id: "inicio", label: "Início", icon: House },
  {
    id: "nova-pesquisa",
    label: "Nova pesquisa",
    icon: Search,
    message: "A funcionalidade Nova pesquisa está em desenvolvimento.",
  },
  {
    id: "historico",
    label: "Histórico",
    icon: History,
    message: "O histórico de pesquisas estará disponível em breve.",
  },
  {
    id: "favoritos",
    label: "Favoritos",
    icon: Star,
    message: "A funcionalidade de favoritos está em desenvolvimento.",
  },
  {
    id: "legislacao",
    label: "Legislação",
    icon: BookOpen,
    message: "A consulta à legislação estará disponível em breve.",
  },
  {
    id: "sobre",
    label: "Sobre o projeto",
    icon: Info,
    message: "Esta seção está em desenvolvimento.",
  },
];

const ACTIVE_ITEM_ID = "inicio";

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

function isMobile(): boolean {
  return window.matchMedia("(max-width: 768px)").matches;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const notify = useNotification();

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  const handleItemClick = (item: MenuItem) => {
    const isActive = item.id === ACTIVE_ITEM_ID;

    if (!isActive && item.message) {
      notify(item.message);
    }

    if (isMobile()) {
      onClose();
    }
  };

  return (
    <>
      <aside
        id="sidebar-menu"
        className={`sidebar ${open ? "is-open" : "is-collapsed"}`}
        inert={!open}
      >
        <div className="sidebar-inner">
          <p className="sidebar-label" id="sidebar-label-menu">
            Menu
          </p>
          <nav aria-labelledby="sidebar-label-menu">
            <ul className="sidebar-list">
              {MENU_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = item.id === ACTIVE_ITEM_ID;

                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`menu-item${isActive ? " is-active" : ""}`}
                      onClick={() => handleItemClick(item)}
                      aria-current={isActive ? "page" : undefined}
                      tabIndex={open ? 0 : -1}
                    >
                      <Icon size={18} aria-hidden={true} />
                      <span>{item.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </aside>

      {open && (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={onClose}
          aria-label="Fechar menu lateral"
          tabIndex={-1}
        />
      )}
    </>
  );
}
