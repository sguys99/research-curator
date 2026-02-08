import apiClient from "@/lib/api/client";
import type {
  Feedback,
  FeedbackCreatePayload,
  FeedbackListResponse,
  FeedbackStatsResponse,
  FeedbackUpdatePayload,
} from "@/types/feedback";

export const createFeedback = async (payload: FeedbackCreatePayload): Promise<Feedback> => {
  const response = await apiClient.post<Feedback>("/api/feedback", payload);
  return response.data;
};

export const getUserFeedback = async (
  userId: string,
  skip = 0,
  limit = 50,
): Promise<FeedbackListResponse> => {
  const response = await apiClient.get<FeedbackListResponse>(`/api/feedback/user/${userId}`, {
    params: { skip, limit },
  });
  return response.data;
};

export const updateFeedback = async (
  feedbackId: string,
  payload: FeedbackUpdatePayload,
): Promise<Feedback> => {
  const response = await apiClient.put<Feedback>(`/api/feedback/${feedbackId}`, payload);
  return response.data;
};

export const deleteFeedback = async (feedbackId: string): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/api/feedback/${feedbackId}`);
  return response.data;
};

export const getArticleFeedbackStats = async (
  articleId: string,
): Promise<FeedbackStatsResponse> => {
  const response = await apiClient.get<FeedbackStatsResponse>(
    `/api/feedback/article/${articleId}/stats`,
  );
  return response.data;
};
