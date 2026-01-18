"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-slate-50 px-6 py-16">
      <div className="mx-auto w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-medium text-rose-600">Something went wrong</p>
        <h2 className="mt-3 font-display text-2xl font-semibold text-slate-900">
          We hit an unexpected error
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          {error.message || "Please retry or return to the dashboard."}
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 rounded-full bg-slate-900 px-6 py-3 text-sm font-medium text-white"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
