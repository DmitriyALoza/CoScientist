"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import type { ChatMessage, AttachedDoc, ChatMode, Citation, WsServerMessage } from "@/lib/types";

export interface UseChatReturn {
  messages: ChatMessage[];
  pendingMessage: { content: string; agent: string | null } | null;
  isStreaming: boolean;
  citations: Citation[];
  toolTrace: Record<string, unknown>[];
  threadId: string | null;
  error: string | null;
  sendMessage: (content: string, docs: AttachedDoc[], mode: ChatMode, runId?: string) => void;
  clearMessages: () => void;
}

export function useChat(userId = "default"): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pendingMessage, setPendingMessage] = useState<{ content: string; agent: string | null } | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [toolTrace, setToolTrace] = useState<Record<string, unknown>[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  // Ref-based accumulation avoids stale closures in the WS handler
  const pendingRef = useRef<{ content: string; agent: string | null } | null>(null);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const sendMessage = useCallback(
    (content: string, docs: AttachedDoc[], mode: ChatMode, runId?: string) => {
      // Close any existing connection
      wsRef.current?.close();
      wsRef.current = null;

      // Immediately append the user turn
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setError(null);

      // Reset pending buffer
      pendingRef.current = { content: "", agent: null };
      setPendingMessage({ content: "", agent: null });

      const ws = new WebSocket(api.wsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            type: "message",
            content,
            mode,
            thread_id: threadId,
            user_id: userId,
            run_id: runId ?? null,
            docs: docs.map((d) => ({ name: d.name, text: d.text })),
          }),
        );
      };

      ws.onmessage = (event: MessageEvent) => {
        const msg: WsServerMessage = JSON.parse(event.data as string);

        if (msg.type === "token") {
          pendingRef.current = {
            content: (pendingRef.current?.content ?? "") + msg.text,
            agent: msg.agent ?? pendingRef.current?.agent ?? null,
          };
          setPendingMessage({ ...pendingRef.current });
        } else if (msg.type === "citation") {
          setCitations((prev) => [...prev, msg.citation]);
        } else if (msg.type === "tool_call") {
          setToolTrace((prev) => [...prev, msg.tool_call]);
        } else if (msg.type === "done") {
          const pending = pendingRef.current;
          if (pending !== null) {
            const assistantMsg: ChatMessage = {
              id: crypto.randomUUID(),
              role: "assistant",
              content: pending.content,
              agent: msg.agent ?? pending.agent ?? undefined,
              timestamp: Date.now(),
            };
            setMessages((m) => [...m, assistantMsg]);
          }
          pendingRef.current = null;
          setPendingMessage(null);
          setThreadId(msg.thread_id);
          setIsStreaming(false);
          ws.close(1000, "done");
          wsRef.current = null;
        } else if (msg.type === "error") {
          setError(msg.message);
          setMessages((m) => [
            ...m,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `⚠ ${msg.message}`,
              timestamp: Date.now(),
            },
          ]);
          pendingRef.current = null;
          setPendingMessage(null);
          setIsStreaming(false);
          ws.close(1000, "error");
          wsRef.current = null;
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection failed. Is the backend running?");
        pendingRef.current = null;
        setPendingMessage(null);
        setIsStreaming(false);
      };

      ws.onclose = (event: CloseEvent) => {
        // Unexpected close (not triggered by us)
        if (event.code !== 1000 && pendingRef.current !== null) {
          setError("Connection lost unexpectedly.");
          pendingRef.current = null;
          setPendingMessage(null);
          setIsStreaming(false);
        }
      };
    },
    [userId, threadId],
  );

  const clearMessages = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    pendingRef.current = null;
    setMessages([]);
    setPendingMessage(null);
    setIsStreaming(false);
    setCitations([]);
    setToolTrace([]);
    setError(null);
  }, []);

  return {
    messages,
    pendingMessage,
    isStreaming,
    citations,
    toolTrace,
    threadId,
    error,
    sendMessage,
    clearMessages,
  };
}
