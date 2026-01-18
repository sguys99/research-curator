"use client";

import { useState } from "react";

import { streamChatCompletion } from "@/lib/api/llm";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const useChatStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamText = async (text: string, onChunk: (content: string) => void) => {
    for (const chunk of text.split(" ")) {
      onChunk(`${chunk} `);
      await sleep(40);
    }
  };

  const streamMessage = async (
    text: string,
    onChunk: (content: string) => void,
  ): Promise<void> => {
    setIsStreaming(true);
    setError(null);

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
