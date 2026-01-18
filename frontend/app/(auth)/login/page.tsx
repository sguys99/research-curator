"use client";

import { useState } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import MarketingHeader from "@/components/layout/MarketingHeader";
import { requestMagicLink } from "@/lib/api/auth";

const schema = z.object({
  email: z.string().email("유효한 이메일을 입력해주세요."),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (values: FormValues) => {
    setIsSending(true);
    setStatusMessage(null);
    setToken(null);

    try {
      const response = await requestMagicLink(values.email);
      setStatusMessage(response.message);
      if (response.token) {
        setToken(response.token);
      }
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "요청에 실패했습니다. 다시 시도해주세요.",
      );
    } finally {
      setIsSending(false);
    }
  };

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
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <label className="block text-sm font-medium text-slate-700">
              Email address
              <input
                type="email"
                placeholder="you@lab.edu"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                {...register("email")}
              />
            </label>
            {errors.email ? (
              <p className="text-xs text-red-500">{errors.email.message}</p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={isSending}
            >
              {isSending ? "Sending..." : "Send login link"}
            </button>
          </form>
          {statusMessage ? (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
              {statusMessage}
              {token ? (
                <div className="mt-3">
                  <p className="font-semibold text-slate-700">Dev token</p>
                  <p className="mt-1 break-all text-[11px] text-slate-500">{token}</p>
                  <Link
                    href={`/verify?token=${token}`}
                    className="mt-2 inline-flex text-xs font-semibold text-blue-600"
                  >
                    Verify now →
                  </Link>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
              Local dev tip: use the printed token to complete login without email delivery.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
