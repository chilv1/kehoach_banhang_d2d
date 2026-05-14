import { useMemo } from "react";
import type { SalesTask } from "@/lib/ai-schema";

export interface FilterState {
  br: string[];
  bc: string[];
  distrito: string[];
  tipo: string[];
  status: string[];
  priority: number[];
  grouping: "br_bc_distrito" | "br_bc_grupo" | "tipo_distrito" | "flat";
}

interface Props {
  tasks: SalesTask[];
  value: FilterState;
  onChange: (next: FilterState) => void;
}

export default function SalesFilterBar({ tasks, value, onChange }: Props) {
  const opts = useMemo(() => {
    const collect = (key: keyof SalesTask) =>
      Array.from(new Set(tasks.map((t) => t[key]).filter(Boolean))).sort() as string[];
    return {
      distrito: collect("distrito"),
      tipo: collect("tipo_df_cp"),
      status: collect("status"),
    };
  }, [tasks]);

  const toggle = <T,>(arr: T[], v: T): T[] =>
    arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];

  return (
    <div style={{
      display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center",
      padding: "6px 12px", borderBottom: "1px solid #e5e7eb", background: "white",
    }}>
      <strong style={{ fontSize: 12 }}>Filter:</strong>
      <select
        multiple
        size={1}
        value={value.distrito}
        onChange={(e) => onChange({
          ...value,
          distrito: Array.from(e.target.selectedOptions, (o) => o.value),
        })}
        style={{ minWidth: 140, padding: 4, fontSize: 12 }}
        title="Distrito"
      >
        {opts.distrito.map((d) => <option key={d} value={d}>{d}</option>)}
      </select>
      <select
        multiple
        size={1}
        value={value.tipo}
        onChange={(e) => onChange({
          ...value,
          tipo: Array.from(e.target.selectedOptions, (o) => o.value),
        })}
        style={{ minWidth: 120, padding: 4, fontSize: 12 }}
        title="Tipo DF/CP"
      >
        {opts.tipo.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <select
        multiple
        size={1}
        value={value.status}
        onChange={(e) => onChange({
          ...value,
          status: Array.from(e.target.selectedOptions, (o) => o.value),
        })}
        style={{ minWidth: 120, padding: 4, fontSize: 12 }}
        title="Status"
      >
        {opts.status.map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      <span style={{ marginLeft: "auto", fontSize: 12 }}>Group by:</span>
      <select
        value={value.grouping}
        onChange={(e) => onChange({ ...value, grouping: e.target.value as FilterState["grouping"] })}
        style={{ padding: 4, fontSize: 12 }}
      >
        <option value="flat">— None —</option>
        <option value="br_bc_distrito">BR &gt; BC &gt; Distrito</option>
        <option value="br_bc_grupo">BR &gt; BC &gt; Grupo</option>
        <option value="tipo_distrito">Tipo &gt; Distrito</option>
      </select>
    </div>
  );
}
