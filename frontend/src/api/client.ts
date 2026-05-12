import axios from "axios";
import type {
  Project, Task, Dependency, Resource, Assignment, Baseline, ScheduleResult,
} from "@/types";

const http = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Projects
export const listProjects = () => http.get<Project[]>("/projects").then(r => r.data);
export const getProject = (id: number) => http.get<Project>(`/projects/${id}`).then(r => r.data);
export const createProject = (data: Partial<Project>) =>
  http.post<Project>("/projects", data).then(r => r.data);
export const updateProject = (id: number, data: Partial<Project>) =>
  http.patch<Project>(`/projects/${id}`, data).then(r => r.data);
export const deleteProject = (id: number) => http.delete(`/projects/${id}`);
export const scheduleProject = (id: number) =>
  http.post<ScheduleResult>(`/projects/${id}/schedule`).then(r => r.data);

// Tasks
export const listTasks = (pid: number) =>
  http.get<Task[]>(`/projects/${pid}/tasks`).then(r => r.data);
export const createTask = (data: Partial<Task>) =>
  http.post<Task>("/tasks", data).then(r => r.data);
export const updateTask = (id: number, data: Partial<Task>) =>
  http.patch<Task>(`/tasks/${id}`, data).then(r => r.data);
export const deleteTask = (id: number) => http.delete(`/tasks/${id}`);

// Dependencies
export const listDependencies = (pid: number) =>
  http.get<Dependency[]>(`/projects/${pid}/dependencies`).then(r => r.data);
export const createDependency = (data: Partial<Dependency>) =>
  http.post<Dependency>("/dependencies", data).then(r => r.data);
export const deleteDependency = (id: number) => http.delete(`/dependencies/${id}`);

// Resources
export const listResources = (pid: number) =>
  http.get<Resource[]>(`/projects/${pid}/resources`).then(r => r.data);
export const createResource = (data: Partial<Resource>) =>
  http.post<Resource>("/resources", data).then(r => r.data);
export const updateResource = (id: number, data: Partial<Resource>) =>
  http.patch<Resource>(`/resources/${id}`, data).then(r => r.data);
export const deleteResource = (id: number) => http.delete(`/resources/${id}`);

// Assignments
export const listAssignments = (tid: number) =>
  http.get<Assignment[]>(`/tasks/${tid}/assignments`).then(r => r.data);
export const createAssignment = (data: Partial<Assignment>) =>
  http.post<Assignment>("/assignments", data).then(r => r.data);
export const updateAssignment = (id: number, data: Partial<Assignment>) =>
  http.patch<Assignment>(`/assignments/${id}`, data).then(r => r.data);
export const deleteAssignment = (id: number) => http.delete(`/assignments/${id}`);

// Baselines
export const listBaselines = (pid: number) =>
  http.get<Baseline[]>(`/projects/${pid}/baselines`).then(r => r.data);
export const createBaseline = (data: { project_id: number; number: number; name?: string }) =>
  http.post<Baseline>("/baselines", data).then(r => r.data);
export const deleteBaseline = (id: number) => http.delete(`/baselines/${id}`);
