"use client";

import { cn } from "@/lib/utils";
import type { PTMSite, PTMStatus } from "@/lib/types";

const STATUS_STYLES: Record<PTMStatus, { bg: string; label: string }> = {
  conserved:       { bg: "bg-emerald-500/20 text-emerald-400", label: "C" },
  shifted:         { bg: "bg-amber-500/20 text-amber-400",     label: "S" },
  residue_changed: { bg: "bg-orange-500/20 text-orange-400",   label: "R" },
  no_evidence:     { bg: "bg-zinc-800 text-zinc-600",          label: "—" },
};

const LEGEND: { status: PTMStatus; label: string; description: string }[] = [
  { status: "conserved",       label: "C", description: "Conserved" },
  { status: "shifted",         label: "S", description: "Shifted (±5 aa)" },
  { status: "residue_changed", label: "R", description: "Residue changed" },
  { status: "no_evidence",     label: "—", description: "No evidence" },
];

export function PTMGrid({ ptmSites }: { ptmSites: PTMSite[] }) {
  if (ptmSites.length === 0) {
    return <p className="text-sm text-zinc-500 py-4 text-center">No PTM annotations retrieved.</p>;
  }

  const allSpecies = Array.from(
    new Set(ptmSites.flatMap((s) => Object.keys(s.species_status).filter((k) => k !== "human")))
  );

  return (
    <div className="space-y-3">
      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {LEGEND.map(({ status, label, description }) => (
          <div key={status} className="flex items-center gap-1.5">
            <span className={cn("w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center",
              STATUS_STYLES[status].bg)}>
              {label}
            </span>
            <span className="text-xs text-zinc-500">{description}</span>
          </div>
        ))}
      </div>

      {/* Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Residue</th>
              <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">PTM Type</th>
              {allSpecies.map((sp) => (
                <th key={sp} className="text-center py-2 px-3 text-xs font-medium text-zinc-500 capitalize">
                  {sp}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ptmSites.map((site) => (
              <tr key={`${site.residue}-${site.ptm_type}`} className="border-b border-zinc-800/50 hover:bg-zinc-800/20">
                <td className="py-2 px-3 font-mono text-xs text-indigo-300">{site.residue}</td>
                <td className="py-2 px-3 text-xs text-zinc-400 max-w-[180px] truncate" title={site.ptm_type}>
                  {site.ptm_type}
                </td>
                {allSpecies.map((sp) => {
                  const status = (site.species_status[sp] ?? "no_evidence") as PTMStatus;
                  const style = STATUS_STYLES[status];
                  return (
                    <td key={sp} className="py-2 px-3 text-center">
                      <span
                        className={cn("inline-flex items-center justify-center w-6 h-6 rounded text-[10px] font-bold", style.bg)}
                        title={status.replace(/_/g, " ")}
                      >
                        {style.label}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
