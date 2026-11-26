import { useEffect, useState } from "react";
import { Flame, LogOut, Menu, X, Bell, ChevronRight } from "lucide-react";
import { api, getToken, setToken, type User } from "../shared/api/client";
import type { Tab } from "../shared/types/navigation";
import { navigation, roleName } from "./navigation";
import LoginPage from "../features/auth/pages/LoginPage";
import DashboardPage from "../features/dashboard/pages/DashboardPage";
import MaterialsPage from "../features/materials/pages/MaterialsPage";
import SuppliersPage from "../features/suppliers/pages/SuppliersPage";
import BatchesPage from "../features/batches/pages/BatchesPage";
import RecipesPage from "../features/recipes/pages/RecipesPage";
import ProductionPage from "../features/production/pages/ProductionPage";
import AssistantPage from "../features/assistant/pages/AssistantPage";

function App() {
  const [tokenReady, setTokenReady] = useState(false),
    [user, setUser] = useState<User | null>(null),
    [tab, setTab] = useState<Tab>("overview"),
    [mobile, setMobile] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setTokenReady(true);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setTokenReady(true));
  }, []);
  const logout = () => {
    setToken(null);
    setUser(null);
  };
  if (!tokenReady)
    return (
      <div className="loading-screen">
        <div className="brand-mark">
          <Flame />
        </div>
        <span>Загружаем CandleFlow</span>
      </div>
    );
  if (!user)
    return <LoginPage onLogin={setUser} onError={setError} error={error} />;
  const page =
    tab === "overview" ? (
      <DashboardPage onNavigate={setTab} />
    ) : tab === "materials" ? (
      <MaterialsPage />
    ) : tab === "suppliers" ? (
      <SuppliersPage />
    ) : tab === "batches" ? (
      <BatchesPage />
    ) : tab === "recipes" ? (
      <RecipesPage />
    ) : tab === "production" ? (
      <ProductionPage />
    ) : (
      <AssistantPage />
    );
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <Flame size={21} />
          </div>
          <div>
            <b>CandleFlow</b>
            <small>AI WORKSPACE</small>
          </div>
          <button className="mobile-close" onClick={() => setMobile(false)}>
            <X />
          </button>
        </div>
        <div className="workspace-label">РАБОЧЕЕ ПРОСТРАНСТВО</div>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => {
                setTab(item.id);
                setMobile(false);
              }}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {item.id === "assistant" && <i className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="status-card">
            <span className="status-pulse" />
            <div>
              <b>Система активна</b>
              <small>API подключение</small>
            </div>
          </div>
          <div className="profile">
            <div className="avatar">
              {user.full_name.slice(0, 1).toUpperCase()}
            </div>
            <div className="profile-info">
              <b>{user.full_name}</b>
              <small>{roleName(user.role)}</small>
            </div>
            <button title="Выйти" onClick={logout}>
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      {mobile && <div className="scrim" onClick={() => setMobile(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobile(true)}>
            <Menu />
          </button>
          <div className="breadcrumb">
            Рабочее пространство <ChevronRight size={14} />{" "}
            <b>{navigation.find((item) => item.id === tab)?.label}</b>
          </div>
          <div className="top-actions">
            <span className="today">
              {new Date().toLocaleDateString("ru-RU", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </span>
            <button className="icon-button" title="Уведомления">
              <Bell size={18} />
              <i />
            </button>
            <div className="top-avatar">
              {user.full_name.slice(0, 1).toUpperCase()}
            </div>
          </div>
        </header>
        <div className="page-wrap">{page}</div>
      </main>
    </div>
  );
}
export default App;
