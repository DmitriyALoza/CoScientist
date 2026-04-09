"use client";
import Link from "next/link";
import { MessageSquare, ArrowLeft } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex flex-1 items-center justify-center min-h-full p-6">
      <div className="max-w-md w-full">
        <div className="bg-zinc-900 rounded-2xl border border-zinc-800 p-8 text-center space-y-5">
          <div className="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center mx-auto">
            <MessageSquare size={24} className="text-indigo-400" />
          </div>

          <div>
            <h1 className="text-xl font-semibold text-zinc-50">Chat — Phase 4</h1>
            <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
              The full chat interface with WebSocket streaming, multi-agent routing,
              citations panel, and tool trace drawer will be delivered in Phase 4.
            </p>
          </div>

          <div className="bg-zinc-800/60 rounded-xl border border-zinc-800 p-4 text-left space-y-2">
            <p className="text-xs font-medium text-zinc-400">What&apos;s coming</p>
            <ul className="text-xs text-zinc-500 space-y-1.5">
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">·</span>
                Real-time token streaming over WebSocket
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">·</span>
                Specialist agent routing (literature, SOP, controls)
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">·</span>
                Inline citations with source preview
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">·</span>
                Tool call trace drawer
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">·</span>
                File/protocol attachment support
              </li>
            </ul>
          </div>

          <div className="pt-1">
            <p className="text-xs text-zinc-600 mb-3">
              In the meantime, use the CLI for chat:
            </p>
            <code className="text-xs font-mono text-zinc-400 bg-zinc-800 rounded-lg px-3 py-2 block text-left">
              uv run eln --chat
            </code>
          </div>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors mt-2"
          >
            <ArrowLeft size={14} />
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
