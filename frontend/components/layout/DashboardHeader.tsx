"use client";

import { useState } from "react";
import Image from "next/image";
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
  const [menuOpen, setMenuOpen] = useState(false);
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
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="rounded-xl px-3 py-2 hover:bg-white"
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
