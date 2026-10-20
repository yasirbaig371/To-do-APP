import { apiRequest, queryString } from "./client";
import type {
  AdminStatistics,
  AdminUser,
  User,
  UserTaskStatistics,
} from "../types";

export async function getMyStatistics(): Promise<UserTaskStatistics> {
  return apiRequest<UserTaskStatistics>("/users/me/statistics");
}

export async function updateMyProfile(
  payload: { full_name?: string; email?: string },
): Promise<User> {
  return apiRequest<User>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function changeMyPassword(
  current_password: string,
  new_password: string,
): Promise<void> {
  return apiRequest<void>("/users/me/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password, new_password }),
  });
}

export async function getAdminStatistics(): Promise<AdminStatistics> {
  return apiRequest<AdminStatistics>("/admin/statistics");
}

export async function listAdminUsers(params: {
  search?: string;
  role?: string;
  is_active?: boolean | "";
  limit?: number;
  offset?: number;
}): Promise<AdminUser[]> {
  return apiRequest<AdminUser[]>(`/admin/users${queryString({ ...params })}`);
}

export async function updateAccountStatus(
  id: number,
  is_active: boolean,
): Promise<User> {
  return apiRequest<User>(`/admin/users/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
}

export async function updateAccountRole(
  id: number,
  role: User["role"],
): Promise<User> {
  return apiRequest<User>(`/admin/users/${id}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}
