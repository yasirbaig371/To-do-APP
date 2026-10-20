export type UserRole = "user" | "admin";
export type TaskStatus = "pending" | "in_progress" | "completed";
export type TaskPriority = "low" | "medium" | "high";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface UserTaskStatistics {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
}

export interface AdminStatistics {
  total_users: number;
  active_users: number;
  inactive_users: number;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  total_admins: number;
}

export interface AdminUser extends User {
  task_count: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface TaskQuery {
  status?: TaskStatus | "";
  priority?: TaskPriority | "";
  search?: string;
  sort_by?: "created_at" | "updated_at" | "due_date" | "title" | "priority";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatToolResult {
  tool: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface ChatResponse {
  response: string;
  requires_confirmation: boolean;
  tool_name: string | null;
  tool_results: ChatToolResult[];
}
