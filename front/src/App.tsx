import { useCallback, useState } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import SearchBar from "./components/SearchBar";
import { NotificationProvider } from "./components/Notification";
import justiceScales from "./assets/justice-scales.png";

function isMobileViewport(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(max-width: 768px)").matches;
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(() => !isMobileViewport());

  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen((current) => !current);
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  return (
    <NotificationProvider>
      <div className="app-shell">
        <Header sidebarOpen={sidebarOpen} onToggleSidebar={handleToggleSidebar} />

        <div className="app-body">
          <Sidebar open={sidebarOpen} onClose={handleCloseSidebar} />

          <main className="main-area" id="conteudo-principal">
            <div className="hero">
              <img className="justice-scales" src={justiceScales} alt="" />
              <SearchBar />
            </div>
          </main>
        </div>
      </div>
    </NotificationProvider>
  );
}
