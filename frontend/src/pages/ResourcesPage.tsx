import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createResource, deleteResource, getProject, listResources,
} from "@/api/client";
import type { ResourceType } from "@/types";

export default function ResourcesPage() {
  const { pid } = useParams();
  const projectId = Number(pid);
  const qc = useQueryClient();
  const projQ = useQuery({ queryKey: ["project", projectId], queryFn: () => getProject(projectId) });
  const resQ = useQuery({ queryKey: ["resources", projectId], queryFn: () => listResources(projectId) });
  const [name, setName] = useState("");
  const [type, setType] = useState<ResourceType>("WORK");
  const [maxUnits, setMaxUnits] = useState(1);
  const [rate, setRate] = useState(0);
  const addMut = useMutation({
    mutationFn: () => createResource({ project_id: projectId, name, type, max_units: maxUnits, standard_rate: rate }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["resources", projectId] }); setName(""); },
  });
  const delMut = useMutation({
    mutationFn: (id: number) => deleteResource(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resources", projectId] }),
  });
  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}><Link to={`/projects/${projectId}`}>← Project</Link></div>
      <div className="card">
        <div className="toolbar"><strong style={{ fontSize: 15 }}>{projQ.data?.name} — Resources</strong></div>
        <div style={{ padding: 12, display: "flex", gap: 8 }}>
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value as ResourceType)}>
            <option value="WORK">Work (người)</option>
            <option value="MATERIAL">Material</option>
            <option value="COST">Cost</option>
          </select>
          <input type="number" step="0.1" placeholder="Max units" value={maxUnits}
                  onChange={(e) => setMaxUnits(parseFloat(e.target.value))} style={{ width: 90 }} />
          <input type="number" placeholder="Std rate /h" value={rate}
                  onChange={(e) => setRate(parseFloat(e.target.value))} style={{ width: 110 }} />
          <button className="primary" disabled={!name} onClick={() => addMut.mutate()}>+ Add resource</button>
        </div>
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Max Units</th><th>Std Rate</th><th>OT Rate</th><th></th></tr></thead>
          <tbody>
            {resQ.data?.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td><td>{r.name}</td><td>{r.type}</td>
                <td>{(r.max_units * 100).toFixed(0)}%</td>
                <td>${r.standard_rate}/h</td><td>${r.overtime_rate}/h</td>
                <td><button className="danger" onClick={() => delMut.mutate(r.id)}>🗑</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
