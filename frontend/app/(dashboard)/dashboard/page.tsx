const stats = [
  { label: "Articles tracked", value: "1,248" },
  { label: "Digests sent", value: "86" },
  { label: "Avg. rating", value: "4.6 / 5" },
];

const digests = [
  { title: "LLM Research Weekly", items: 12, score: 91 },
  { title: "AI Policy Watch", items: 7, score: 88 },
  { title: "Startup Signals", items: 9, score: 84 },
];

export default function DashboardPage() {
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
            <h2 className="font-display text-xl font-semibold text-slate-900">
              Recent digests
            </h2>
            <button className="text-sm font-medium text-blue-600">View all</button>
          </div>
          <div className="mt-6 space-y-4">
            {digests.map((digest) => (
              <div
                key={digest.title}
                className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-900">{digest.title}</p>
                  <p className="text-xs text-slate-500">{digest.items} items curated</p>
                </div>
                <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                  Score {digest.score}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Scheduler status</h3>
            <p className="mt-3 text-sm text-slate-500">
              Last run 02:10 KST • Next run 08:00 KST
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs text-emerald-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Healthy
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Quick actions</h3>
            <div className="mt-4 flex flex-col gap-3 text-sm">
              <button className="rounded-full bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700">
                Send test digest
              </button>
              <button className="rounded-full border border-slate-200 px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50">
                Trigger collection job
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
