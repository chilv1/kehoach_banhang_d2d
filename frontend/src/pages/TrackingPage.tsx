import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createBaseline, getProject, getVariance, listBaselines } from "@/api/client";

export default function TrackingPage() {
  const { pid } = useParams();
  const projectId = Number(pid);
  const qc = useQueryClient();
  const [number, setNumber] = useState(0);
  const projQ = useQuery({ queryKey: ["project", projectId], queryFn: () => getProject(projectId) });
  const baselinesQ = useQuery({ queryKey: ["baselines", projectId], queryFn: () => listBaselines(projectId) });
  const varianceQ = useQuery({
    queryKey: ["variance", projectId, number],
    queryFn: () => getVariance(projectId, number),
  });
  const createMut = useMutation({
    mutationFn: () => createBaseline({ project_id: projectId, number, name: `Baseline ${number}` }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["baselines", projectId] });
      qc.invalidateQueries({ queryKey: ["variance", projectId, number] });
    },
  });
  const slipping = (varianceQ.data?.tasks ?? []).filter((t: any) => t.is_slipping);
  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}><Link to={`/projects/${projectId}`}>← Project</Link></div>
      <div className="card">
        <div className="toolbar">
          <strong style={{ fontSize: 15 }}>{projQ.data?.name} — Tracking</strong>
          <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
            <label>Baseline #:</label>
            <input type="number" min={0} max={10} value={number}
                    onChange={(e) => setNumber(parseInt(e.target.value))} style={{ width: 60 }} />
            <button className="primary" onClick={() => createMut.mutate()}>📸 Save baseline {number}</button>
          </span>
        </div>
        <div style={{ padding: 16 }}>
          <h3>📚 Baselines</h3>
          {(baselinesQ.data?.length ?? 0) === 0 ? (
            <div style={{ color: "#6b7280" }}>Chưa có baseline. Bấm "Save baseline" để snapshot kế hoạch hiện tại.</div>
          ) : (
            <table><thead><tr><th>#</th><th>Tên</th><th>Snapshot date</th></tr></thead>
              <tbody>{baselinesQ.data.map((b: any) => (
                <tr key={b.id}><td>{b.number}</td><td>{b.name}</td><td>{b.snapshot_date?.slice(0, 19).replace("T", " ")}</td></tr>
              ))}</tbody></table>
          )}
          <h3 style={{ marginTop: 24 }}>📈 Variance vs Baseline #{number}</h3>
          {slipping.length > 0 && (
            <div style={{ background: "#fef2f2", padding: 8, borderRadius: 4, marginBottom: 8 }}>
              ⚠️ {slipping.length} task đang trễ tiến độ
            </div>
          )}
          <table>
            <thead><tr><th>Task</th><th>Baseline start</th><th>Current start</th><th>Baseline finish</th><th>Current finish</th><th>Finish var (h)</th><th>Status</th></tr></thead>
            <tbody>
              {(varianceQ.data?.tasks ?? []).map((t: any) => (
                <tr key={t.task_id} className={t.is_slipping ? "critical" : ""}>
                  <td>{t.name}</td>
                  <td>{t.baseline_start?.slice(0, 16).replace("T", " ") ?? "—"}</td>
                  <td>{t.current_start?.slice(0, 16).replace("T", " ") ?? "—"}</td>
                  <td>{t.baseline_finish?.slice(0, 16).replace("T", " ") ?? "—"}</td>
                  <td>{t.current_finish?.slice(0, 16).replace("T", " ") ?? "—"}</td>
                  <td style={{ color: t.finish_variance_hours > 0 ? "#dc2626" : "#16a34a", fontWeight: 600 }}>
                    {t.finish_variance_hours != null ? t.finish_variance_hours.toFixed(0) : "—"}
                  </td>
                  <td>{t.is_slipping ? <span className="badge b-crit">SLIPPING</span> : <span className="badge b-ok">ON TIME</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
