export default function SearchPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-xl font-semibold text-slate-900">Search</h2>
        <p className="mt-2 text-sm text-slate-500">
          Run semantic or keyword searches across the curated archive.
        </p>
        <div className="mt-4 flex flex-col gap-3 md:flex-row">
          <input
            placeholder="Search papers, keywords, or authors"
            className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
          <button className="rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white">
            Search
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
          {["Papers", "News", "Reports", "High importance", "Last 7 days"].map((filter) => (
            <span
              key={filter}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1"
            >
              {filter}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {["On-device LLM optimizations", "Global AI policy tracker"].map((title) => (
          <div
            key={title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-sm font-semibold text-slate-900">{title}</p>
            <p className="mt-2 text-sm text-slate-600">
              Summary placeholder for semantic search results with relevance score and tags.
            </p>
            <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
              <span>Score 0.86 • arXiv</span>
              <button className="font-medium text-blue-600">View details</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
