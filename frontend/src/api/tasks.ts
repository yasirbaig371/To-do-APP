import { apiRequest, queryString } from "./client";
import type { Task, TaskQuery } from "../types";

export interface TaskInput {
  title: string;
  description: string | null;
  status: Task["status"];
  priority: Task["priority"];
  due_date: string | null;
}

export async function listTasks(params: TaskQuery = {}): Promise<Task[]> {
  return apiRequest<Task[]>(`/tasks${queryString({ ...params })}`);
}

export async function getTask(id: number): Promise<Task> {
  return apiRequest<Task>(`/tasks/${id}`);
}

export async function createTask(payload: TaskInput): Promise<Task> {
  return apiRequest<Task>("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTask(
  id: number,
  payload: Partial<TaskInput>,
): Promise<Task> {
  return apiRequest<Task>(`/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteTask(id: number): Promise<void> {
  return apiRequest<void>(`/tasks/${id}`, { method: "DELETE" });
}
