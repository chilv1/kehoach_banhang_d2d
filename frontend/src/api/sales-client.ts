import axios from "axios";
import type {
  AICommandPayload, AIPlanResponse, SalesCampaign, SalesLocation, SalesTask,
} from "@/lib/ai-schema";

const http = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// ---------- Imports ----------
export async function uploadExcel(file: File): Promise<{
  file_id: number;
  sheets_detected: string[];
  rows_per_sheet: Record<string, number>;
  inserted: Record<string, number>;
  warnings: string[];
  errors: string[];
}> {
  const fd = new FormData();
  fd.append("file", file);
  return (await http.post("/imports/excel", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  })).data;
}

// ---------- Sales core ----------
export const listLocations = () => http.get<SalesLocation[]>("/sales/locations").then(r => r.data);
export const listCampaigns = () => http.get<SalesCampaign[]>("/sales/campaigns").then(r => r.data);
export const listTasks = (cid: number) =>
  http.get<SalesTask[]>(`/sales/campaigns/${cid}/tasks`).then(r => r.data);
export const getGantt = (cid: number) =>
  http.get<{ campaign: SalesCampaign; tasks: SalesTask[] }>(
    `/sales/campaigns/${cid}/gantt`,
  ).then(r => r.data);
export const updateTask = (tid: number, patch: Partial<SalesTask>) =>
  http.patch<SalesTask>(`/sales/tasks/${tid}`, patch).then(r => r.data);

// ---------- AI ----------
export const aiCommand = (payload: AICommandPayload) =>
  http.post<AIPlanResponse>(`/ai/${payload.command}`, payload).then(r => r.data);

export const aiApply = (sessionId: number) =>
  http.post<{ status: string; tasks_created: number }>(
    `/ai/apply-plan/${sessionId}`,
  ).then(r => r.data);

// ---------- Dashboard / Map / Export ----------
export const getDashboard = () => http.get("/dashboard/summary").then(r => r.data);
export const getMapLocations = () => http.get("/map/locations").then(r => r.data);
export const routeOptimize = (location_ids: number[], max_per_day = 5) =>
  http.post("/map/route-optimize", { location_ids, max_per_day }).then(r => r.data);
export const exportExcelUrl = (cid: number) => `/api/exports/${cid}/excel`;
