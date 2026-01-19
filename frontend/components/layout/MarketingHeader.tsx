"use client";

import Image from "next/image";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";

const navItems = [
  { label: "About", href: "#about" },
  { label: "Workflow", href: "#workflow" },
  { label: "Contact", href: "#contact" },
];

export default function MarketingHeader() {
  const { user } = useAuth();
  const { clearAuth, hydrated } = useAuthStore();
  const queryClient = useQueryClient();

  const handleLogout = () => {
    clearAuth();
    // React Query 캐시 초기화 (인증 관련 쿼리)
    queryClient.removeQueries({ queryKey: ["auth"] });
  };

  // 인증 버튼 영역 렌더링
  const renderAuthButtons = () => {
    // hydration 전에는 기본 버튼 표시 (깜빡임 방지)
    if (!hydrated) {
      return (
        <>
          <Link
            href="/login"
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="hidden rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 md:inline-flex"
          >
            Get started
          </Link>
        </>
      );
    }

    // 인증된 사용자
    if (user) {
      return (
        <>
          <span className="hidden text-sm text-slate-600 md:block">{user.email}</span>
          <Link
            href="/dashboard"
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="hidden rounded-full bg-slate-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 md:inline-flex"
          >
            Logout
          </button>
        </>
      );
    }

    // 미인증 사용자
    return (
      <>
        <Link
          href="/login"
          className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          Sign in
        </Link>
        <Link
          href="/dashboard"
          className="hidden rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 md:inline-flex"
        >
          Get started
        </Link>
      </>
    );
  };

  return (
    <header className="sticky top-0 z-30 border-b border-transparent bg-white/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <Image
            src="/images/icon.png"
            alt="Research Curator"
            width={36}
            height={36}
            className="rounded-xl"
          />
          <span className="font-display">Research Curator</span>
        </Link>
        <nav className="hidden items-center gap-2 rounded-full bg-slate-100 p-1 text-sm md:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="rounded-full px-4 py-2 text-slate-600 transition-colors hover:text-slate-900"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">{renderAuthButtons()}</div>
      </div>
    </header>
  );
}
