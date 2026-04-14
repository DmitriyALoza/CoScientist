"use client";

import { useEffect, useRef } from "react";
import { Microscope, FlaskConical, BookOpen, Lightbulb } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  { icon: Microscope, text: "What controls do I need for a flow cytometry panel?" },
  { icon: FlaskConical, text: "Generate hypotheses for low T-cell activation in my co-culture" },
  { icon: BookOpen, text: "Summarize the latest literature on CD69 upregulation kinetics" },
  { icon: Lightbulb, text: "Help me troubleshoot poor antibody staining efficiency" },
];

interface Props {
  messages: ChatMessage[];
  pendingMessage: { content: string; agent: string | null } | null;
  isStreaming: boolean;
  toolTrace: Record<string, unknown>[];
  onSuggestion: (text: string) => void;
}

export function MessageList({
  messages,
  pendingMessage,
  isStreaming,
  toolTrace,
  onSuggestion,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const userScrolledRef = useRef(false);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    userScrolledRef.current = distanceFromBottom > 80;
  };

  // Scroll to bottom on new content, unless user has scrolled up
  useEffect(() => {
    if (!userScrolledRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, pendingMessage]);

  // When a new user message is sent, always scroll down
  useEffect(() => {
    if (isStreaming) {
      userScrolledRef.current = false;
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [isStreaming]);

  const isEmpty = messages.length === 0 && !pendingMessage;

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-6 px-4">
        <div className="text-center">
          <p className="text-zinc-400 text-sm mb-1">Ask the AI Co-Scientist</p>
          <p className="text-zinc-600 text-xs">Start a conversation or try a suggestion below</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
          {SUGGESTIONS.map(({ icon: Icon, text }) => (
            <button
              key={text}
              onClick={() => onSuggestion(text)}
              className="flex items-start gap-2.5 p-3 rounded-xl border border-zinc-800 bg-zinc-900 hover:border-zinc-700 hover:bg-zinc-800/60 transition-colors text-left group"
            >
              <Icon size={14} className="text-indigo-400 shrink-0 mt-0.5" />
              <span className="text-xs text-zinc-400 group-hover:text-zinc-300 leading-snug">
                {text}
              </span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
    >
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          toolTrace={msg.role === "assistant" ? toolTrace : []}
        />
      ))}

      {/* Live streaming message */}
      {pendingMessage && (
        <MessageBubble
          message={{
            id: "__pending__",
            role: "assistant",
            content: pendingMessage.content || "…",
            agent: pendingMessage.agent ?? undefined,
            timestamp: Date.now(),
          }}
          isLive
        />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
