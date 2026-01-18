export default function GlobalLoading() {
  return (
    <div className="min-h-screen bg-slate-50 px-6 py-16">
      <div className="mx-auto w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-medium text-blue-600">Loading</p>
        <h2 className="mt-3 font-display text-2xl font-semibold text-slate-900">
          Preparing your workspace
        </h2>
        <p className="mt-2 text-sm text-slate-500">Just a moment while we fetch data.</p>
      </div>
    </div>
  );
}
