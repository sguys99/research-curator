"use client";

import { useEffect } from "react";

import { useToastStore } from "@/stores/toast-store";

const variantStyles = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  error: "border-rose-200 bg-rose-50 text-rose-800",
  info: "border-slate-200 bg-white text-slate-800",
};

type ToastItemProps = {
  id: string;
  title: string;
  description?: string;
  variant?: "success" | "error" | "info";
  onDismiss: (id: string) => void;
};

const ToastItem = ({ id, title, description, variant = "info", onDismiss }: ToastItemProps) => {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), 4000);
    return () => clearTimeout(timer);
  }, [id, onDismiss]);

  return (
    <div
      className={`pointer-events-auto w-full max-w-sm rounded-2xl border px-4 py-3 shadow-sm ${
        variantStyles[variant]
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{title}</p>
          {description && <p className="mt-1 text-xs opacity-80">{description}</p>}
        </div>
        <button
          type="button"
          onClick={() => onDismiss(id)}
          className="text-xs font-medium opacity-60 hover:opacity-100"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default function ToastProvider({ children }: { children: React.ReactNode }) {
  const toasts = useToastStore((state) => state.toasts);
  const removeToast = useToastStore((state) => state.removeToast);

  return (
    <>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} {...toast} onDismiss={removeToast} />
        ))}
      </div>
    </>
  );
}
