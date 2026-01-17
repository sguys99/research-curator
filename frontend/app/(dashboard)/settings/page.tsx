export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-semibold text-slate-900">Preferences</h2>
        <p className="mt-2 text-sm text-slate-500">
          Customize research focus, delivery time, and content mix.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Research fields
            <input
              placeholder="AI, NLP, Computer Vision"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </label>
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Keywords
            <input
              placeholder="transformer, agentic, alignment"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </label>
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Delivery time (KST)
            <input
              type="time"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </label>
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Daily limit
            <input
              type="number"
              placeholder="10"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </label>
        </div>
        <div className="mt-6 flex flex-wrap gap-2 text-xs text-slate-500">
          {["Papers 50%", "News 30%", "Reports 20%"].map((ratio) => (
            <span
              key={ratio}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1"
            >
              {ratio}
            </span>
          ))}
        </div>
        <div className="mt-6 flex gap-3">
          <button className="rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white">
            Save changes
          </button>
          <button className="rounded-full border border-slate-200 px-6 py-3 text-sm font-medium text-slate-700">
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
