"use client";

import { useEffect, useMemo } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { z } from "zod";

import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";
import { getUserPreferences, updateUserPreferences } from "@/lib/api/users";
import type { UserPreferences } from "@/types/user";

const preferencesSchema = z
  .object({
    researchFields: z.string().optional(),
    keywords: z.string().optional(),
    sources: z.string().optional(),
    paperRatio: z.coerce.number().min(0).max(100),
    newsRatio: z.coerce.number().min(0).max(100),
    reportRatio: z.coerce.number().min(0).max(100),
    emailTime: z.string().regex(/^\d{2}:\d{2}$/, "Use HH:MM format."),
    dailyLimit: z.coerce.number().min(1).max(20),
    emailEnabled: z.boolean(),
  })
  .refine(
    (values) => Math.abs(values.paperRatio + values.newsRatio + values.reportRatio - 100) <= 1,
    {
      message: "Content mix must total 100%.",
      path: ["paperRatio"],
    },
  );

type PreferencesFormValues = z.infer<typeof preferencesSchema>;

const defaultValues: PreferencesFormValues = {
  researchFields: "",
  keywords: "",
  sources: "",
  paperRatio: 40,
  newsRatio: 40,
  reportRatio: 20,
  emailTime: "08:00",
  dailyLimit: 5,
  emailEnabled: true,
};

const parseList = (value: string) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const toPercent = (value: number | undefined) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  return value <= 1 ? Math.round(value * 100) : Math.round(value);
};

const toFormValues = (preferences?: UserPreferences): PreferencesFormValues => {
  if (!preferences) {
    return defaultValues;
  }

  return {
    researchFields: preferences.research_fields?.join(", ") ?? "",
    keywords: preferences.keywords?.join(", ") ?? "",
    sources: preferences.sources?.join(", ") ?? "",
    paperRatio: toPercent(preferences.info_types?.paper),
    newsRatio: toPercent(preferences.info_types?.news),
    reportRatio: toPercent(preferences.info_types?.report),
    emailTime: preferences.email_time ?? defaultValues.emailTime,
    dailyLimit: preferences.daily_limit ?? defaultValues.dailyLimit,
    emailEnabled: preferences.email_enabled ?? defaultValues.emailEnabled,
  };
};

export default function SettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const form = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesSchema),
    defaultValues,
    mode: "onBlur",
  });

  const preferencesQuery = useQuery({
    queryKey: ["users", user?.id, "preferences"],
    queryFn: () => getUserPreferences(user?.id ?? ""),
    enabled: Boolean(user?.id),
  });

  useEffect(() => {
    if (preferencesQuery.data) {
      form.reset(toFormValues(preferencesQuery.data));
    }
  }, [form, preferencesQuery.data]);

  const mutation = useMutation({
    mutationFn: (payload: Partial<UserPreferences>) =>
      updateUserPreferences(user?.id ?? "", payload),
    onSuccess: () =>
      toast({
        title: "Preferences saved",
        description: "Your settings are updated.",
        variant: "success",
      }),
    onError: () =>
      toast({
        title: "Unable to save preferences",
        description: "Check your connection and try again.",
        variant: "error",
      }),
  });

  const [paperRatio, newsRatio, reportRatio] = useWatch({
    control: form.control,
    name: ["paperRatio", "newsRatio", "reportRatio"],
  });

  const ratioSum = useMemo(
    () => (paperRatio ?? 0) + (newsRatio ?? 0) + (reportRatio ?? 0),
    [paperRatio, newsRatio, reportRatio],
  );

  const onSubmit = (values: PreferencesFormValues) => {
    if (!user?.id) {
      toast({
        title: "Login required",
        description: "Please sign in to save preferences.",
        variant: "error",
      });
      return;
    }

    const payload: Partial<UserPreferences> = {
      research_fields: parseList(values.researchFields ?? ""),
      keywords: parseList(values.keywords ?? ""),
      sources: parseList(values.sources ?? ""),
      info_types: {
        paper: values.paperRatio / 100,
        news: values.newsRatio / 100,
        report: values.reportRatio / 100,
      },
      email_time: values.emailTime,
      daily_limit: values.dailyLimit,
      email_enabled: values.emailEnabled,
    };

    mutation.mutate(payload);
  };

  const handleReset = () => {
    form.reset(toFormValues(preferencesQuery.data));
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-semibold text-slate-900">Preferences</h2>
        <p className="mt-2 text-sm text-slate-500">
          Tailor your research focus, content mix, and delivery schedule.
        </p>
        {preferencesQuery.isLoading && (
          <p className="mt-4 text-sm text-slate-500">Loading your preferences...</p>
        )}
        <form className="mt-6 space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Research fields
              <input
                {...form.register("researchFields")}
                placeholder="AI, NLP, Computer Vision"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Keywords
              <input
                {...form.register("keywords")}
                placeholder="transformer, agentic, alignment"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Sources
              <input
                {...form.register("sources")}
                placeholder="arxiv, semantic scholar"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">Content mix</p>
                <p className="text-xs text-slate-500">Set percentages that add up to 100%.</p>
              </div>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
                Total {ratioSum}%
              </span>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="space-y-2 text-sm font-medium text-slate-700">
                Papers (%)
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={5}
                  {...form.register("paperRatio")}
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-slate-700">
                News (%)
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={5}
                  {...form.register("newsRatio")}
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-slate-700">
                Reports (%)
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={5}
                  {...form.register("reportRatio")}
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </label>
            </div>
            {form.formState.errors.paperRatio && (
              <p className="mt-2 text-xs text-rose-500">
                {form.formState.errors.paperRatio.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Delivery time (KST)
              <input
                type="time"
                {...form.register("emailTime")}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Daily limit
              <input
                type="number"
                min={1}
                max={20}
                {...form.register("dailyLimit")}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
            <label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                {...form.register("emailEnabled")}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Enable daily email
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {mutation.isPending ? "Saving..." : "Save changes"}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-full border border-slate-200 px-6 py-3 text-sm font-medium text-slate-700"
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
