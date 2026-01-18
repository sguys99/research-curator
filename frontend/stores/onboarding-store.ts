import { create } from "zustand";

import type { ChatMessage } from "@/types/chat";
import type { UserPreferences } from "@/types/user";

type OnboardingState = {
  step: number;
  messages: ChatMessage[];
  preferences: UserPreferences;
  completed: boolean;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, content: string) => void;
  setStep: (step: number) => void;
  updatePreferences: (patch: Partial<UserPreferences>) => void;
  markCompleted: () => void;
  reset: () => void;
};

const defaultPreferences: UserPreferences = {
  research_fields: [],
  keywords: [],
  sources: [],
  info_types: {
    paper: 0.5,
    news: 0.3,
    report: 0.2,
  },
  email_time: "08:00",
  daily_limit: 5,
  email_enabled: true,
};

export const useOnboardingStore = create<OnboardingState>((set) => ({
  step: 0,
  messages: [],
  preferences: defaultPreferences,
  completed: false,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id, content) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id ? { ...message, content } : message,
      ),
    })),
  setStep: (step) => set({ step }),
  updatePreferences: (patch) =>
    set((state) => ({ preferences: { ...state.preferences, ...patch } })),
  markCompleted: () => set({ completed: true }),
  reset: () =>
    set({
      step: 0,
      messages: [],
      preferences: defaultPreferences,
      completed: false,
    }),
}));
