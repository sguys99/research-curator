"use client";

import { useState } from "react";

import { streamChatCompletion } from "@/lib/api/llm";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type StreamOptions = {
  useRemote?: boolean;
};

export const useChatStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamText = async (text: string, onChunk: (content: string) => void) => {
    // 정규식으로 단어와 공백/줄바꿈을 각각 토큰으로 분리 (한국어 및 마크다운 호환)
    const tokens = text.match(/\S+|\s+/g) ?? [text];
    for (const token of tokens) {
      onChunk(token);
      await sleep(30);
    }
  };

  const streamMessage = async (
    text: string,
    onChunk: (content: string) => void,
    options?: StreamOptions,
  ): Promise<void> => {
    setIsStreaming(true);
    setError(null);

    if (!options?.useRemote) {
      try {
        await streamText(text, onChunk);
      } finally {
        setIsStreaming(false);
      }
      return;
    }

    const payload = {
      messages: [
        {
          role: "system" as const,
          content: "You are a relay. Repeat the user message exactly.",
        },
        { role: "user" as const, content: text },
      ],
      provider: "openai" as const,
      temperature: 0.2,
      max_tokens: 800,
      response_format: "text" as const,
      stream: true,
    };

    try {
      await streamChatCompletion(payload, onChunk);
    } catch (err) {
      await streamText(text, onChunk);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Streaming unavailable.");
      }
    } finally {
      setIsStreaming(false);
    }
  };

  return { streamMessage, isStreaming, error };
};
