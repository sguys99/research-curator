"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { verifyMagicLink } from "@/lib/api/auth";
import { useAuthStore } from "@/stores/auth-store";

export default function VerifyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [error, setError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    if (!token) {
      setError("토큰을 찾을 수 없습니다. 다시 로그인해주세요.");
      return;
    }

    const verify = async () => {
      setIsVerifying(true);
      setError(null);
      try {
        const response = await verifyMagicLink(token);
        setToken(response.access_token);
        setUser(response.user);
        router.replace("/onboarding");
      } catch (err) {
        setError(err instanceof Error ? err.message : "검증에 실패했습니다.");
      } finally {
        setIsVerifying(false);
      }
    };

    void verify();
  }, [router, setToken, setUser, token]);

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="page-fade mx-auto flex w-full max-w-6xl items-center justify-center px-6 py-20">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-medium text-blue-600">Verifying token</p>
          <h1 className="font-display mt-3 text-2xl font-semibold text-slate-900">
            Confirming your access
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            {isVerifying
              ? "This page will validate the magic link and redirect you to the dashboard."
              : "Verification completed."}
          </p>
          {error ? (
            <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-600">
              {error}
            </div>
          ) : null}
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
