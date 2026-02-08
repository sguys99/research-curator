import apiClient from "@/lib/api/client";
import type { SchedulerStatus, TriggerJobResponse } from "@/types/scheduler";

export const getSchedulerStatus = async (): Promise<SchedulerStatus> => {
  const response = await apiClient.get<SchedulerStatus>("/api/scheduler/status");
  return response.data;
};

export const triggerSchedulerJob = async (jobId: string): Promise<TriggerJobResponse> => {
  const response = await apiClient.post<TriggerJobResponse>("/api/scheduler/jobs/trigger", {
    job_id: jobId,
  });
  return response.data;
};
