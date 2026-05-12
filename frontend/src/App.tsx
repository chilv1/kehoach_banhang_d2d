import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import ProjectListPage from "@/pages/ProjectListPage";
import ProjectViewPage from "@/pages/ProjectViewPage";
import ResourcesPage from "@/pages/ResourcesPage";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>📊 ProjectWeb — MS Project clone</h1>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Projects</NavLink>
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/:pid" element={<ProjectViewPage />} />
          <Route path="/projects/:pid/resources" element={<ResourcesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
