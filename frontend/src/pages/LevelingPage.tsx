import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getOverallocations, getResourceLoad, levelResources, getProject } from "@/api/client";

export default function LevelingPage() {
  const { pid } = useParams();
  const projectId = Number(pid);
  const qc = useQueryClient();
  const projQ = useQuery({ queryKey: ["project", projectId], queryFn: () => getProject(projectId) });
  const overQ = useQuery({
    queryKey: ["over", projectId],
    queryFn: () => getOverallocations(projectId),
  });
  const loadQ = useQuery({
    queryKey: ["resload", projectId],
    queryFn: () => getResourceLoad(projectId),
  });
  const levelMut = useMutation({
    mutationFn: () => levelResources(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["over", projectId] });
      qc.invalidateQueries({ queryKey: ["resload", projectId] });
      qc.invalidateQueries({ queryKey: ["tasks", projectId] });
    },
  });

  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}>
        <Link to={`/projects/${projectId}`}>← Project</Link>
      </div>
      <div className="card">
        <div className="toolbar">
          <strong style={{ fontSize: 15 }}>{projQ.data?.name} — Resource Leveling</strong>
          <span style={{ marginLeft: "auto" }}>
            <button className="primary" onClick={() => levelMut.mutate()}
                    disabled={levelMut.isPending}>
              {levelMut.isPending ? "Đang chạy…" : "🛠️ Auto-level"}
            </button>
          </span>
        </div>

        {levelMut.data && (
          <div style={{ padding: 12, background: "#f0fdf4", borderBottom: "1px solid #e5e7eb" }}>
            ✅ Đã chạy {levelMut.data.iterations} iterations, converged: {String(levelMut.data.converged)}, delays: {levelMut.data.delays.length}
          </div>
        )}

        <div style={{ padding: 16 }}>
          <h3>⚠️ Overallocations</h3>
          {(overQ.data?.length ?? 0) === 0 ? (
            <div style={{ color: "#16a34a" }}>✅ Không có overallocation</div>
          ) : (
            <table>
              <thead>
                <tr><th>Resource</th><th>Ngày</th><th>Used</th><th>Max</th><th>Over</th></tr>
              </thead>
              <tbody>
                {overQ.data.map((o: any, i: number) => (
                  <tr key={i} className="critical">
                    <td>{o.resource_name}</td>
                    <td>{o.date}</td>
                    <td>{o.used_units}</td>
                    <td>{o.max_units}</td>
                    <td style={{ color: "#dc2626", fontWeight: 600 }}>+{o.over}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3 style={{ marginTop: 24 }}>📊 Resource daily load (peak)</h3>
          <table>
            <thead><tr><th>Resource ID</th><th>Số ngày làm</th><th>Peak load</th></tr></thead>
            <tbody>
              {Object.entries(loadQ.data ?? {}).map(([rid, days]: any) => {
                const peak = Math.max(0, ...Object.values(days as Record<string, number>));
                const nDays = Object.keys(days as object).length;
                return (
                  <tr key={rid}>
                    <td>{rid}</td>
                    <td>{nDays}</td>
                    <td>{peak.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
