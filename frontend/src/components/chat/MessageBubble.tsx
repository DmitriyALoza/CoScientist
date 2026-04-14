"use client";

import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { ToolTrace } from "./ToolTrace";
import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
  isLive?: boolean;
  toolTrace?: Record<string, unknown>[];
}

export function MessageBubble({ message, isLive = false, toolTrace = [] }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "relative max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-indigo-600 text-white rounded-br-sm"
            : "bg-zinc-900 text-zinc-100 rounded-bl-sm border border-zinc-800",
        )}
      >
        {/* Agent badge */}
        {!isUser && message.agent && (
          <div className="mb-2">
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-zinc-800 text-indigo-400 border border-zinc-700">
              via {message.agent}
            </span>
          </div>
        )}

        {/* Content */}
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
        ) : (
          <div
            className={cn(
              "text-sm leading-relaxed",
              "prose prose-sm prose-invert max-w-none",
              "prose-p:my-1 prose-headings:text-zinc-100 prose-headings:font-semibold",
              "prose-code:text-indigo-300 prose-code:bg-zinc-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono",
              "prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800",
              "prose-a:text-indigo-400 prose-strong:text-zinc-100",
              "prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5",
            )}
          >
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isLive && (
              <span className="inline-block w-0.5 h-4 bg-zinc-300 ml-0.5 animate-pulse align-middle" />
            )}
          </div>
        )}

        {/* Tool trace (assistant only, not live) */}
        {!isUser && !isLive && toolTrace.length > 0 && (
          <ToolTrace toolTrace={toolTrace} />
        )}

        {/* Timestamp */}
        {!isLive && (
          <p
            className={cn(
              "text-[10px] mt-1.5 select-none",
              isUser ? "text-indigo-200" : "text-zinc-600",
            )}
          >
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </div>
  );
}
