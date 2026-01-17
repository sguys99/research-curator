import Link from "next/link";
import MarketingHeader from "@/components/layout/MarketingHeader";

export default function Home() {
  const features = [
    {
      title: "Automated collection",
      description: "Pull new papers, news, and reports from curated sources every day.",
    },
    {
      title: "LLM summaries",
      description: "Summarize and rank items in Korean with transparent importance scores.",
    },
    {
      title: "Semantic search",
      description: "Rediscover past insights with vector search powered by Qdrant.",
    },
    {
      title: "Digest delivery",
      description: "Send curated HTML digests on a daily schedule or on demand.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <MarketingHeader />
      <main className="page-fade">
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_#dbeafe_0%,_transparent_55%),_radial-gradient(circle_at_bottom,_#fde7f3_0%,_transparent_50%)]" />
          <div className="absolute -left-10 top-24 h-40 w-40 rounded-full bg-blue-100/70 blur-3xl" />
          <div className="absolute right-10 top-10 h-32 w-32 rounded-full bg-indigo-100/80 blur-2xl float-slow" />
          <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-20 lg:flex-row lg:items-center">
            <div className="flex-1 space-y-6">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm">
                AI Research Concierge
              </p>
              <h1 className="font-display text-4xl font-semibold leading-tight text-slate-900 md:text-5xl">
                Curate the research you actually need, delivered on schedule.
              </h1>
              <p className="max-w-xl text-lg text-slate-600">
                Research Curator blends automated crawling, LLM summarization, and semantic
                retrieval so your team stays ahead without manual triage.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  Start with magic link
                </Link>
                <Link
                  href="#workflow"
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  See the workflow
                </Link>
              </div>
            </div>
            <div className="flex-1">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-500">Daily Digest</p>
                  <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                    08:00 KST
                  </span>
                </div>
                <div className="mt-6 space-y-4">
                  {["LLM Trends", "Multimodal Benchmarks", "Funding Signals"].map((item) => (
                    <div
                      key={item}
                      className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{item}</p>
                        <p className="text-xs text-slate-500">3 highlights • top score 92</p>
                      </div>
                      <span className="text-xs font-medium text-slate-500">View</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="about" className="mx-auto w-full max-w-6xl px-6 py-16">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
            <div className="space-y-4">
              <h2 className="font-display text-3xl font-semibold text-slate-900">
                A focused pipeline from signal to summary.
              </h2>
              <p className="text-slate-600">
                Configure sources, define relevance, and let the system handle collection,
                summarization, and delivery so your team can act faster.
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold text-slate-700">Typical stack</p>
              <div className="mt-4 flex flex-wrap gap-2 text-sm text-slate-600">
                {["FastAPI", "PostgreSQL", "Qdrant", "LiteLLM", "Streamlit", "APScheduler"].map(
                  (item) => (
                    <span
                      key={item}
                      className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1"
                    >
                      {item}
                    </span>
                  ),
                )}
              </div>
            </div>
          </div>
        </section>

        <section id="workflow" className="mx-auto w-full max-w-6xl px-6 pb-20">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-3xl font-semibold text-slate-900">
              Built for research workflows
            </h2>
            <Link href="/dashboard" className="text-sm font-medium text-blue-600">
              Explore dashboard →
            </Link>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  ✦
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="contact" className="mx-auto w-full max-w-6xl px-6 pb-24">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="font-display text-2xl font-semibold text-slate-900">
                  Ready to set up your first digest?
                </h3>
                <p className="mt-2 text-sm text-slate-600">
                  Connect your data sources and personalize the schedule in minutes.
                </p>
              </div>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
              >
                Request access
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
