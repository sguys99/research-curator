import Link from "next/link";

export default function VerifyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <main className="page-fade mx-auto flex w-full max-w-6xl items-center justify-center px-6 py-20">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-medium text-blue-600">Verifying token</p>
          <h1 className="font-display mt-3 text-2xl font-semibold text-slate-900">
            Confirming your access
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            This page will validate the magic link and redirect you to the dashboard.
          </p>
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
            If verification stalls, return to{" "}
            <Link href="/login" className="font-medium text-blue-600">
              login
            </Link>{" "}
            and request a new link.
          </div>
        </div>
      </main>
    </div>
  );
}
