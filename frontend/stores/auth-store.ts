import { create } from "zustand";

import type { User } from "@/types/user";

type AuthState = {
  token: string | null;
  user: User | null;
  hydrated: boolean;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  hydrate: () => void;
  clearAuth: () => void;
};

// sessionStorage 사용: XSS 공격 시 토큰 노출 위험 감소 (탭 닫으면 자동 삭제)
const persistToken = (token: string | null) => {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.sessionStorage.setItem("access_token", token);
  } else {
    window.sessionStorage.removeItem("access_token");
  }
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  hydrated: false,
  setToken: (token) => {
    persistToken(token);
    set({ token });
  },
  setUser: (user) => set({ user }),
  hydrate: () => {
    if (typeof window === "undefined") {
      set({ hydrated: true });
      return;
    }
    const token = window.sessionStorage.getItem("access_token");
    set({ token, hydrated: true });
  },
  clearAuth: () => {
    persistToken(null);
    set({ token: null, user: null });
  },
}));
