"use client";

import Link from "next/link";

import { useAuth } from "@/hooks/use-auth";

const baseNavItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Search", href: "/search" },
  { label: "Settings", href: "/settings" },
  { label: "Feedback", href: "/feedback" },
];

export default function DashboardHeader() {
  const { user } = useAuth();
  const adminEmails = (process.env.NEXT_PUBLIC_ADMIN_EMAILS ?? "")
    .split(",")
    .map((email) => email.trim())
    .filter(Boolean);
  const fallbackAdmins = adminEmails.length ? adminEmails : ["sguys99@gmail.com"];
  const isAdmin = Boolean(user?.email && fallbackAdmins.includes(user.email));
  const navItems = isAdmin
    ? [...baseNavItems, { label: "Admin", href: "/admin" }]
    : baseNavItems;

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white">
            RC
          </span>
          <span className="font-display">Research Curator</span>
        </Link>
        <nav className="hidden items-center gap-1 rounded-full bg-slate-100 p-1 text-sm md:flex">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="rounded-full px-4 py-2 text-slate-600 transition-colors hover:text-slate-900"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <span className="hidden text-sm text-slate-500 md:block">Signed in</span>
          <button className="rounded-full border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">
            User
          </button>
          <button className="rounded-full border border-slate-200 px-3 py-2 text-sm md:hidden">
            Menu
          </button>
        </div>
      </div>
    </header>
  );
}
