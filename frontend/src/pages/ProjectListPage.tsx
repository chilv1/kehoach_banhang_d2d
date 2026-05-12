import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createProject, deleteProject, listProjects } from "@/api/client";
import { useState } from "react";

export default function ProjectListPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const [name, setName] = useState("New project");
  const [start, setStart] = useState(new Date().toISOString().slice(0, 10));

  const createMut = useMutation({
    mutationFn: () =>
      createProject({ name, start_date: new Date(start + "T08:00:00").toISOString() }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });

  return (
    <div className="page">
      <div className="card" style={{ padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Projects</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" />
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          <button className="primary" onClick={() => createMut.mutate()}>+ New project</button>
        </div>
        {isLoading && <div>Loading…</div>}
        <table>
          <thead>
            <tr><th>ID</th><th>Name</th><th>Start</th><th>Finish</th><th>Updated</th><th></th></tr>
          </thead>
          <tbody>
            {data?.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>
                  <a href="#" onClick={(e) => { e.preventDefault(); nav(`/projects/${p.id}`); }}>
                    {p.name}
                  </a>
                </td>
                <td>{p.start_date?.slice(0, 10)}</td>
                <td>{p.finish_date?.slice(0, 10) ?? "—"}</td>
                <td>{p.updated_at?.slice(0, 16).replace("T", " ")}</td>
                <td>
                  <button className="danger" onClick={() => deleteMut.mutate(p.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
