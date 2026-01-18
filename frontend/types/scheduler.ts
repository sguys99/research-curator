export type SchedulerJob = {
  id: string;
  name: string;
  next_run_time: string | null;
  trigger: string;
};

export type SchedulerStatus = {
  running: boolean;
  timezone: string;
  current_time: string;
  jobs: SchedulerJob[];
};

export type TriggerJobResponse = {
  success: boolean;
  message: string;
  job_id: string;
  triggered_at: string;
};
