import apiClient from "@/lib/api/client";
import type { DigestListResponse } from "@/types/digests";
import type { User, UserPreferences } from "@/types/user";

export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>("/users/me");
  return response.data;
};

export const updateUser = async (payload: { name?: string }): Promise<User> => {
  const response = await apiClient.put<User>("/users/me", payload);
  return response.data;
};

export const getUserPreferences = async (userId: string): Promise<UserPreferences> => {
  const response = await apiClient.get<UserPreferences>(`/users/${userId}/preferences`);
  return response.data;
};

export const updateUserPreferences = async (
  userId: string,
  payload: Partial<UserPreferences>,
): Promise<UserPreferences> => {
  const response = await apiClient.put<UserPreferences>(`/users/${userId}/preferences`, payload);
  return response.data;
};

export const getUserDigests = async (userId: string): Promise<DigestListResponse> => {
  const response = await apiClient.get<DigestListResponse>(`/users/${userId}/digests`);
  return response.data;
};

export const sendTestDigest = async (userId: string): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`/users/${userId}/digests/test`);
  return response.data;
};
