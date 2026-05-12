export type LinkType = "FS" | "SS" | "FF" | "SF";
export type TaskConstraint =
  | "ASAP" | "ALAP" | "MSO" | "MFO" | "SNET" | "SNLT" | "FNET" | "FNLT";
export type TaskType = "FIXED_DURATION" | "FIXED_UNITS" | "FIXED_WORK";
export type ResourceType = "WORK" | "MATERIAL" | "COST";

export interface Project {
  id: number;
  name: string;
  description: string | null;
  start_date: string;
  finish_date: string | null;
  status_date: string | null;
  calendar_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  project_id: number;
  parent_id: number | null;
  wbs: string | null;
  outline_level: number;
  sort_order: number;
  name: string;
  notes: string | null;
  duration_hours: number;
  is_milestone: boolean;
  is_summary: boolean;
  task_type: TaskType;
  start_date: string | null;
  finish_date: string | null;
  early_start: string | null;
  early_finish: string | null;
  late_start: string | null;
  late_finish: string | null;
  total_slack_hours: number;
  free_slack_hours: number;
  is_critical: boolean;
  constraint_type: TaskConstraint;
  constraint_date: string | null;
  deadline: string | null;
  percent_complete: number;
  actual_start: string | null;
  actual_finish: string | null;
  actual_work_hours: number;
  actual_cost: number;
  fixed_cost: number;
  priority: number;
  calendar_id: number | null;
}

export interface Dependency {
  id: number;
  predecessor_id: number;
  successor_id: number;
  link_type: LinkType;
  lag_hours: number;
}

export interface Resource {
  id: number;
  project_id: number;
  name: string;
  initials: string | null;
  type: ResourceType;
  group: string | null;
  email: string | null;
  max_units: number;
  standard_rate: number;
  overtime_rate: number;
  cost_per_use: number;
  calendar_id: number | null;
}

export interface Assignment {
  id: number;
  task_id: number;
  resource_id: number;
  units: number;
  work_hours: number;
  actual_work_hours: number;
  cost: number;
}

export interface Baseline {
  id: number;
  project_id: number;
  number: number;
  name: string;
  snapshot_date: string;
}

export interface ScheduleResult {
  n_tasks: number;
  n_critical: number;
  project_start: string | null;
  project_finish: string | null;
}
