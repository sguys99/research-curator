const feedbackItems = [
  { title: "LLM safety roundup", rating: 5, note: "Perfectly scoped summary." },
  { title: "Vision benchmarks", rating: 4, note: "Include more datasets next time." },
];

export default function FeedbackPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-semibold text-slate-900">Feedback</h2>
        <p className="mt-2 text-sm text-slate-500">
          Share ratings and notes to tune future digests.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <button className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm">
            ⭐⭐⭐⭐⭐ Submit digest feedback
          </button>
          <button className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm">
            ⭐⭐⭐⭐ Request deeper coverage
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Recent feedback</h3>
        <div className="mt-4 space-y-4">
          {feedbackItems.map((item) => (
            <div
              key={item.title}
              className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm"
            >
              <div>
                <p className="font-semibold text-slate-900">{item.title}</p>
                <p className="text-xs text-slate-500">{item.note}</p>
              </div>
              <span className="text-xs font-medium text-blue-600">{item.rating} / 5</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
