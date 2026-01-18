"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";

import { useAuth } from "@/hooks/use-auth";
import {
  createFeedback,
  deleteFeedback,
  getArticleFeedbackStats,
  getUserFeedback,
  updateFeedback,
} from "@/lib/api/feedback";
import type { Feedback, FeedbackStatsResponse } from "@/types/feedback";

const createSchema = z.object({
  articleId: z.string().min(1, "Article ID is required."),
  rating: z.coerce.number().min(1).max(5),
  comment: z.string().max(1000).optional(),
});

type CreateFormValues = z.infer<typeof createSchema>;

type EditState = {
  id: string;
  rating: number;
  comment: string;
} | null;

const statsSchema = z.object({
  articleId: z.string().min(1, "Enter an article ID."),
});

type StatsFormValues = z.infer<typeof statsSchema>;

const formatDate = (value?: string) => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString();
};

export default function FeedbackPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState>(null);
  const [stats, setStats] = useState<FeedbackStatsResponse | null>(null);

  const createForm = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      articleId: "",
      rating: 5,
      comment: "",
    },
  });

  const statsForm = useForm<StatsFormValues>({
    resolver: zodResolver(statsSchema),
    defaultValues: {
      articleId: "",
    },
  });

  const feedbackQuery = useQuery({
    queryKey: ["feedback", "user", user?.id],
    queryFn: () => getUserFeedback(user?.id ?? "", 0, 50),
    enabled: Boolean(user?.id),
  });

  const createMutation = useMutation({
    mutationFn: createFeedback,
    onSuccess: () => {
      setStatusMessage("Feedback submitted.");
      createForm.reset({ articleId: "", rating: 5, comment: "" });
      queryClient.invalidateQueries({ queryKey: ["feedback", "user", user?.id] });
    },
    onError: () => setStatusMessage("Unable to submit feedback."),
  });

  const updateMutation = useMutation({
    mutationFn: (values: { feedbackId: string; payload: { rating?: number; comment?: string } }) =>
      updateFeedback(values.feedbackId, values.payload),
    onSuccess: () => {
      setStatusMessage("Feedback updated.");
      setEditState(null);
      queryClient.invalidateQueries({ queryKey: ["feedback", "user", user?.id] });
    },
    onError: () => setStatusMessage("Unable to update feedback."),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFeedback,
    onSuccess: () => {
      setStatusMessage("Feedback removed.");
      queryClient.invalidateQueries({ queryKey: ["feedback", "user", user?.id] });
    },
    onError: () => setStatusMessage("Unable to delete feedback."),
  });

  const statsMutation = useMutation({
    mutationFn: getArticleFeedbackStats,
    onSuccess: (data) => {
      setStats(data);
    },
  });

  const feedbackItems = useMemo(
    () => feedbackQuery.data?.feedback ?? [],
    [feedbackQuery.data?.feedback],
  );
  const averageRating = useMemo(() => {
    if (!feedbackItems.length) {
      return 0;
    }
    const total = feedbackItems.reduce((sum, item) => sum + item.rating, 0);
    return total / feedbackItems.length;
  }, [feedbackItems]);

  const onSubmit = (values: CreateFormValues) => {
    setStatusMessage(null);
    createMutation.mutate({
      article_id: values.articleId,
      rating: values.rating,
      comment: values.comment?.trim() || undefined,
    });
  };

  const onEditSave = () => {
    if (!editState) {
      return;
    }
    setStatusMessage(null);
    updateMutation.mutate({
      feedbackId: editState.id,
      payload: { rating: editState.rating, comment: editState.comment.trim() || undefined },
    });
  };

  const onStatsSubmit = (values: StatsFormValues) => {
    statsMutation.mutate(values.articleId);
  };

  const startEdit = (feedback: Feedback) => {
    setEditState({
      id: feedback.id,
      rating: feedback.rating,
      comment: feedback.comment ?? "",
    });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-semibold text-slate-900">Feedback</h2>
        <p className="mt-2 text-sm text-slate-500">
          Share ratings and notes to improve future digests.
        </p>

        <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={createForm.handleSubmit(onSubmit)}>
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Article ID
            <input
              {...createForm.register("articleId")}
              placeholder="UUID or article identifier"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
            {createForm.formState.errors.articleId && (
              <span className="text-xs text-rose-500">
                {createForm.formState.errors.articleId.message}
              </span>
            )}
          </label>
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Rating
            <select
              {...createForm.register("rating")}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
              {[5, 4, 3, 2, 1].map((value) => (
                <option key={value} value={value}>
                  {value} / 5
                </option>
              ))}
            </select>
          </label>
          <label className="md:col-span-2 space-y-2 text-sm font-medium text-slate-700">
            Comment (optional)
            <textarea
              {...createForm.register("comment")}
              rows={4}
              placeholder="What should we improve?"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </label>
          <div className="md:col-span-2 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {createMutation.isPending ? "Submitting..." : "Submit feedback"}
            </button>
            {statusMessage && <span className="text-sm text-slate-600">{statusMessage}</span>}
          </div>
        </form>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-700">Recent feedback</h3>
            <p className="text-xs text-slate-500">
              {feedbackItems.length} items, average rating {averageRating.toFixed(2)}
            </p>
          </div>
        </div>
        {feedbackQuery.isLoading ? (
          <p className="mt-4 text-sm text-slate-500">Loading feedback...</p>
        ) : feedbackItems.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No feedback yet.</p>
        ) : (
          <div className="mt-4 space-y-4">
            {feedbackItems.map((item) => {
              const isEditing = editState?.id === item.id;
              return (
                <div
                  key={item.id}
                  className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4 text-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-900">Article {item.article_id}</p>
                      <p className="text-xs text-slate-500">Submitted {formatDate(item.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-blue-600">
                      Rating {item.rating} / 5
                    </div>
                  </div>
                  {!isEditing && (
                    <p className="mt-3 text-xs text-slate-600">
                      {item.comment || "No comment"}
                    </p>
                  )}

                  {isEditing && (
                    <div className="mt-3 grid gap-3 md:grid-cols-[160px_1fr]">
                      <label className="space-y-2 text-xs font-medium text-slate-600">
                        Rating
                        <select
                          value={editState?.rating ?? 3}
                          onChange={(event) =>
                            setEditState((prev) =>
                              prev ? { ...prev, rating: Number(event.target.value) } : prev,
                            )
                          }
                          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                        >
                          {[5, 4, 3, 2, 1].map((value) => (
                            <option key={value} value={value}>
                              {value} / 5
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-2 text-xs font-medium text-slate-600">
                        Comment
                        <textarea
                          rows={3}
                          value={editState?.comment ?? ""}
                          onChange={(event) =>
                            setEditState((prev) =>
                              prev ? { ...prev, comment: event.target.value } : prev,
                            )
                          }
                          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                        />
                      </label>
                    </div>
                  )}

                  <div className="mt-4 flex flex-wrap gap-2">
                    {isEditing ? (
                      <>
                        <button
                          type="button"
                          onClick={onEditSave}
                          disabled={updateMutation.isPending}
                          className="rounded-full bg-blue-600 px-4 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:bg-blue-400"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditState(null)}
                          className="rounded-full border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => startEdit(item)}
                          className="rounded-full border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteMutation.mutate(item.id)}
                          disabled={deleteMutation.isPending}
                          className="rounded-full border border-rose-200 px-4 py-2 text-xs font-medium text-rose-600"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Article feedback stats</h3>
        <p className="mt-1 text-xs text-slate-500">
          Lookup rating distribution for a specific article.
        </p>
        <form
          className="mt-4 flex flex-wrap items-end gap-3"
          onSubmit={statsForm.handleSubmit(onStatsSubmit)}
        >
          <label className="flex-1 space-y-2 text-sm font-medium text-slate-700">
            Article ID
            <input
              {...statsForm.register("articleId")}
              placeholder="UUID or article identifier"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
            {statsForm.formState.errors.articleId && (
              <span className="text-xs text-rose-500">
                {statsForm.formState.errors.articleId.message}
              </span>
            )}
          </label>
          <button
            type="submit"
            disabled={statsMutation.isPending}
            className="rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white"
          >
            {statsMutation.isPending ? "Loading..." : "Fetch stats"}
          </button>
        </form>
        {stats && (
          <div className="mt-4 grid gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs text-slate-500">Total feedback</span>
              <span className="text-sm font-semibold text-slate-900">{stats.count}</span>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs text-slate-500">Average rating</span>
              <span className="text-sm font-semibold text-slate-900">
                {stats.average_rating.toFixed(2)} / 5
              </span>
            </div>
            <div className="space-y-2">
              <span className="text-xs font-medium text-slate-600">Distribution</span>
              <div className="grid gap-2 md:grid-cols-5">
                {[5, 4, 3, 2, 1].map((rating) => (
                  <div
                    key={rating}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-center"
                  >
                    <p className="text-xs text-slate-500">{rating} / 5</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {stats.rating_distribution?.[String(rating)] ?? 0}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
