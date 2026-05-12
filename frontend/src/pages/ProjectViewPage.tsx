import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Gantt, Task as GanttTask, ViewMode } from "gantt-task-react";
import {
  createDependency, createTask, deleteTask, getProject, listDependencies,
  listTasks, scheduleProject, updateTask,
} from "@/api/client";
import type { Task as ApiTask } from "@/types";
import TaskGrid from "@/components/TaskGrid/TaskGrid";

export default function ProjectViewPage() {
  const { pid } = useParams();
  const projectId = Number(pid);
  const qc = useQueryClient();
  const [view, setView] = useState<ViewMode>(ViewMode.Day);
  const [tab, setTab] = useState<"gantt" | "grid">("gantt");

  const projQ = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });
  const tasksQ = useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => listTasks(projectId),
  });
  const depsQ = useQuery({
    queryKey: ["deps", projectId],
    queryFn: () => listDependencies(projectId),
  });

  const scheduleMut = useMutation({
    mutationFn: () => scheduleProject(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
  const addTaskMut = useMutation({
    mutationFn: () =>
      createTask({
        project_id: projectId, name: "New task", duration_hours: 8,
        sort_order: (tasksQ.data?.length ?? 0) + 1,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
  const delTaskMut = useMutation({
    mutationFn: (id: number) => deleteTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
  const updateTaskMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateTask(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });

  const ganttTasks: GanttTask[] = useMemo(() => {
    if (!tasksQ.data) return [];
    const tasks = tasksQ.data;
    const deps = depsQ.data ?? [];
    return tasks
      .filter((t) => t.start_date && t.finish_date)
      .map<GanttTask>((t) => ({
        id: String(t.id),
        name: t.name,
        start: new Date(t.start_date!),
        end: t.is_milestone
          ? new Date(new Date(t.start_date!).getTime() + 24 * 3600 * 1000)
          : new Date(t.finish_date!),
        progress: t.percent_complete ?? 0,
        type: t.is_milestone ? "milestone" : t.is_summary ? "project" : "task",
        isDisabled: false,
        styles: t.is_critical
          ? { progressColor: "#ef4444", backgroundColor: "#fecaca", progressSelectedColor: "#b91c1c", backgroundSelectedColor: "#fca5a5" }
          : undefined,
        dependencies: deps
          .filter((d) => d.successor_id === t.id)
          .map((d) => String(d.predecessor_id)),
      }));
  }, [tasksQ.data, depsQ.data]);

  if (projQ.isLoading) return <div className="page">Loading…</div>;
  if (!projQ.data) return <div className="page">Project not found</div>;

  return (
    <div className="page">
      <div style={{ marginBottom: 8 }}>
        <Link to="/">← Projects</Link>
      </div>
      <div className="card">
        <div className="toolbar">
          <strong style={{ fontSize: 15 }}>{projQ.data.name}</strong>
          <span style={{ color: "#6b7280", marginLeft: 8 }}>
            {projQ.data.start_date?.slice(0, 10)} → {projQ.data.finish_date?.slice(0, 10) ?? "—"}
          </span>
          <span style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
            <button className={tab === "gantt" ? "primary" : ""} onClick={() => setTab("gantt")}>📊 Gantt</button>
            <button className={tab === "grid" ? "primary" : ""} onClick={() => setTab("grid")}>📋 Grid</button>
            <Link to={`/projects/${projectId}/resources`}>
              <button>🧑 Resources</button>
            </Link>
            <button onClick={() => addTaskMut.mutate()}>+ Task</button>
            <button className="primary" onClick={() => scheduleMut.mutate()}>
              ⚙️ Schedule (CPM)
            </button>
          </span>
        </div>

        {tab === "gantt" && (
          <div className="gantt-container">
            <div style={{ padding: "6px 12px", display: "flex", gap: 6 }}>
              <button onClick={() => setView(ViewMode.Hour)}>Hour</button>
              <button onClick={() => setView(ViewMode.Day)}>Day</button>
              <button onClick={() => setView(ViewMode.Week)}>Week</button>
              <button onClick={() => setView(ViewMode.Month)}>Month</button>
            </div>
            {ganttTasks.length > 0 ? (
              <Gantt
                tasks={ganttTasks}
                viewMode={view}
                listCellWidth=""
                columnWidth={60}
                onDateChange={(t) => {
                  const id = Number(t.id);
                  // recompute duration in hours from new dates (working time approx 8h/day)
                  const ms = t.end.getTime() - t.start.getTime();
                  const days = ms / (1000 * 3600 * 24);
                  updateTaskMut.mutate({
                    id,
                    data: {
                      duration_hours: Math.max(1, Math.round(days * 8)),
                      constraint_type: "MSO",
                      constraint_date: t.start.toISOString(),
                    },
                  });
                }}
                onProgressChange={(t) =>
                  updateTaskMut.mutate({ id: Number(t.id), data: { percent_complete: t.progress } })
                }
                onDoubleClick={(t) => {
                  if (confirm(`Xoá task "${t.name}"?`)) delTaskMut.mutate(Number(t.id));
                }}
              />
            ) : (
              <div style={{ padding: 24, color: "#6b7280" }}>
                Chưa có task có ngày. Bấm <b>+ Task</b> rồi <b>⚙️ Schedule</b>.
              </div>
            )}
          </div>
        )}

        {tab === "grid" && (
          <TaskGrid
            tasks={tasksQ.data ?? []}
            deps={depsQ.data ?? []}
            onUpdate={(id, data) => updateTaskMut.mutate({ id, data })}
            onDelete={(id) => delTaskMut.mutate(id)}
            onAddDep={(pred, succ) =>
              createDependency({ predecessor_id: pred, successor_id: succ, link_type: "FS" })
                .then(() => {
                  qc.invalidateQueries({ queryKey: ["deps", projectId] });
                })
            }
          />
        )}
      </div>
    </div>
  );
}
