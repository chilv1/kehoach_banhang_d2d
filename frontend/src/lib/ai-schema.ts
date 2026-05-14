// TypeScript mirror of the AISalesPlan JSON schema.
// Keep in sync with backend/app/sales_planner/schemas/sales_schemas.py.

export type RiskLevel = "low" | "medium" | "high";
export type AICommand =
  | "goal" | "optimize" | "risk" | "recover"
  | "simulate" | "explain" | "daily";

export interface AIMerch {
  boligrafo: number;
  taza: number;
  llavero: number;
  papin: number;
  sombrero: number;
}

export interface AIPlanItem {
  task_name: string;
  code_ubicacion: string;
  br: string;
  bc: string;
  distrito?: string | null;
  tipo_df_cp?: string | null;
  people_in_charge?: string | null;
  grupo_code_pr?: string | null;
  start_date: string;      // ISO date
  end_date: string;        // ISO date
  duration_days: number;
  priority: number;
  target_activation: number;
  target_mnp: number;
  target_tv360: number;
  target_bipay: number;
  planned_cost: number;
  merchandising: AIMerch;
  risk_level: RiskLevel;
  risk_reason?: string | null;
  checklist: string[];
  reasoning?: string | null;
}

export interface AIResourceAlloc {
  pr_code: string;
  days: number;
  tasks: number[];
}

export interface AIPlanResponse {
  session_id: number;
  summary: string;
  planning_assumptions: string[];
  campaign_plan: AIPlanItem[];
  resource_allocation: AIResourceAlloc[];
  risks: Record<string, unknown>[];
  warnings: string[];
  recommendations: string[];
  changes_preview: Record<string, unknown>[];
  requires_user_approval: boolean;
  provider: string;
  duration_ms: number;
}

export interface AICommandPayload {
  command: AICommand;
  prompt: string;
  campaign_id?: number | null;
  scenario?: Record<string, unknown> | null;
}

// --- Sales entities mirroring the backend ---

export interface SalesLocation {
  id: number;
  code: string;
  branch_id: number;
  business_center_id: number;
  departamento: string | null;
  distrito: string | null;
  tipo_df_cp: string | null;
  horario_traffico: string | null;
  fecha_alta_traffico: string | null;
  prioridad: number;
  latitud: number | null;
  longitud: number | null;
  nota: string | null;
  is_active: boolean;
}

export interface SalesCampaign {
  id: number;
  name: string;
  description: string | null;
  branch_id: number | null;
  start_date: string;
  end_date: string | null;
  status_date: string | null;
  horizon_days: number;
}

export interface SalesTask {
  id: number;
  wbs?: string | null;
  name?: string;
  task_name?: string;
  start?: string | null;
  end?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  duration_days?: number | null;
  progress: number;
  status: string;
  priority: number;
  risk_level: string;
  is_milestone: boolean;
  is_summary: boolean;
  is_critical: boolean;
  parent_id?: number | null;
  bc_id?: number | null;
  location_id?: number | null;
  distrito?: string | null;
  tipo_df_cp?: string | null;
  pr_staff_id?: number | null;
  group_id?: number | null;
  people_in_charge?: string | null;
  campana_ok?: string | null;
}
