import { NavLink, Route, Routes, Navigate, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import ProjectListPage from "@/pages/ProjectListPage";
import ProjectViewPage from "@/pages/ProjectViewPage";
import ResourcesPage from "@/pages/ResourcesPage";
import LoginPage from "@/pages/LoginPage";
import EvmPage from "@/pages/EvmPage";
import LevelingPage from "@/pages/LevelingPage";
import TrackingPage from "@/pages/TrackingPage";
import SalesPlannerPage from "@/pages/SalesPlannerPage";

function AuthGuard({ children }: { children: React.ReactNode }) {
  const nav = useNavigate();
  useEffect(() => {
    if (!localStorage.getItem("token")) nav("/login");
  }, []);
  return <>{children}</>;
}

export default function App() {
  const user = (() => {
    try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
  })();
  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };
  return (
    <div className="app">
      <header className="header">
        <h1>📊 ProjectWeb — MS Project clone</h1>
        <nav style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Projects</NavLink>
          <NavLink to="/sales-planner" className={({ isActive }) => (isActive ? "active" : "")}>🤖 Sales Planner</NavLink>
          {user ? (
            <>
              <span style={{ color: "#cbd5e1", fontSize: 12 }}>👤 {user.username}</span>
              <a href="#" onClick={(e) => { e.preventDefault(); logout(); }} style={{ color: "#fca5a5" }}>Logout</a>
            </>
          ) : (
            <NavLink to="/login" className={({ isActive }) => (isActive ? "active" : "")}>Login</NavLink>
          )}
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<AuthGuard><ProjectListPage /></AuthGuard>} />
          <Route path="/projects/:pid" element={<AuthGuard><ProjectViewPage /></AuthGuard>} />
          <Route path="/projects/:pid/resources" element={<AuthGuard><ResourcesPage /></AuthGuard>} />
          <Route path="/projects/:pid/tracking" element={<AuthGuard><TrackingPage /></AuthGuard>} />
          <Route path="/projects/:pid/leveling" element={<AuthGuard><LevelingPage /></AuthGuard>} />
          <Route path="/projects/:pid/evm" element={<AuthGuard><EvmPage /></AuthGuard>} />
          <Route path="/sales-planner" element={<AuthGuard><SalesPlannerPage /></AuthGuard>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
