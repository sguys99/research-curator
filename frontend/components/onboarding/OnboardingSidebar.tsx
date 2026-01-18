"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";

const steps = [
  "Research fields",
  "Focus keywords",
  "Content mix",
  "Preferred sources",
  "Delivery time",
];

export default function OnboardingSidebar() {
  const { step, preferences } = useOnboardingStore();

  return (
    <aside className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Progress</h3>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {steps.map((label, index) => (
            <li key={label} className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  index < step - 1 ? "bg-emerald-500" : "bg-slate-300"
                }`}
              />
              {label}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Preview</h3>
        <div className="mt-4 space-y-3 text-sm text-slate-600">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Research Fields</p>
            <p>{preferences.research_fields.join(", ") || "Awaiting input"}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Keywords</p>
            <p>{preferences.keywords.join(", ") || "Awaiting input"}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Sources</p>
            <p>{preferences.sources.join(", ") || "Default set"}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Email Time</p>
            <p>{preferences.email_time}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
