"use client";

import { cn } from "@/lib/utils";
import type { ConservationSummary } from "@/lib/types";

const RISK_COLORS: Record<string, string> = {
  High:     "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Moderate: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  Low:      "bg-red-500/10 text-red-400 border-red-500/20",
  Unclear:  "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
  Strong:   "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Partial:  "bg-amber-500/10 text-amber-400 border-amber-500/20",
  Limited:  "bg-red-500/10 text-red-400 border-red-500/20",
};

// Translational risk: Low = good (emerald), High = bad (red)
const RISK_REVERSE: Record<string, string> = {
  Low:     "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Moderate: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  High:    "bg-red-500/10 text-red-400 border-red-500/20",
  Unclear: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
};

interface BadgeProps {
  label: string;
  value: string;
  colorMap?: Record<string, string>;
}

function Badge({ label, value, colorMap = RISK_COLORS }: BadgeProps) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 flex flex-col gap-2">
      <p className="text-xs text-zinc-500 font-medium">{label}</p>
      <span
        className={cn(
          "self-start px-2.5 py-1 rounded-full text-sm font-semibold border",
          (colorMap[value] ?? "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"),
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function ConservationBadges({ summary }: { summary: ConservationSummary }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <Badge label="Ortholog Conservation" value={summary.ortholog_conservation} />
      <Badge label="PTM Conservation"      value={summary.ptm_conservation} />
      <Badge label="Antibody Coverage"     value={summary.antibody_coverage} />
      <Badge label="Translational Risk"    value={summary.translational_risk} colorMap={RISK_REVERSE} />
    </div>
  );
}
