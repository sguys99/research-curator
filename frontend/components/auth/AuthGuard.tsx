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
    // 토큰이 없으면 로그인 페이지로 리다이렉트
    if (!token && pathname !== "/login") {
      router.replace("/login");
    }
  }, [hydrated, pathname, router, token]);

  // hydration 전이거나 로딩 중이면 로딩 표시
  if (!hydrated || isLoading) {
    return <LoadingCard />;
  }

  // 토큰이 없으면 null 반환 (useEffect에서 리다이렉트 처리)
  if (!token) {
    return null;
  }

  // 토큰이 있으면 자식 컴포넌트 렌더링 (user는 API 응답 후 설정됨)
  return <>{children}</>;
}
