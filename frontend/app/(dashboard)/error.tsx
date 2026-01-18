"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <p className="text-sm font-medium text-rose-600">Dashboard error</p>
      <h2 className="mt-3 font-display text-xl font-semibold text-slate-900">
        We could not load this section
      </h2>
      <p className="mt-2 text-sm text-slate-500">
        {error.message || "Please retry in a moment."}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-full bg-slate-900 px-6 py-3 text-sm font-medium text-white"
      >
        Retry
      </button>
    </div>
  );
}
