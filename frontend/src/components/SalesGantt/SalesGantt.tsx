/**
 * SalesGantt — MS Project–style Gantt for sales campaigns.
 *
 * Phase 1 implementation:
 *  - Adapts `gantt-task-react` (already installed) with sales-specific colours,
 *    status badges, and grouping support.
 *  - Drag/resize commits via PATCH /api/sales/tasks/{id}.
 *
 * Phase 2 will replace this with a custom Canvas/SVG renderer so the look-and-
 * feel mirrors Microsoft Project exactly (dependency arrows, baseline overlay,
 * critical path highlight, virtualised grid+timeline).
 */
import { useMemo } from "react";
import { Gantt, Task as GanttTask, ViewMode } from "gantt-task-react";
import type { SalesTask } from "@/lib/ai-schema";
import { updateTask } from "@/api/sales-client";

const STATUS_COLORS: Record<string, { bg: string; bar: string }> = {
  PLANNED:     { bg: "#dbeafe", bar: "#2563eb" },
  IN_PROGRESS: { bg: "#fef3c7", bar: "#d97706" },
  COMPLETED:   { bg: "#dcfce7", bar: "#16a34a" },
  DELAYED:     { bg: "#fee2e2", bar: "#dc2626" },
  AT_RISK:     { bg: "#ffedd5", bar: "#ea580c" },
  NO_OK:       { bg: "#fee2e2", bar: "#dc2626" },
  OK:          { bg: "#dcfce7", bar: "#16a34a" },
  CANCELLED:   { bg: "#e5e7eb", bar: "#6b7280" },
};

interface Props {
  tasks: SalesTask[];
  view: ViewMode;
  onTasksChanged: () => void;
}

export default function SalesGantt({ tasks, view, onTasksChanged }: Props) {
  const ganttItems: GanttTask[] = useMemo(() => {
    return tasks
      .map((t) => {
        const start = t.start ?? t.start_date;
        const end = t.end ?? t.end_date;
        if (!start || !end) return null;
        const palette = STATUS_COLORS[t.status] ?? STATUS_COLORS.PLANNED;
        return {
          id: String(t.id),
          name: t.name ?? t.task_name ?? "Task",
          start: new Date(start),
          end: t.is_milestone
            ? new Date(new Date(start).getTime() + 24 * 3600 * 1000)
            : new Date(end),
          progress: Number(t.progress ?? 0),
          type: t.is_milestone ? "milestone" : t.is_summary ? "project" : "task",
          isDisabled: false,
          styles: {
            backgroundColor: palette.bg,
            progressColor: palette.bar,
            backgroundSelectedColor: palette.bg,
            progressSelectedColor: palette.bar,
          },
          // dependencies could be filled if we fetched links
        } as GanttTask;
      })
      .filter((x): x is GanttTask => x !== null);
  }, [tasks]);

  if (ganttItems.length === 0) {
    return (
      <div style={{ padding: 32, color: "#6b7280", textAlign: "center" }}>
        Chưa có task với ngày Start/End. Hãy <b>Import Excel</b> hoặc bấm <b>/goal</b> để
        AI sinh kế hoạch.
      </div>
    );
  }

  return (
    <Gantt
      tasks={ganttItems}
      viewMode={view}
      columnWidth={view === ViewMode.Month ? 280 : 60}
      listCellWidth="155px"
      onDateChange={async (t) => {
        const id = Number(t.id);
        await updateTask(id, {
          start_date: t.start.toISOString().slice(0, 10) as any,
          end_date: t.end.toISOString().slice(0, 10) as any,
        });
        onTasksChanged();
      }}
      onProgressChange={async (t) => {
        await updateTask(Number(t.id), { progress: t.progress });
        onTasksChanged();
      }}
      onDoubleClick={() => {
        // Phase 2: open task detail drawer
      }}
    />
  );
}
