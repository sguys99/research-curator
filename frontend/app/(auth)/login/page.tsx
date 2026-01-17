import MarketingHeader from "@/components/layout/MarketingHeader";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <MarketingHeader />
      <main className="page-fade mx-auto flex w-full max-w-6xl items-center justify-center px-6 py-20">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-6 text-center">
            <p className="text-sm font-medium text-blue-600">Magic Link Login</p>
            <h1 className="font-display mt-3 text-2xl font-semibold text-slate-900">
              Sign in to your digest
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Receive a one-time login link by email.
            </p>
          </div>
          <form className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Email address
              <input
                type="email"
                placeholder="you@lab.edu"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </label>
            <button
              type="button"
              className="w-full rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Send login link
            </button>
          </form>
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
            Local dev tip: use the printed token to complete login without email delivery.
          </div>
        </div>
      </main>
    </div>
  );
}
