import apiClient from "@/lib/api/client";
import type { PipelineStatusResponse } from "@/types/pipeline";

export const runPipeline = async (): Promise<{ message: string; status: string }> => {
  const response = await apiClient.post<{ message: string; status: string }>("/api/pipeline/run");
  return response.data;
};

export const getPipelineStatus = async (): Promise<PipelineStatusResponse> => {
  const response = await apiClient.get<PipelineStatusResponse>("/api/pipeline/status");
  return response.data;
};
