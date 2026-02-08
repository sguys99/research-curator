const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// SSE 스트림 타임아웃 설정 (30초)
const STREAM_TIMEOUT_MS = 30000;

type StreamPayload = {
  messages: { role: "system" | "user" | "assistant"; content: string }[];
  provider?: "openai" | "claude";
  model?: string | null;
  temperature?: number;
  max_tokens?: number;
  response_format?: "text" | "json";
  stream?: boolean;
};

// SSE 응답 파싱 결과 타입
type StreamResponse = {
  content?: string;
  done?: boolean;
  error?: string;
};

/**
 * Server-Sent Events(SSE) 스트림을 처리하여 실시간 LLM 응답을 수신합니다.
 *
 * @param payload - LLM 요청 파라미터 (메시지, 모델 설정 등)
 * @param onChunk - 청크 수신 시 호출되는 콜백 함수
 * @param options - 추가 옵션 (abortSignal: 외부에서 요청 취소 가능)
 * @throws {Error} 스트림 요청 실패, 타임아웃, 또는 파싱 오류 시
 */
export const streamChatCompletion = async (
  payload: StreamPayload,
  onChunk: (content: string) => void,
  options?: { abortSignal?: AbortSignal },
): Promise<void> => {
  // AbortController로 타임아웃 및 외부 취소 처리
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

  // 외부 abort signal과 연결
  if (options?.abortSignal) {
    options.abortSignal.addEventListener("abort", () => controller.abort());
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/llm/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(typeof window !== "undefined" && window.sessionStorage.getItem("access_token")
          ? { Authorization: `Bearer ${window.sessionStorage.getItem("access_token")}` }
          : {}),
      },
      body: JSON.stringify({ ...payload, stream: true }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`스트림 요청 실패 (${response.status}): ${errorText}`);
    }

    if (!response.body) {
      throw new Error("응답 본문이 없습니다.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // 스트림 읽기 루프
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      // 타임아웃 리셋 (데이터 수신 시마다)
      clearTimeout(timeoutId);

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      // SSE 이벤트 파싱
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) {
          continue;
        }
        const data = line.replace(/^data:\s*/, "");
        if (!data) {
          continue;
        }

        try {
          const parsed = JSON.parse(data) as StreamResponse;
          if (parsed.error) {
            throw new Error(parsed.error);
          }
          if (parsed.content) {
            onChunk(parsed.content);
          }
          if (parsed.done) {
            return;
          }
        } catch {
          // JSON 파싱 실패 시 무시하고 계속 진행
          console.warn("SSE 데이터 파싱 실패:", data);
        }
      }
    }
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("요청이 취소되었거나 타임아웃되었습니다.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};
