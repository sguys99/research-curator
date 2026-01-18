"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/lib/api/users";
import { useAuthStore } from "@/stores/auth-store";

export const useAuth = () => {
  const { token, user, setUser } = useAuthStore();

  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: Boolean(token),
    retry: 1,
  });

  useEffect(() => {
    if (query.data) {
      setUser(query.data);
    }
  }, [query.data, setUser]);

  return {
    token,
    user: user ?? query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
};
