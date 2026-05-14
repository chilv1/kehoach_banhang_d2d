import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ViewMode } from "gantt-task-react";
import {
  aiApply, exportExcelUrl, getGantt, listCampaigns, uploadExcel,
} from "@/api/sales-client";
import type { AIPlanResponse, SalesTask } from "@/lib/ai-schema";
import AICommandBar from "@/components/AICommandBar/AICommandBar";
import SalesFilterBar, { type FilterState } from "@/components/SalesFilterBar/SalesFilterBar";
import SalesGantt from "@/components/SalesGantt/SalesGantt";

const DEFAULT_FILTER: FilterState = {
  br: [], bc: [], distrito: [], tipo: [], status: [], priority: [],
  grouping: "flat",
};

type LeftNav = "gantt" | "calendar" | "map" | "dashboard" | "resources" | "kpi" | "budget" | "risk";

export default function SalesPlannerPage() {
  const qc = useQueryClient();
  const [campaignId, setCampaignId] = useState<number | null>(null);
  const [view, setView] = useState<ViewMode>(ViewMode.Day);
  const [filter, setFilter] = useState<FilterState>(DEFAULT_FILTER);
  const [leftNav, setLeftNav] = useState<LeftNav>("gantt");
  const [aiResult, setAIResult] = useState<AIPlanResponse | null>(null);

  const campaigns = useQuery({ queryKey: ["sales-campaigns"], queryFn: listCampaigns });
  useEffect(() => {
    if (campaigns.data?.length && campaignId == null) setCampaignId(campaigns.data[0].id);
  }, [campaigns.data, campaignId]);

  const gantt = useQuery({
    enabled: campaignId != null,
    queryKey: ["sales-gantt", campaignId],
    queryFn: () => getGantt(campaignId!),
  });

  const uploadMut = useMutation({
    mutationFn: (f: File) => uploadExcel(f),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-campaigns"] });
      qc.invalidateQueries({ queryKey: ["sales-gantt", campaignId] });
    },
  });

  const applyMut = useMutation({
    mutationFn: (sid: number) => aiApply(sid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-gantt", campaignId] });
      qc.invalidateQueries({ queryKey: ["sales-campaigns"] });
      setAIResult(null);
    },
  });

  const filteredTasks: SalesTask[] = useMemo(() => {
    const tasks = gantt.data?.tasks ?? [];
    return tasks.filter((t) => {
      if (filter.distrito.length && !filter.distrito.includes(t.distrito ?? "")) return false;
      if (filter.tipo.length && !filter.tipo.includes(t.tipo_df_cp ?? "")) return false;
      if (filter.status.length && !filter.status.includes(t.status)) return false;
      return true;
    });
  }, [gantt.data, filter]);

  const sidebarItems: { id: LeftNav; label: string; emoji: string }[] = [
    { id: "gantt", label: "Gantt", emoji: "📊" },
    { id: "calendar", label: "Calendar", emoji: "🗓️" },
    { id: "map", label: "Map", emoji: "🗺️" },
    { id: "dashboard", label: "Dashboard", emoji: "📈" },
    { id: "resources", label: "Resources", emoji: "🧑" },
    { id: "kpi", label: "KPI", emoji: "🎯" },
    { id: "budget", label: "Budget", emoji: "💰" },
    { id: "risk", label: "Risk", emoji: "⚠️" },
  ];

  return (
    <div className="app" style={{ gridTemplateRows: "48px 1fr" }}>
      <header className="header">
        <h1>🤖 AI Sales Campaign Planner</h1>
        <span style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <select
            value={campaignId ?? ""}
            onChange={(e) => setCampaignId(e.target.value ? Number(e.target.value) : null)}
            style={{ padding: 4, borderRadius: 4 }}
          >
            {campaigns.data?.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <label style={{ cursor: "pointer", fontSize: 12 }}>
            <input
              type="file"
              accept=".xlsx"
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) uploadMut.mutate(f);
              }}
            />
            <span style={{ background: "#10b981", padding: "4px 10px", borderRadius: 4, color: "white" }}>
              📥 Import Excel
            </span>
          </label>
          {campaignId && (
            <a href={exportExcelUrl(campaignId)} download style={{ color: "white", fontSize: 12 }}>
              📤 Export Excel
            </a>
          )}
        </span>
      </header>
      <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", height: "100%", overflow: "hidden" }}>
        {/* Left sidebar */}
        <aside style={{ background: "#1e293b", color: "white", padding: 8 }}>
          {sidebarItems.map((s) => (
            <button
              key={s.id}
              onClick={() => setLeftNav(s.id)}
              style={{
                width: "100%", textAlign: "left", padding: "8px 12px", margin: "2px 0",
                background: leftNav === s.id ? "#0e2a52" : "transparent",
                color: "white", border: "none", borderRadius: 4, cursor: "pointer",
                fontSize: 13,
              }}
            >
              <span style={{ marginRight: 6 }}>{s.emoji}</span>{s.label}
            </button>
          ))}
        </aside>

        {/* Main */}
        <main style={{ display: "grid", gridTemplateRows: "auto auto auto 1fr", overflow: "hidden" }}>
          <AICommandBar campaignId={campaignId ?? undefined} onResult={setAIResult} />
          <SalesFilterBar tasks={gantt.data?.tasks ?? []} value={filter} onChange={setFilter} />
          {leftNav === "gantt" && (
            <div style={{ padding: "6px 12px", display: "flex", gap: 6, borderBottom: "1px solid #e5e7eb", background: "#fafafa" }}>
              <button onClick={() => setView(ViewMode.Hour)}>Hour</button>
              <button onClick={() => setView(ViewMode.Day)}>Day</button>
              <button onClick={() => setView(ViewMode.Week)}>Week</button>
              <button onClick={() => setView(ViewMode.Month)}>Month</button>
              <span style={{ marginLeft: "auto", fontSize: 12, color: "#6b7280", lineHeight: "28px" }}>
                {filteredTasks.length} task — Gantt sẽ chuyển sang custom Canvas/SVG ở Phase 2
              </span>
            </div>
          )}
          <div style={{ overflow: "auto", position: "relative" }}>
            {leftNav === "gantt" && (
              <SalesGantt
                tasks={filteredTasks}
                view={view}
                onTasksChanged={() => qc.invalidateQueries({ queryKey: ["sales-gantt", campaignId] })}
              />
            )}
            {leftNav !== "gantt" && (
              <div style={{ padding: 32, color: "#6b7280" }}>
                <h3>{sidebarItems.find((s) => s.id === leftNav)?.label} view</h3>
                <p>Phase {leftNav === "dashboard" || leftNav === "map" ? "1" : "2+"} — implementation in progress.</p>
              </div>
            )}
            {aiResult && (
              <AIResultDrawer
                resp={aiResult}
                onApply={() => applyMut.mutate(aiResult.session_id)}
                onClose={() => setAIResult(null)}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function AIResultDrawer({
  resp, onApply, onClose,
}: { resp: AIPlanResponse; onApply: () => void; onClose: () => void }) {
  return (
    <div style={{
      position: "absolute", top: 0, right: 0, width: 420, height: "100%",
      background: "white", borderLeft: "1px solid #e5e7eb",
      boxShadow: "-4px 0 12px rgba(0,0,0,0.05)", padding: 16, overflowY: "auto",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <strong>🤖 AI plan (session {resp.session_id})</strong>
        <button onClick={onClose}>✕</button>
      </div>
      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 8 }}>
        provider={resp.provider} · {resp.duration_ms}ms · {resp.campaign_plan.length} tasks
      </div>
      <div style={{ background: "#f8fafc", padding: 8, borderRadius: 4, fontSize: 12 }}>
        {resp.summary}
      </div>
      {resp.warnings.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong style={{ fontSize: 12 }}>⚠️ Warnings ({resp.warnings.length})</strong>
          <ul style={{ fontSize: 11, paddingLeft: 16 }}>
            {resp.warnings.slice(0, 6).map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
      <h4 style={{ marginTop: 12 }}>Plan preview</h4>
      <table style={{ fontSize: 11, width: "100%" }}>
        <thead style={{ background: "#f1f5f9" }}>
          <tr><th align="left">Task</th><th>Start</th><th>End</th><th>Prio</th></tr>
        </thead>
        <tbody>
          {resp.campaign_plan.slice(0, 12).map((p, i) => (
            <tr key={i}>
              <td>{p.task_name}</td>
              <td>{p.start_date}</td>
              <td>{p.end_date}</td>
              <td style={{ textAlign: "center", color: p.priority === 1 ? "#dc2626" : "#374151" }}>
                {p.priority}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <button className="primary" onClick={onApply}>✅ Apply plan</button>
        <button onClick={onClose}>Discard</button>
      </div>
    </div>
  );
}
