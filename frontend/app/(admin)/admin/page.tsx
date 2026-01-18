"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import AuthGuard from "@/components/auth/AuthGuard";
import { useAuth } from "@/hooks/use-auth";
import { getArticleStatistics, getArticles } from "@/lib/api/articles";
import { getSchedulerStatus } from "@/lib/api/scheduler";
import { getUserDigests } from "@/lib/api/users";
import type { Article } from "@/types/articles";
import type { Digest } from "@/types/digests";

type TabKey = "overview" | "users" | "articles" | "digests";

const tabs: { key: TabKey; label: string }[] = [
  { key: "overview", label: "System overview" },
  { key: "users", label: "Users" },
  { key: "articles", label: "Articles" },
  { key: "digests", label: "Digests" },
];

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function AdminPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  const adminEmails = useMemo(() => {
    const raw = process.env.NEXT_PUBLIC_ADMIN_EMAILS ?? "";
    const list = raw
      .split(",")
      .map((email) => email.trim())
      .filter(Boolean);
    return list.length ? list : ["sguys99@gmail.com"];
  }, []);

  const isAdmin = Boolean(user?.email && adminEmails.includes(user.email));

  const statsQuery = useQuery({
    queryKey: ["admin", "article-stats"],
    queryFn: getArticleStatistics,
    enabled: isAdmin,
  });

  const schedulerQuery = useQuery({
    queryKey: ["admin", "scheduler-status"],
    queryFn: getSchedulerStatus,
    enabled: isAdmin,
    refetchInterval: 60_000,
  });

  const articlesQuery = useQuery({
    queryKey: ["admin", "articles"],
    queryFn: () => getArticles({ skip: 0, limit: 20 }),
    enabled: isAdmin,
  });

  const digestsQuery = useQuery({
    queryKey: ["admin", "digests", user?.id],
    queryFn: () => getUserDigests(user?.id ?? ""),
    enabled: isAdmin && Boolean(user?.id),
  });

  const articles = articlesQuery.data?.articles ?? [];
  const digests = digestsQuery.data?.digests ?? [];

  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto w-full max-w-6xl px-6 py-10">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="font-display text-2xl font-semibold text-slate-900">
                Admin overview
              </h1>
              <p className="mt-2 text-sm text-slate-500">
                Monitor system health and operational data.
              </p>
            </div>
            <Link
              href="/dashboard"
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"
            >
              Back to dashboard
            </Link>
          </div>

          {!isAdmin && (
            <div className="mt-8 rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
              Admin access required. Contact an administrator to update
              `NEXT_PUBLIC_ADMIN_EMAILS`.
            </div>
          )}

          {isAdmin && (
            <>
              <div className="mt-8 flex flex-wrap gap-2 rounded-full bg-white p-1 text-sm">
                {tabs.map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className={`rounded-full px-4 py-2 transition ${
                      activeTab === tab.key
                        ? "bg-slate-900 text-white"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {activeTab === "overview" && (
                <div className="mt-6 space-y-6">
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <p className="text-sm text-slate-500">Total users</p>
                      <p className="mt-3 text-2xl font-semibold text-slate-900">N/A</p>
                      <p className="mt-2 text-xs text-slate-400">Requires admin API</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <p className="text-sm text-slate-500">Articles</p>
                      <p className="mt-3 text-2xl font-semibold text-slate-900">
                        {statsQuery.data?.total ?? "-"}
                      </p>
                      <p className="mt-2 text-xs text-slate-400">From article statistics</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <p className="text-sm text-slate-500">Digests sent</p>
                      <p className="mt-3 text-2xl font-semibold text-slate-900">N/A</p>
                      <p className="mt-2 text-xs text-slate-400">Requires admin API</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <p className="text-sm text-slate-500">Feedback total</p>
                      <p className="mt-3 text-2xl font-semibold text-slate-900">N/A</p>
                      <p className="mt-2 text-xs text-slate-400">Requires admin API</p>
                    </div>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <h2 className="text-sm font-semibold text-slate-700">
                        Article distribution
                      </h2>
                      {statsQuery.isLoading ? (
                        <p className="mt-3 text-sm text-slate-500">Loading stats...</p>
                      ) : (
                        <div className="mt-4 grid gap-4 md:grid-cols-2">
                          <div>
                            <p className="text-xs font-semibold text-slate-600">By source</p>
                            <div className="mt-2 space-y-2 text-sm text-slate-700">
                              {Object.entries(statsQuery.data?.by_source_type ?? {}).map(
                                ([source, count]) => (
                                  <div key={source} className="flex items-center justify-between">
                                    <span>{source}</span>
                                    <span className="text-slate-500">{count}</span>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-slate-600">By category</p>
                            <div className="mt-2 space-y-2 text-sm text-slate-700">
                              {Object.entries(statsQuery.data?.by_category ?? {}).map(
                                ([category, count]) => (
                                  <div
                                    key={category}
                                    className="flex items-center justify-between"
                                  >
                                    <span>{category}</span>
                                    <span className="text-slate-500">{count}</span>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                      <h2 className="text-sm font-semibold text-slate-700">Scheduler status</h2>
                      {schedulerQuery.isLoading ? (
                        <p className="mt-3 text-sm text-slate-500">Loading scheduler...</p>
                      ) : schedulerQuery.data ? (
                        <div className="mt-3 space-y-3 text-sm text-slate-600">
                          <p>
                            Status:{" "}
                            <span className="font-medium text-slate-900">
                              {schedulerQuery.data.running ? "Running" : "Stopped"}
                            </span>
                          </p>
                          <p>Timezone: {schedulerQuery.data.timezone}</p>
                          <p>Current time: {schedulerQuery.data.current_time}</p>
                          <div>
                            <p className="text-xs font-semibold text-slate-500">Jobs</p>
                            <div className="mt-2 space-y-2 text-xs text-slate-600">
                              {schedulerQuery.data.jobs.map((job) => (
                                <div
                                  key={job.id}
                                  className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2"
                                >
                                  <p className="font-medium text-slate-700">{job.name}</p>
                                  <p>Next run: {job.next_run_time ?? "N/A"}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="mt-3 text-sm text-slate-500">Scheduler unavailable.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "users" && (
                <div className="mt-6 space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                    <h2 className="text-sm font-semibold text-slate-700">Admin allowlist</h2>
                    <p className="mt-2 text-sm text-slate-500">
                      Manage admin access via `NEXT_PUBLIC_ADMIN_EMAILS`.
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                      {adminEmails.map((email) => (
                        <span
                          key={email}
                          className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1"
                        >
                          {email}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                    <h3 className="text-sm font-semibold text-slate-700">Current user</h3>
                    <div className="mt-4 grid gap-4 md:grid-cols-3 text-sm text-slate-600">
                      <div>
                        <p className="text-xs text-slate-400">Email</p>
                        <p className="font-medium text-slate-800">{user?.email ?? "-"}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">User ID</p>
                        <p className="font-medium text-slate-800">{user?.id ?? "-"}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Last login</p>
                        <p className="font-medium text-slate-800">
                          {formatDateTime(user?.last_login)}
                        </p>
                      </div>
                    </div>
                    <p className="mt-4 text-xs text-slate-400">
                      Full user listing requires a dedicated admin API endpoint.
                    </p>
                  </div>
                </div>
              )}

              {activeTab === "articles" && (
                <div className="mt-6 space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <h2 className="text-sm font-semibold text-slate-700">Recent articles</h2>
                      <span className="text-xs text-slate-500">
                        Showing {articles.length} items
                      </span>
                    </div>
                    {articlesQuery.isLoading ? (
                      <p className="mt-4 text-sm text-slate-500">Loading articles...</p>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {articles.map((article: Article) => (
                          <div
                            key={article.id}
                            className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div>
                                <p className="text-sm font-semibold text-slate-900">
                                  {article.title}
                                </p>
                                <p className="text-xs text-slate-500">
                                  {article.source_type} · {article.category ?? "Uncategorized"}
                                </p>
                              </div>
                              <div className="text-xs text-slate-600">
                                Score {article.importance_score.toFixed(2)}
                              </div>
                            </div>
                            {article.summary && (
                              <p className="mt-2 text-xs text-slate-600">
                                {article.summary}
                              </p>
                            )}
                          </div>
                        ))}
                        {articles.length === 0 && (
                          <p className="text-sm text-slate-500">No articles available.</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "digests" && (
                <div className="mt-6 space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                    <h2 className="text-sm font-semibold text-slate-700">Digest history</h2>
                    <p className="mt-2 text-sm text-slate-500">
                      Showing your digests. Global history requires admin API support.
                    </p>
                    {digestsQuery.isLoading ? (
                      <p className="mt-4 text-sm text-slate-500">Loading digests...</p>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {digests.map((digest: Digest) => (
                          <div
                            key={digest.id}
                            className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div>
                                <p className="text-sm font-semibold text-slate-900">
                                  Digest {digest.id}
                                </p>
                                <p className="text-xs text-slate-500">
                                  Sent {formatDateTime(digest.sent_at)}
                                </p>
                              </div>
                              <div className="text-xs text-slate-600">
                                Articles {digest.article_ids.length}
                              </div>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                              Opened: {digest.email_opened ? "Yes" : "No"}
                            </p>
                          </div>
                        ))}
                        {digests.length === 0 && (
                          <p className="text-sm text-slate-500">No digests found.</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
