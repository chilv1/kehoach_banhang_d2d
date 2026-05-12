import { useState } from "react";
import { indentTask, outdentTask } from "@/api/client";
import type { Dependency, Task } from "@/types";

interface Props {
  tasks: Task[];
  deps: Dependency[];
  onUpdate: (id: number, data: Partial<Task>) => void;
  onDelete: (id: number) => void;
  onAddDep: (predId: number, succId: number) => Promise<unknown>;
  onRefresh?: () => void;
}

const fmt = (s: string | null) =>
  s ? new Date(s).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" }) : "—";

function predecessorsLabel(t: Task, deps: Dependency[], all: Task[]): string {
  const preds = deps.filter((d) => d.successor_id === t.id);
  if (preds.length === 0) return "";
  const names: Record<number, string> = Object.fromEntries(all.map((x) => [x.id, x.name]));
  return preds.map((d) => {
    const lag = d.lag_hours === 0 ? "" : ` ${d.lag_hours > 0 ? "+" : ""}${d.lag_hours}h`;
    return `${d.predecessor_id} (${names[d.predecessor_id]?.slice(0, 20) ?? "?"}) ${d.link_type}${lag}`;
  }).join(", ");
}

export default function TaskGrid({ tasks, deps, onUpdate, onDelete, onAddDep, onRefresh }: Props) {
  const [editing, setEditing] = useState<{ id: number; field: string } | null>(null);
  const [draft, setDraft] = useState("");
  const [predDialog, setPredDialog] = useState<{ tid: number; value: string } | null>(null);

  const doIndent = async (id: number) => {
    try { await indentTask(id); onRefresh?.(); }
    catch (e: any) { alert(e?.response?.data?.detail || e.message); }
  };
  const doOutdent = async (id: number) => {
    try { await outdentTask(id); onRefresh?.(); }
    catch (e: any) { alert(e?.response?.data?.detail || e.message); }
  };
  const handleStartEdit = (t: Task, field: string, current: string) => {
    setEditing({ id: t.id, field }); setDraft(current);
  };
  const handleSaveEdit = () => {
    if (!editing) return;
    const patch: Record<string, any> = {};
    if (editing.field === "name") patch.name = draft;
    if (editing.field === "duration_hours") patch.duration_hours = parseFloat(draft) || 0;
    if (editing.field === "percent_complete") patch.percent_complete = Math.min(100, Math.max(0, parseFloat(draft) || 0));
    onUpdate(editing.id, patch); setEditing(null);
  };
  return (
    <div style={{ overflow: "auto", maxHeight: 700 }}>
      <table>
        <thead>
          <tr><th style={{ width: 40 }}>ID</th><th style={{ width: 280 }}>Name</th><th>Dur (h)</th>
              <th>Start</th><th>Finish</th><th>Slack</th><th>%</th>
              <th>Predecessors</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id} className={[t.is_critical ? "critical" : "", t.is_milestone ? "milestone" : ""].join(" ")}>
              <td>{t.id}</td>
              <td onDoubleClick={() => handleStartEdit(t, "name", t.name)}>
                {editing?.id === t.id && editing.field === "name" ? (
                  <input autoFocus value={draft} onChange={(e) => setDraft(e.target.value)}
                    onBlur={handleSaveEdit} onKeyDown={(e) => e.key === "Enter" && handleSaveEdit()} />
                ) : (
                  <span style={{ paddingLeft: (t.outline_level - 1) * 12 }}>
                    {t.is_milestone ? "◆ " : ""}{t.name}
                  </span>
                )}
              </td>
              <td onDoubleClick={() => handleStartEdit(t, "duration_hours", String(t.duration_hours))}>
                {editing?.id === t.id && editing.field === "duration_hours" ? (
                  <input type="number" autoFocus value={draft}
                    onChange={(e) => setDraft(e.target.value)} onBlur={handleSaveEdit}
                    onKeyDown={(e) => e.key === "Enter" && handleSaveEdit()} style={{ width: 60 }} />
                ) : t.duration_hours}
              </td>
              <td>{fmt(t.start_date)}</td><td>{fmt(t.finish_date)}</td>
              <td style={{ color: t.is_critical ? "#dc2626" : "#6b7280" }}>{t.total_slack_hours.toFixed(1)}h</td>
              <td onDoubleClick={() => handleStartEdit(t, "percent_complete", String(t.percent_complete))}>
                {editing?.id === t.id && editing.field === "percent_complete" ? (
                  <input type="number" autoFocus value={draft}
                    onChange={(e) => setDraft(e.target.value)} onBlur={handleSaveEdit}
                    onKeyDown={(e) => e.key === "Enter" && handleSaveEdit()} style={{ width: 50 }} />
                ) : `${t.percent_complete.toFixed(0)}%`}
              </td>
              <td style={{ fontSize: 11, maxWidth: 280 }}>
                {predecessorsLabel(t, deps, tasks) || (
                  <button onClick={() => setPredDialog({ tid: t.id, value: "" })}>+ link</button>
                )}
              </td>
              <td>{t.is_critical ? (<span className="badge b-crit">CRITICAL</span>) : (<span className="badge b-ok">OK</span>)}</td>
              <td style={{ whiteSpace: "nowrap" }}>
                <button onClick={() => doOutdent(t.id)} title="Outdent">⇦</button>
                <button onClick={() => doIndent(t.id)} title="Indent">⇨</button>
                <button className="danger" onClick={() => onDelete(t.id)}>🗑</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {predDialog && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center",
          justifyContent: "center", zIndex: 100 }}>
          <div className="card" style={{ padding: 20, minWidth: 360 }}>
            <h3 style={{ marginTop: 0 }}>Add predecessor for task #{predDialog.tid}</h3>
            <input autoFocus placeholder="Predecessor task ID" value={predDialog.value}
              onChange={(e) => setPredDialog({ ...predDialog, value: e.target.value })}
              style={{ width: "100%", padding: 8 }} />
            <div style={{ marginTop: 12, display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button onClick={() => setPredDialog(null)}>Cancel</button>
              <button className="primary" onClick={async () => {
                const predId = parseInt(predDialog.value, 10);
                if (predId) await onAddDep(predId, predDialog.tid);
                setPredDialog(null);
              }}>Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
