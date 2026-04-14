"use client";

import { ChevronDown } from "lucide-react";

interface Props {
  toolTrace: Record<string, unknown>[];
}

export function ToolTrace({ toolTrace }: Props) {
  if (toolTrace.length === 0) return null;

  return (
    <details className="mt-2 group">
      <summary className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-400 cursor-pointer list-none select-none">
        <ChevronDown
          size={12}
          className="transition-transform group-open:rotate-180"
        />
        {toolTrace.length} tool call{toolTrace.length !== 1 ? "s" : ""}
      </summary>

      <div className="mt-2 space-y-2">
        {toolTrace.map((call, i) => {
          const tool = (call.tool ?? call.name ?? call.function ?? "tool") as string;
          const args = call.args ?? call.arguments ?? call.input ?? {};
          return (
            <div
              key={i}
              className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2"
            >
              <p className="text-xs font-mono text-indigo-400 mb-1">{String(tool)}</p>
              <pre className="text-xs text-zinc-500 font-mono overflow-x-auto whitespace-pre-wrap break-all">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          );
        })}
      </div>
    </details>
  );
}
