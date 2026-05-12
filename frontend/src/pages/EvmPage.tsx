import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getEvm, getProject } from "@/api/client";

const fmtMoney = (v: number | null | undefined) =>
  v == null ? "—" : `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const fmtIdx = (v: number | null | undefined) => v == null ? "—" : v.toFixed(2);

function indexColor(v: number | null | undefined) {
  if (v == null) return "#6b7280";
  if (v >= 1.0) return "#16a34a";
  if (v >= 0.9) return "#ca8a04";
  return "#dc2626";
}

export default function EvmPage() {
  const { pid } = useParams();
  const projectId = Number(pid);
  const [statusDate, setStatusDate] = useState(new Date().toISOString().slice(0, 10));
  const projQ = useQuery({ queryKey: ["project", projectId], queryFn: () => getProject(projectId) });
  const evmQ = useQuery({
    queryKey: ["evm", projectId, statusDate],
    queryFn: () => getEvm(projectId, statusDate + "T23:59:59"),
  });
  const d = evmQ.data;
  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}><Link to={`/projects/${projectId}`}>← Project</Link></div>
      <div className="card">
        <div className="toolbar">
          <strong style={{ fontSize: 15 }}>{projQ.data?.name} — EVM (Earned Value)</strong>
          <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
            <label>Status date:</label>
            <input type="date" value={statusDate} onChange={(e) => setStatusDate(e.target.value)} />
          </span>
        </div>
        {evmQ.isLoading && <div style={{ padding: 16 }}>Loading…</div>}
        {d && (
          <div style={{ padding: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <Box label="BAC" value={fmtMoney(d.bac)} />
              <Box label="BCWS" value={fmtMoney(d.bcws)} />
              <Box label="BCWP" value={fmtMoney(d.bcwp)} />
              <Box label="ACWP" value={fmtMoney(d.acwp)} />
              <Box label="CV" value={fmtMoney(d.cv)} color={d.cv >= 0 ? "#16a34a" : "#dc2626"} />
              <Box label="SV" value={fmtMoney(d.sv)} color={d.sv >= 0 ? "#16a34a" : "#dc2626"} />
              <Box label="CPI" value={fmtIdx(d.cpi)} color={indexColor(d.cpi)} />
              <Box label="SPI" value={fmtIdx(d.spi)} color={indexColor(d.spi)} />
              <Box label="EAC" value={fmtMoney(d.eac)} />
              <Box label="ETC" value={fmtMoney(d.etc)} />
              <Box label="VAC" value={fmtMoney(d.vac)} color={d.vac && d.vac >= 0 ? "#16a34a" : "#dc2626"} />
              <Box label="TCPI" value={fmtIdx(d.tcpi)} color={indexColor(d.tcpi)} />
            </div>
            <h3 style={{ marginTop: 24 }}>Per-task breakdown</h3>
            <table>
              <thead><tr><th>Task</th><th>%</th><th>Planned</th><th>BCWS</th><th>BCWP</th><th>ACWP</th></tr></thead>
              <tbody>
                {d.tasks.map((t: any) => (
                  <tr key={t.task_id}>
                    <td>{t.name}</td><td>{t.percent_complete.toFixed(0)}%</td>
                    <td>{fmtMoney(t.planned_cost)}</td><td>{fmtMoney(t.bcws)}</td>
                    <td>{fmtMoney(t.bcwp)}</td><td>{fmtMoney(t.acwp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Box({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 6, padding: 12 }}>
      <div style={{ fontSize: 11, color: "#6b7280" }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color ?? "#111827" }}>{value}</div>
    </div>
  );
}
