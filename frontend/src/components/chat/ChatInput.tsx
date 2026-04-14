"use client";

import { useRef, useState, useCallback, type KeyboardEvent, type ChangeEvent } from "react";
import { Paperclip, Send, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AttachedDoc, ChatMode } from "@/lib/types";

const CHAR_LIMIT_PER_FILE = 8_000;
const CHAR_LIMIT_TOTAL = 24_000;
const ACCEPTED_TYPES = ".txt,.md,.csv";

interface Props {
  onSend: (content: string, docs: AttachedDoc[]) => void;
  isStreaming: boolean;
  initialValue?: string;
}

export function ChatInput({ onSend, isStreaming, initialValue = "" }: Props) {
  const [value, setValue] = useState(initialValue);
  const [mode, setMode] = useState<ChatMode>("normal");
  const [docs, setDocs] = useState<AttachedDoc[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-grow textarea
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 144) + "px"; // max 6 rows ≈ 144px
  };

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed, docs);
    setValue("");
    setDocs([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [value, docs, isStreaming, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileError(null);

    const reader = new FileReader();
    reader.onload = () => {
      const text = (reader.result as string).slice(0, CHAR_LIMIT_PER_FILE);
      const totalChars = docs.reduce((s, d) => s + d.chars, 0) + text.length;

      if (totalChars > CHAR_LIMIT_TOTAL) {
        setFileError(`Total attachment size exceeds ${CHAR_LIMIT_TOTAL.toLocaleString()} characters.`);
        return;
      }

      setDocs((prev) => [
        ...prev,
        { name: file.name, text, chars: text.length },
      ]);
    };
    reader.readAsText(file);

    // Reset so the same file can be re-attached after removal
    e.target.value = "";
  };

  const removeDoc = (name: string) => {
    setDocs((prev) => prev.filter((d) => d.name !== name));
    setFileError(null);
  };

  const MODE_LABELS: Record<ChatMode, string> = {
    normal: "Normal",
    validation: "Validation",
    protocol: "Protocol",
  };

  return (
    <div className="shrink-0 border-t border-zinc-800 bg-zinc-900 px-4 pt-3 pb-4">
      {/* Mode pills */}
      <div className="flex items-center gap-1 mb-2">
        {(Object.keys(MODE_LABELS) as ChatMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              "px-2.5 py-0.5 text-[11px] font-medium rounded-full transition-colors",
              mode === m
                ? "bg-indigo-600 text-white"
                : "text-zinc-500 hover:text-zinc-300",
            )}
          >
            {MODE_LABELS[m]}
          </button>
        ))}
      </div>

      {/* Attached file chips */}
      {docs.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {docs.map((doc) => (
            <div
              key={doc.name}
              className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-zinc-800 border border-zinc-700 text-xs text-zinc-300"
            >
              <span className="max-w-[160px] truncate">{doc.name}</span>
              <span className="text-zinc-600">·</span>
              <span className="text-zinc-500 text-[10px] shrink-0">
                {(doc.chars / 1000).toFixed(1)}k chars
              </span>
              <button
                onClick={() => removeDoc(doc.name)}
                className="ml-0.5 text-zinc-500 hover:text-zinc-200"
                aria-label={`Remove ${doc.name}`}
              >
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
      )}

      {fileError && (
        <p className="text-[11px] text-red-400 mb-1.5">{fileError}</p>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2">
        {/* Paperclip */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          title={`Attach a text file (.txt, .md, .csv) — ${CHAR_LIMIT_PER_FILE.toLocaleString()} chars/file, ${CHAR_LIMIT_TOTAL.toLocaleString()} total`}
          className="shrink-0 p-2 rounded-lg text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors mb-0.5"
          aria-label="Attach file"
        >
          <Paperclip size={16} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          placeholder={isStreaming ? "Waiting for response…" : "Ask the AI Co-Scientist…"}
          className={cn(
            "flex-1 resize-none rounded-xl bg-zinc-800 border border-zinc-700 px-3 py-2.5",
            "text-sm text-zinc-100 placeholder:text-zinc-600",
            "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "min-h-[42px] max-h-[144px] overflow-y-auto",
          )}
        />

        {/* Send */}
        <button
          type="button"
          onClick={handleSend}
          disabled={isStreaming || !value.trim()}
          className={cn(
            "shrink-0 p-2.5 rounded-xl transition-colors mb-0.5",
            isStreaming || !value.trim()
              ? "bg-zinc-800 text-zinc-600 cursor-not-allowed"
              : "bg-indigo-600 text-white hover:bg-indigo-500",
          )}
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </div>

      <p className="text-[10px] text-zinc-700 mt-1.5">
        Shift+Enter for new line · Attach .txt / .md / .csv files for context
      </p>
    </div>
  );
}
