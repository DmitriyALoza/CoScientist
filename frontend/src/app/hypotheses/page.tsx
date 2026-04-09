"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { HypothesisSet, Hypothesis } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Swords, FlaskConical } from "lucide-react";

const STATUS_CONFIG = {
  proposed: { label: "Proposed", className: "bg-blue-500/15 text-blue-400 border-blue-500/20" },
  testing: { label: "Testing", className: "bg-amber-400/15 text-amber-400 border-amber-400/20" },
  supported: { label: "Supported", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
  refuted: { label: "Refuted", className: "bg-red-500/15 text-red-400 border-red-500/20" },
} as const;

const SCORE_CONFIG = [
  { key: "novelty_score" as const, label: "Novelty", color: "bg-indigo-500" },
  { key: "feasibility_score" as const, label: "Feasibility", color: "bg-emerald-500" },
  { key: "evidence_score" as const, label: "Evidence", color: "bg-cyan-500" },
  { key: "cost_estimate" as const, label: "Cost (inv.)", color: "bg-amber-400", invert: true },
];

function ScoreBar({ label, value, color, invert = false }: { label: string; value: number; color: string; invert?: boolean }) {
  const displayValue = invert ? 1 - Math.min(1, value) : Math.min(1, value);
  const pct = Math.round(displayValue * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-zinc-500 w-20 shrink-0">{label}</span>
      <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-zinc-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

function HypothesisCard({ hyp }: { hyp: Hypothesis }) {
  const status = STATUS_CONFIG[hyp.status];
  return (
    <div className="bg-zinc-800/40 rounded-lg border border-zinc-800 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono text-zinc-600 w-4">#{hyp.rank}</span>
          <span
            className={cn(
              "text-[11px] font-medium px-1.5 py-0.5 rounded border",
              status.className
            )}
          >
            {status.label}
          </span>
        </div>
        <span className="text-xs font-mono text-indigo-400 shrink-0">
          {Math.round(hyp.composite_score * 100)}%
        </span>
      </div>

      <p className="text-sm text-zinc-200 leading-relaxed">{hyp.statement}</p>

      <div className="space-y-1.5">
        {SCORE_CONFIG.map((s) => (
          <ScoreBar
            key={s.key}
            label={s.label}
            value={hyp[s.key]}
            color={s.color}
            invert={s.invert}
          />
        ))}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={() => alert("Debate feature coming in a future phase.")}
          className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-indigo-400 bg-zinc-800 hover:bg-indigo-500/10 border border-zinc-700 hover:border-indigo-500/30 rounded-md px-3 py-1.5 transition-colors"
        >
          <Swords size={12} />
          Debate this
        </button>
        <button
          type="button"
          onClick={() => alert("Experiment planning coming in a future phase.")}
          className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-emerald-400 bg-zinc-800 hover:bg-emerald-500/10 border border-zinc-700 hover:border-emerald-500/30 rounded-md px-3 py-1.5 transition-colors"
        >
          <FlaskConical size={12} />
          Plan experiment
        </button>
      </div>
    </div>
  );
}

function HypothesisSetAccordion({ set }: { set: HypothesisSet }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-zinc-800/40 transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-start gap-3 min-w-0">
          <span className="text-xs font-mono text-zinc-600 mt-0.5 shrink-0">
            {new Date(set.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-zinc-200 truncate">{set.query}</p>
            <p className="text-xs text-zinc-500 mt-0.5">
              {set.hypotheses.length} hypothesis{set.hypotheses.length !== 1 ? "es" : ""}
              {set.debate_id && " · debated"}
            </p>
          </div>
        </div>
        {open ? (
          <ChevronUp size={16} className="text-zinc-500 shrink-0" />
        ) : (
          <ChevronDown size={16} className="text-zinc-500 shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-3 border-t border-zinc-800">
          <div className="h-4" />
          {set.hypotheses.map((hyp) => (
            <HypothesisCard key={hyp.hypothesis_id} hyp={hyp} />
          ))}
        </div>
      )}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5 animate-pulse">
      <div className="h-4 bg-zinc-800 rounded w-3/4 mb-2" />
      <div className="h-3 bg-zinc-800 rounded w-1/4" />
    </div>
  );
}

export default function HypothesesPage() {
  const { data: sets, isLoading, error } = useQuery({
    queryKey: ["hypotheses"],
    queryFn: () => api.hypotheses.list("default", 20),
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-50">Hypotheses</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Ask the AI to{" "}
          <span className="font-mono text-indigo-400 text-xs bg-indigo-500/10 px-1.5 py-0.5 rounded">
            generate hypotheses for [your question]
          </span>{" "}
          in the Chat.
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
          Failed to load hypotheses. Is the backend running?
        </div>
      )}

      {!isLoading && !error && sets && sets.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-4xl mb-4" aria-hidden="true">💡</span>
          <p className="text-zinc-400 text-sm font-medium">No hypotheses yet</p>
          <p className="text-zinc-600 text-xs mt-1 max-w-xs">
            Ask the AI to &quot;generate hypotheses for [question]&quot; in the Chat page.
          </p>
        </div>
      )}

      {!isLoading && sets && sets.length > 0 && (
        <div className="space-y-3">
          {sets.map((set) => (
            <HypothesisSetAccordion key={set.set_id} set={set} />
          ))}
        </div>
      )}
    </div>
  );
}
