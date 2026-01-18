"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";

const LoadingCard = () => (
  <div className="mx-auto mt-16 max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
    <p className="text-sm font-medium text-blue-600">Checking access</p>
    <h2 className="font-display mt-3 text-xl font-semibold text-slate-900">
      Loading your workspace
    </h2>
    <p className="mt-2 text-sm text-slate-500">
      Verifying your session, please wait...
    </p>
  </div>
);

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, user, isLoading } = useAuth();
  const hydrated = useAuthStore((state) => state.hydrated);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!token && pathname !== "/login") {
      router.replace("/login");
    }
  }, [hydrated, pathname, router, token]);

  if (!hydrated || isLoading) {
    return <LoadingCard />;
  }

  if (!token || !user) {
    return null;
  }

  return <>{children}</>;
}
