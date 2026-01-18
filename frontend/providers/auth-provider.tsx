"use client";

import { useEffect } from "react";

import { useAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";

type AuthProviderProps = {
  children: React.ReactNode;
};

export default function AuthProvider({ children }: AuthProviderProps) {
  const hydrate = useAuthStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useAuth();

  return <>{children}</>;
}
