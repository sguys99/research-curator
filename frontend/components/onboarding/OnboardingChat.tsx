"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";

import { useChatStream } from "@/hooks/use-chat-stream";
import { updateUserPreferences } from "@/lib/api/users";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import type { UserPreferences } from "@/types/user";

const createId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const infoTypeOptions = [
  "📚 논문 위주 (70%)",
  "📰 뉴스 위주 (70%)",
  "📊 리포트 위주 (70%)",
  "⚖️ 균형있게 (논문 50%, 뉴스 30%, 리포트 20%)",
];

const timeOptions = ["🕗 오전 8시 (기본)", "🕐 오후 1시", "🕕 오후 6시", "🕘 오후 9시"];

const buildSummary = (preferences: UserPreferences) => {
  const paper = Math.round(preferences.info_types.paper * 100);
  const news = Math.round(preferences.info_types.news * 100);
  const report = Math.round(preferences.info_types.report * 100);

  return (
    `완벽합니다! 🎉\n\n설정이 완료되었습니다. 확인해주세요:\n\n` +
    `**연구 분야**: ${preferences.research_fields.join(", ") || "미입력"}\n` +
    `**키워드**: ${preferences.keywords.join(", ") || "미입력"}\n` +
    `**정보 유형**: 논문 ${paper}%, 뉴스 ${news}%, 리포트 ${report}%\n` +
    `**이메일 발송 시간**: ${preferences.email_time}\n` +
    `**일일 제공량**: ${preferences.daily_limit}개\n\n` +
    "이대로 저장하시겠습니까?\n\n'확인' 또는 '수정'을 입력해주세요."
  );
};

export default function OnboardingChat() {
  const router = useRouter();
  const { streamMessage, isStreaming, error: streamError } = useChatStream();
  const user = useAuthStore((state) => state.user);
  const {
    step,
    messages,
    preferences,
    completed,
    addMessage,
    updateMessage,
    clearAllOptions,
    setStep,
    updatePreferences,
    markCompleted,
    reset,
  } = useOnboardingStore();
  const [inputValue, setInputValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const initialized = useRef(false);

  const progressLabel = useMemo(() => {
    if (step <= 0) {
      return "Step 1 / 5";
    }
    if (step >= 6) {
      return "Review";
    }
    return `Step ${step} / 5`;
  }, [step]);

  const addAssistantMessage = useCallback(
    async (content: string, options?: string[]) => {
      const id = createId();
      addMessage({ id, role: "assistant", content: "", options });

      let assembled = "";
      await streamMessage(content, (chunk) => {
        assembled += chunk;
        updateMessage(id, assembled);
      });
    },
    [addMessage, streamMessage, updateMessage],
  );

  const seedConversation = useCallback(async () => {
    const welcomeMessage =
      "안녕하세요! 👋\n\n저는 Research Curator의 AI 어시스턴트입니다. 몇 가지 질문을 통해 맞춤형 설정을 완료해드릴게요.";
    addMessage({ id: createId(), role: "assistant", content: welcomeMessage });

    await addAssistantMessage(
      "\n**질문 1/5**: 어떤 연구 분야에 관심이 있으신가요?\n\n예시: Machine Learning, Natural Language Processing, Computer Vision",
    );
    setStep(1);
  }, [addAssistantMessage, addMessage, setStep]);

  useEffect(() => {
    if (initialized.current) {
      return;
    }
    if (messages.length === 0) {
      initialized.current = true;
      void seedConversation();
    }
  }, [messages.length, seedConversation]);

  const handleUserResponse = async (content: string) => {
    if (!content.trim()) {
      return;
    }

    addMessage({ id: createId(), role: "user", content });

    if (step === 1) {
      const fields = content
        .split(",")
        .map((field) => field.trim())
        .filter((field) => field.length > 2)
        .slice(0, 5);
      const nextFields = fields.length ? fields : ["AI", "Machine Learning"];
      updatePreferences({ research_fields: nextFields });
      await addAssistantMessage(
        "좋아요!\n**질문 2/5**: 특히 관심있는 키워드를 알려주세요.\n\n예시: transformer, GPT, alignment",
      );
      setStep(2);
      return;
    }

    if (step === 2) {
      const keywords = content
        .split(",")
        .map((keyword) => keyword.trim())
        .filter((keyword) => keyword.length > 1)
        .slice(0, 10);
      const nextKeywords = keywords.length ? keywords : ["AI", "research"];
      updatePreferences({ keywords: nextKeywords });
      await addAssistantMessage("**질문 3/5**: 어떤 유형의 정보를 받고 싶으신가요?", infoTypeOptions);
      setStep(3);
      return;
    }

    if (step === 3) {
      let infoTypes: UserPreferences["info_types"] = { paper: 0.5, news: 0.3, report: 0.2 };
      const normalized = content.toLowerCase();
      if (content.includes("균형") || normalized.includes("balance")) {
        infoTypes = { paper: 0.5, news: 0.3, report: 0.2 };
      } else if (content.includes("논문") || normalized.includes("paper")) {
        infoTypes = { paper: 0.7, news: 0.2, report: 0.1 };
      } else if (content.includes("뉴스") || normalized.includes("news")) {
        infoTypes = { paper: 0.2, news: 0.7, report: 0.1 };
      } else if (content.includes("리포트") || normalized.includes("report")) {
        infoTypes = { paper: 0.2, news: 0.1, report: 0.7 };
      }
      updatePreferences({ info_types: infoTypes });
      await addAssistantMessage(
        "**질문 4/5**: 특별히 포함하고 싶은 웹사이트가 있나요?\n예시: techcrunch.com, venturebeat.com\n없으면 '없음'이라고 입력해주세요.",
      );
      setStep(4);
      return;
    }

    if (step === 4) {
      const normalized = content.trim().toLowerCase();
      const sources =
        normalized.includes("없음") || normalized.includes("기본") || normalized.includes("skip")
          ? []
          : content
              .replace(/,/g, " ")
              .split(" ")
              .map((item) => item.trim())
              .filter((item) => item.includes("."))
              .slice(0, 5);
      updatePreferences({ sources });
      await addAssistantMessage("**질문 5/5**: 이메일 발송 시간을 선택해주세요.", timeOptions);
      setStep(5);
      return;
    }

    if (step === 5) {
      const timeMap: Record<string, string> = {
        "오전 8시": "08:00",
        "오후 1시": "13:00",
        "오후 6시": "18:00",
        "오후 9시": "21:00",
      };
      const match = Object.keys(timeMap).find((key) => content.includes(key));
      const nextPreferences = {
        ...preferences,
        email_time: match ? timeMap[match] : "08:00",
      };
      updatePreferences({ email_time: nextPreferences.email_time });
      await addAssistantMessage(buildSummary(nextPreferences));
      setStep(6);
      return;
    }

    if (step === 6) {
      if (content.includes("수정") || content.toLowerCase().includes("edit")) {
        reset();
        initialized.current = false;
        setInputValue("");
        return;
      }
      if (content.includes("확인") || content.toLowerCase().includes("yes") || content.includes("네")) {
        if (!user?.id) {
          setSaveError("로그인 정보를 찾을 수 없습니다.");
          return;
        }
        setIsSaving(true);
        setSaveError(null);
        try {
          await updateUserPreferences(user.id, preferences);
          markCompleted();
          addMessage({
            id: createId(),
            role: "system",
            content:
              "✅ 설정이 저장되었습니다! 이제 대시보드에서 맞춤형 다이제스트를 확인할 수 있습니다.",
          });
        } catch (error) {
          setSaveError(error instanceof Error ? error.message : "저장에 실패했습니다.");
        } finally {
          setIsSaving(false);
        }
      }
    }
  };

  const handleOptionSelect = async (option: string) => {
    // 중복 클릭 방지: 이미 처리 중이거나 스트리밍 중이면 무시
    if (isProcessing || isStreaming) {
      return;
    }
    setIsProcessing(true);

    try {
      // 응답 처리 완료 후 options 제거 (타이밍 문제 해결)
      await handleUserResponse(option);
    } finally {
      clearAllOptions();
      setIsProcessing(false);
    }
  };

  const handleSubmit = () => {
    if (isStreaming || completed || isSaving || isProcessing) {
      return;
    }
    const value = inputValue.trim();
    setInputValue("");
    void handleUserResponse(value);
  };

  const canSend = !isStreaming && !completed && !isSaving && !isProcessing && inputValue.trim().length > 0;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-slate-900">AI onboarding assistant</h2>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          {progressLabel}
        </span>
      </div>

      <div className="mt-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={message.role === "user" ? "flex justify-end" : "flex"}>
            <div
              className={
                message.role === "user"
                  ? "max-w-sm rounded-2xl bg-blue-600 px-4 py-3 text-sm text-white whitespace-pre-line"
                  : message.role === "system"
                    ? "w-full rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900 whitespace-pre-line"
                    : "max-w-sm rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-700 whitespace-pre-line"
              }
            >
              <ReactMarkdown
                components={{
                  // 마크다운 요소들이 채팅 버블 스타일과 어울리도록 커스터마이징
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                }}
              >
                {message.content}
              </ReactMarkdown>
              {message.options && message.options.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.options.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => handleOptionSelect(option)}
                      className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 transition-colors hover:bg-slate-50"
                      disabled={isStreaming || completed || isSaving || isProcessing}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      {streamError ? (
        <p className="mt-4 text-xs text-amber-600">{streamError} 로컬 스트리밍으로 전환했습니다.</p>
      ) : null}

      {saveError ? <p className="mt-4 text-xs text-red-600">{saveError}</p> : null}

      {!completed ? (
        <div className="mt-6 flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3">
          <input
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="메시지를 입력하세요..."
            className="flex-1 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
            disabled={isStreaming || isSaving}
          />
          <button
            type="button"
            onClick={handleSubmit}
            className="rounded-full bg-blue-600 px-4 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!canSend}
          >
            {isStreaming ? "Typing..." : "Send"}
          </button>
        </div>
      ) : (
        <div className="mt-6 flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-4 text-sm text-slate-600">
          <span>온보딩이 완료되었습니다.</span>
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-full bg-blue-600 px-4 py-2 text-xs font-medium text-white"
            disabled={isSaving}
          >
            대시보드로 이동
          </button>
        </div>
      )}
    </section>
  );
}
