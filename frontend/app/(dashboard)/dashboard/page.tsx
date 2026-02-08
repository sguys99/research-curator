"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";
import { getArticleStatistics } from "@/lib/api/articles";
import { getPipelineStatus, runPipeline } from "@/lib/api/pipeline";
import { getSchedulerStatus } from "@/lib/api/scheduler";
import { getUserDigests, sendTestDigest } from "@/lib/api/users";

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function DashboardPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [pipelinePolling, setPipelinePolling] = useState(false);

  const statsQuery = useQuery({
    queryKey: ["articles", "stats"],
    queryFn: getArticleStatistics,
  });

  const digestsQuery = useQuery({
    queryKey: ["digests", user?.id],
    queryFn: () => getUserDigests(user?.id ?? ""),
    enabled: Boolean(user?.id),
  });

  const schedulerQuery = useQuery({
    queryKey: ["scheduler", "status"],
    queryFn: getSchedulerStatus,
    enabled: Boolean(user?.id),
  });

  const testDigestMutation = useMutation({
    mutationFn: (userId: string) => sendTestDigest(userId),
    onSuccess: (data) =>
      toast({ title: "Test digest sent", description: data.message, variant: "success" }),
    onError: (error) => {
      const detail =
        (error as unknown as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      toast({
        title: "Failed to send test digest",
        description: detail || (error instanceof Error ? error.message : "Unknown error"),
        variant: "error",
      });
    },
  });

  const pipelineStatusQuery = useQuery({
    queryKey: ["pipeline", "status"],
    queryFn: getPipelineStatus,
    enabled: pipelinePolling,
    refetchInterval: pipelinePolling ? 3000 : false,
  });

  const pipelineStatus = pipelineStatusQuery.data?.status;

  useEffect(() => {
    if (pipelineStatus === "completed") {
      setPipelinePolling(false);
      toast({ title: "Pipeline completed", description: pipelineStatusQuery.data?.message, variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["articles", "stats"] });
    } else if (pipelineStatus === "failed") {
      setPipelinePolling(false);
      toast({ title: "Pipeline failed", description: pipelineStatusQuery.data?.message, variant: "error" });
    }
  }, [pipelineStatus]);

  const runPipelineMutation = useMutation({
    mutationFn: runPipeline,
    onSuccess: () => {
      setPipelinePolling(true);
      toast({ title: "Pipeline started", description: "Collecting and processing articles...", variant: "success" });
    },
    onError: (error) => {
      const detail =
        (error as unknown as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      toast({
        title: "Failed to start pipeline",
        description: detail || (error instanceof Error ? error.message : "Unknown error"),
        variant: "error",
      });
    },
  });

  const schedulerSummary = useMemo(() => {
    if (!schedulerQuery.data) {
      return null;
    }
    const nextRuns = schedulerQuery.data.jobs
      .map((job) => ({ id: job.id, next: job.next_run_time }))
      .filter((job) => job.next);
    const nextRun = nextRuns.length
      ? nextRuns.sort((a, b) => (a.next ?? "").localeCompare(b.next ?? ""))[0]?.next
      : null;
    return {
      running: schedulerQuery.data.running,
      timezone: schedulerQuery.data.timezone,
      current: schedulerQuery.data.current_time,
      next: nextRun,
    };
  }, [schedulerQuery.data]);

  const stats = [
    {
      label: "Articles tracked",
      value: statsQuery.data ? statsQuery.data.total.toLocaleString() : "-",
    },
    {
      label: "Digests sent",
      value: digestsQuery.data ? digestsQuery.data.total.toLocaleString() : "-",
    },
    {
      label: "Avg. importance",
      value: statsQuery.data
        ? `${statsQuery.data.average_importance_score.toFixed(2)} / 1.0`
        : "-",
    },
  ];

  const recentDigests = digestsQuery.data?.digests.slice(0, 3) ?? [];

  return (
    <div className="space-y-8">
      <section className="grid gap-4 md:grid-cols-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-sm text-slate-500">{stat.label}</p>
            <p className="mt-3 text-2xl font-semibold text-slate-900">{stat.value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-semibold text-slate-900">Recent digests</h2>
            <button className="text-sm font-medium text-blue-600">View all</button>
          </div>
          <div className="mt-6 space-y-4">
            {recentDigests.length ? (
              recentDigests.map((digest) => (
                <div
                  key={digest.id}
                  className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      Digest • {formatDateTime(digest.sent_at)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {digest.article_ids.length} items curated
                    </p>
                  </div>
                  <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                    {digest.email_opened ? "Opened" : "Sent"}
                  </span>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                No digests yet. Complete onboarding and run a test digest to get started.
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Scheduler status</h3>
            <p className="mt-3 text-sm text-slate-500">
              {schedulerSummary
                ? `Now ${formatDateTime(schedulerSummary.current)} • Next ${formatDateTime(
                    schedulerSummary.next,
                  )}`
                : "Loading scheduler status..."}
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs text-emerald-600">
              <span
                className={`h-2 w-2 rounded-full ${
                  schedulerSummary?.running ? "bg-emerald-500" : "bg-slate-300"
                }`}
              />
              {schedulerSummary?.running ? "Running" : "Paused"}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Quick actions</h3>
            <div className="mt-4 flex flex-col gap-3 text-sm">
              <button
                className="rounded-full bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                onClick={() => user?.id && testDigestMutation.mutate(user.id)}
                disabled={!user?.id || testDigestMutation.isPending || statsQuery.data?.total === 0}
              >
                {testDigestMutation.isPending ? "Sending..." : "Send test digest"}
              </button>
              {statsQuery.data?.total === 0 && (
                <p className="text-xs text-slate-400">
                  Collect articles first before sending a test digest.
                </p>
              )}
              <button
                className="rounded-full border border-slate-200 px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-200"
                onClick={() => runPipelineMutation.mutate()}
                disabled={runPipelineMutation.isPending || pipelinePolling}
              >
                {pipelinePolling ? "Running..." : runPipelineMutation.isPending ? "Starting..." : "Run pipeline"}
              </button>
              {pipelinePolling && (
                <p className="text-xs text-blue-500">
                  Collecting and processing articles. This may take a few minutes...
                </p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
