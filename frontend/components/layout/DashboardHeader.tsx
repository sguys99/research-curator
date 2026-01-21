"use client";

import { useCallback, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/hooks/use-auth";
import { useClickOutside } from "@/hooks/use-click-outside";
import { useAuthStore } from "@/stores/auth-store";

const baseNavItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Search", href: "/search" },
  { label: "Settings", href: "/settings" },
  { label: "Feedback", href: "/feedback" },
];

export default function DashboardHeader() {
  const { user } = useAuth();
  const { clearAuth } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const adminEmails = (process.env.NEXT_PUBLIC_ADMIN_EMAILS ?? "")
    .split(",")
    .map((email) => email.trim())
    .filter(Boolean);
  const fallbackAdmins = adminEmails.length ? adminEmails : ["sguys99@gmail.com"];
  const isAdmin = Boolean(user?.email && fallbackAdmins.includes(user.email));
  const navItems = isAdmin
    ? [...baseNavItems, { label: "Admin", href: "/admin" }]
    : baseNavItems;

  // 드롭다운 외부 클릭 시 닫기
  const closeDropdown = useCallback(() => setDropdownOpen(false), []);
  useClickOutside(dropdownRef, closeDropdown, dropdownOpen);

  const handleLogout = () => {
    clearAuth();
    // React Query 캐시 초기화 (인증 관련 쿼리)
    queryClient.removeQueries({ queryKey: ["auth"] });
    setDropdownOpen(false);
    router.push("/");
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto w-full max-w-6xl px-6 py-4">
        <div className="flex items-center justify-between">
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
        <nav className="hidden items-center gap-1 rounded-full bg-slate-100 p-1 text-sm md:flex">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`rounded-full px-4 py-2 transition-colors ${
                  isActive
                    ? "bg-white font-semibold text-slate-900 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-2">
          {/* 사용자 드롭다운 메뉴 */}
          <div ref={dropdownRef} className="relative hidden md:block">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              <span className="max-w-[200px] truncate">{user?.email ?? "User"}</span>
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
          {/* 모바일 메뉴 버튼 */}
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-full border border-slate-200 px-3 py-2 text-sm md:hidden"
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
          >
            Menu
          </button>
        </div>
        </div>
        {menuOpen && (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 md:hidden">
            <nav id="mobile-nav" className="grid gap-2 text-sm text-slate-700">
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    className={`rounded-xl px-3 py-2 ${
                      isActive
                        ? "bg-white font-semibold text-slate-900"
                        : "text-slate-700 hover:bg-white"
                    }`}
                    onClick={() => setMenuOpen(false)}
                  >
                    {item.label}
                  </Link>
                );
              })}
              {/* 모바일: 사용자 정보 및 로그아웃 */}
              <div className="mt-2 border-t border-slate-200 pt-2">
                <span className="block px-3 py-2 text-slate-500">{user?.email ?? "User"}</span>
                <button
                  onClick={handleLogout}
                  className="w-full rounded-xl px-3 py-2 text-left text-red-600 hover:bg-white"
                >
                  Logout
                </button>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
