"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ExperimentLoop, Experiment } from "@/lib/types";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";

const LOOP_STATUS_CONFIG = {
  active: { label: "Active", className: "bg-indigo-500/15 text-indigo-400 border-indigo-500/20" },
  converged: { label: "Converged", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
  exhausted: { label: "Exhausted", className: "bg-amber-400/15 text-amber-400 border-amber-400/20" },
  abandoned: { label: "Abandoned", className: "bg-zinc-600/15 text-zinc-500 border-zinc-600/20" },
} as const;

const EXPERIMENT_STATUS_CONFIG = {
  planned: { label: "Planned", className: "bg-zinc-700/50 text-zinc-400 border-zinc-700" },
  running: { label: "Running", className: "bg-indigo-500/15 text-indigo-400 border-indigo-500/20" },
  completed: { label: "Completed", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
  failed: { label: "Failed", className: "bg-red-500/15 text-red-400 border-red-500/20" },
} as const;

function ExperimentRow({ exp }: { exp: Experiment }) {
  const status = EXPERIMENT_STATUS_CONFIG[exp.status];
  return (
    <div className="flex items-start gap-3 py-3 border-b border-zinc-800/50 last:border-0">
      <span className="text-xs font-mono text-zinc-600 mt-0.5 shrink-0 w-6">
        #{exp.iteration}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-zinc-300 leading-snug line-clamp-2">{exp.protocol}</p>
        <p className="text-xs text-zinc-500 mt-1">{formatDate(exp.created_at)}</p>
      </div>
      <span
        className={cn(
          "text-[11px] font-medium px-1.5 py-0.5 rounded border shrink-0",
          status.className
        )}
      >
        {status.label}
      </span>
    </div>
  );
}

function ExperimentLoopCard({ loop }: { loop: ExperimentLoop }) {
  const status = LOOP_STATUS_CONFIG[loop.status];
  const progress =
    loop.max_iterations > 0
      ? (loop.current_iteration / loop.max_iterations) * 100
      : 0;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-zinc-800">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 min-w-0">
            <code className="text-xs font-mono text-zinc-500 truncate">
              {loop.loop_id}
            </code>
          </div>
          <span
            className={cn(
              "text-[11px] font-medium px-1.5 py-0.5 rounded border shrink-0",
              status.className
            )}
          >
            {status.label}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-zinc-500">
              Iteration {loop.current_iteration} / {loop.max_iterations}
            </span>
            <span className="text-xs font-mono text-zinc-600">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                loop.status === "converged"
                  ? "bg-emerald-500"
                  : loop.status === "exhausted"
                  ? "bg-amber-400"
                  : loop.status === "abandoned"
                  ? "bg-zinc-600"
                  : "bg-indigo-500"
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Experiments list */}
      {loop.experiments.length > 0 ? (
        <div className="px-5 divide-y divide-zinc-800/0">
          {loop.experiments.map((exp) => (
            <ExperimentRow key={exp.experiment_id} exp={exp} />
          ))}
        </div>
      ) : (
        <div className="px-5 py-4 text-sm text-zinc-600">No experiments yet.</div>
      )}

      {/* Learnings */}
      {loop.learnings.length > 0 && (
        <div className="px-5 py-4 border-t border-zinc-800 bg-zinc-800/20">
          <p className="text-xs font-medium text-zinc-400 mb-2">Learnings</p>
          <ul className="space-y-1.5">
            {loop.learnings.map((l, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-zinc-500">
                <span className="text-indigo-500 mt-0.5 shrink-0">·</span>
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5 animate-pulse space-y-3">
      <div className="flex justify-between">
        <div className="h-3 bg-zinc-800 rounded w-40" />
        <div className="h-3 bg-zinc-800 rounded w-16" />
      </div>
      <div className="h-2 bg-zinc-800 rounded-full" />
    </div>
  );
}

export default function ExperimentsPage() {
  const { data: loops, isLoading, error } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.experiments.list("default", 20),
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-50">Experiments</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Iterative experiment loops managed by the Experiment Manager agent.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-sm text-red-400">
          Failed to load experiments. Is the backend running?
        </div>
      )}

      {!isLoading && !error && loops && loops.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-4xl mb-4" aria-hidden="true">🧪</span>
          <p className="text-zinc-400 text-sm font-medium">No experiment loops yet</p>
          <p className="text-zinc-600 text-xs mt-1 max-w-xs">
            Ask the AI to plan an experiment in the Chat page to get started.
          </p>
        </div>
      )}

      {!isLoading && loops && loops.length > 0 && (
        <div className="space-y-4">
          {loops.map((loop) => (
            <ExperimentLoopCard key={loop.loop_id} loop={loop} />
          ))}
        </div>
      )}
    </div>
  );
}
