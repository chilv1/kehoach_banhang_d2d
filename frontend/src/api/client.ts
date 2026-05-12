import axios from "axios";
import type {
  Project, Task, Dependency, Resource, Assignment, Baseline, ScheduleResult,
} from "@/types";

const http = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

export const listProjects = () => http.get<Project[]>("/projects").then(r => r.data);
export const getProject = (id: number) => http.get<Project>(`/projects/${id}`).then(r => r.data);
export const createProject = (data: Partial<Project>) => http.post<Project>("/projects", data).then(r => r.data);
export const updateProject = (id: number, data: Partial<Project>) => http.patch<Project>(`/projects/${id}`, data).then(r => r.data);
export const deleteProject = (id: number) => http.delete(`/projects/${id}`);
export const scheduleProject = (id: number) => http.post<ScheduleResult>(`/projects/${id}/schedule`).then(r => r.data);

export const listTasks = (pid: number) => http.get<Task[]>(`/projects/${pid}/tasks`).then(r => r.data);
export const createTask = (data: Partial<Task>) => http.post<Task>("/tasks", data).then(r => r.data);
export const updateTask = (id: number, data: Partial<Task>) => http.patch<Task>(`/tasks/${id}`, data).then(r => r.data);
export const deleteTask = (id: number) => http.delete(`/tasks/${id}`);

export const listDependencies = (pid: number) => http.get<Dependency[]>(`/projects/${pid}/dependencies`).then(r => r.data);
export const createDependency = (data: Partial<Dependency>) => http.post<Dependency>("/dependencies", data).then(r => r.data);
export const deleteDependency = (id: number) => http.delete(`/dependencies/${id}`);

export const listResources = (pid: number) => http.get<Resource[]>(`/projects/${pid}/resources`).then(r => r.data);
export const createResource = (data: Partial<Resource>) => http.post<Resource>("/resources", data).then(r => r.data);
export const updateResource = (id: number, data: Partial<Resource>) => http.patch<Resource>(`/resources/${id}`, data).then(r => r.data);
export const deleteResource = (id: number) => http.delete(`/resources/${id}`);

export const listAssignments = (tid: number) => http.get<Assignment[]>(`/tasks/${tid}/assignments`).then(r => r.data);
export const createAssignment = (data: Partial<Assignment>) => http.post<Assignment>("/assignments", data).then(r => r.data);
export const updateAssignment = (id: number, data: Partial<Assignment>) => http.patch<Assignment>(`/assignments/${id}`, data).then(r => r.data);
export const deleteAssignment = (id: number) => http.delete(`/assignments/${id}`);

export const listBaselines = (pid: number) => http.get<Baseline[]>(`/projects/${pid}/baselines`).then(r => r.data);
export const createBaseline = (data: { project_id: number; number: number; name?: string }) => http.post<Baseline>("/baselines", data).then(r => r.data);
export const deleteBaseline = (id: number) => http.delete(`/baselines/${id}`);

export const indentTask = (id: number) => http.post(`/tasks/${id}/indent`).then(r => r.data);
export const outdentTask = (id: number) => http.post(`/tasks/${id}/outdent`).then(r => r.data);
export const moveTask = (id: number, sort_order: number) => http.post(`/tasks/${id}/move`, { sort_order }).then(r => r.data);

export const recomputeCosts = (pid: number) => http.post(`/projects/${pid}/costs/recompute`).then(r => r.data);

export const getVariance = (pid: number, baseline_number = 0) =>
  http.get(`/projects/${pid}/variance`, { params: { baseline_number } }).then(r => r.data);

export const getOverallocations = (pid: number) => http.get(`/projects/${pid}/overallocations`).then(r => r.data);
export const getResourceLoad = (pid: number) => http.get(`/projects/${pid}/resource-load`).then(r => r.data);
export const levelResources = (pid: number) => http.post(`/projects/${pid}/level`).then(r => r.data);

export const getEvm = (pid: number, status_date?: string) =>
  http.get(`/projects/${pid}/evm`, { params: status_date ? { status_date } : {} }).then(r => r.data);

export const exportXmlUrl = (pid: number) => `/api/projects/${pid}/export-xml`;
export const importXml = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return http.post<{ project_id: number; status: string }>(
    "/projects/import-xml", fd,
    { headers: { "Content-Type": "multipart/form-data" } },
  ).then(r => r.data);
};

export const register = (data: { username: string; password: string; full_name?: string; email?: string }) =>
  http.post("/auth/register", data).then(r => r.data);
export const login = (username: string, password: string) => {
  const fd = new FormData();
  fd.append("username", username);
  fd.append("password", password);
  return http.post<{ access_token: string; user: any }>(
    "/auth/login", fd,
    { headers: { "Content-Type": "multipart/form-data" } },
  ).then(r => r.data);
};
export const getMe = () => http.get("/auth/me").then(r => r.data);
