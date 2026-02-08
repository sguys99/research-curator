export type PipelineStatus = "idle" | "running" | "completed" | "failed";

export type PipelineStatusResponse = {
  status: PipelineStatus;
  message: string;
};
