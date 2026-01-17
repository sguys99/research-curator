const stats = [
  { label: "Total users", value: "142" },
  { label: "Articles", value: "6,230" },
  { label: "Digests", value: "412" },
  { label: "Feedback", value: "1,004" },
];

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <h1 className="font-display text-2xl font-semibold text-slate-900">
          Admin overview
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Monitor system health and user activity.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <p className="text-sm text-slate-500">{stat.label}</p>
              <p className="mt-3 text-2xl font-semibold text-slate-900">{stat.value}</p>
            </div>
          ))}
        </div>
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700">Scheduler status</h2>
          <p className="mt-3 text-sm text-slate-500">
            All background jobs completed successfully in the last 24 hours.
          </p>
        </div>
      </div>
    </div>
  );
}
