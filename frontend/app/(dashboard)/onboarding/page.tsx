const steps = [
  "Research fields",
  "Focus keywords",
  "Content mix",
  "Delivery time",
  "Daily limit",
];

export default function OnboardingPage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold text-slate-900">
            AI onboarding assistant
          </h2>
          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            Step 2 / 5
          </span>
        </div>
        <div className="mt-6 space-y-4">
          <div className="max-w-sm rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-700">
            Tell me about your research focus areas.
          </div>
          <div className="ml-auto max-w-sm rounded-2xl bg-blue-600 px-4 py-3 text-sm text-white">
            LLMs, multimodal systems, and AI policy updates.
          </div>
          <div className="max-w-sm rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-700">
            Great. Now pick a few keywords for daily tracking.
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          {["transformer", "agentic", "alignment", "inference"].map((chip) => (
            <button
              key={chip}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs text-slate-600 transition-colors hover:bg-slate-50"
            >
              {chip}
            </button>
          ))}
        </div>
        <div className="mt-6 flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3">
          <input
            placeholder="Type a response..."
            className="flex-1 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
          />
          <button className="rounded-full bg-blue-600 px-4 py-2 text-xs font-medium text-white">
            Send
          </button>
        </div>
      </section>

      <aside className="space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700">Progress</h3>
          <ul className="mt-4 space-y-2 text-sm text-slate-600">
            {steps.map((step, index) => (
              <li key={step} className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    index < 1 ? "bg-emerald-500" : "bg-slate-300"
                  }`}
                />
                {step}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700">Preview</h3>
          <p className="mt-3 text-sm text-slate-500">
            Preferences summary will appear here after onboarding.
          </p>
          <div className="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-xs text-slate-400">
            Awaiting more answers...
          </div>
        </div>
      </aside>
    </div>
  );
}
