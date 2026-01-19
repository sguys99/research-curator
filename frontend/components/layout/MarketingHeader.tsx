"use client";

import { useEffect, useRef, useState } from "react";
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
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    clearAuth();
    queryClient.removeQueries({ queryKey: ["auth"] });
    setDropdownOpen(false);
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

    // 인증된 사용자: Dashboard 버튼 + 드롭다운
    if (user) {
      return (
        <>
          <Link
            href="/dashboard"
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Dashboard
          </Link>
          <div ref={dropdownRef} className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              <span className="hidden max-w-[150px] truncate md:block">{user.email}</span>
              <span className="md:hidden">Account</span>
              <svg
                className={`h-4 w-4 transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {dropdownOpen && (
              <div className="absolute right-0 z-50 mt-2 w-48 rounded-xl border border-slate-200 bg-white py-1 shadow-lg">
                <div className="border-b border-slate-100 px-4 py-2 md:hidden">
                  <span className="text-sm text-slate-500">{user.email}</span>
                </div>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-slate-50"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
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
