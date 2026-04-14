"use client";

import { useState, useCallback } from "react";
import { PanelRight, PanelRightClose, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChat } from "@/lib/hooks/useChat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";
import { CitationsPanel } from "@/components/chat/CitationsPanel";
import type { AttachedDoc } from "@/lib/types";

export default function ChatPage() {
  const chat = useChat("default");
  const [panelOpen, setPanelOpen] = useState(false);

  const handleSend = useCallback(
    (content: string, docs: AttachedDoc[]) => {
      chat.sendMessage(content, docs, "normal");
    },
    [chat],
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="shrink-0 flex items-center justify-between gap-3 px-4 h-11 border-b border-zinc-800 bg-zinc-900/80">
        <div className="flex items-center gap-2 min-w-0">
          {chat.threadId && (
            <span className="text-[10px] font-mono text-zinc-600 truncate hidden sm:block">
              thread: {chat.threadId}
            </span>
          )}
          {chat.error && (
            <span className="text-[11px] text-red-400 truncate">{chat.error}</span>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {chat.messages.length > 0 && (
            <button
              onClick={chat.clearMessages}
              title="Clear conversation"
              className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
              aria-label="Clear conversation"
            >
              <Trash2 size={14} />
            </button>
          )}
          <button
            onClick={() => setPanelOpen((o) => !o)}
            title={panelOpen ? "Hide citations panel" : "Show citations panel"}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors",
              panelOpen
                ? "bg-zinc-800 text-zinc-200"
                : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800",
            )}
          >
            {panelOpen ? <PanelRightClose size={14} /> : <PanelRight size={14} />}
            <span className="hidden sm:inline">
              {panelOpen ? "Hide Panel" : "Show Panel"}
            </span>
            {chat.citations.length > 0 && (
              <span className="ml-0.5 px-1.5 py-0.5 rounded-full bg-indigo-600 text-white text-[10px] font-medium">
                {chat.citations.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat column */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <MessageList
            messages={chat.messages}
            pendingMessage={chat.pendingMessage}
            isStreaming={chat.isStreaming}
            toolTrace={chat.toolTrace}
            onSuggestion={(text) => chat.sendMessage(text, [], "normal")}
          />
          <ChatInput
            onSend={handleSend}
            isStreaming={chat.isStreaming}
          />
        </div>

        {/* Citations side panel */}
        {panelOpen && <CitationsPanel citations={chat.citations} />}
      </div>
    </div>
  );
}
