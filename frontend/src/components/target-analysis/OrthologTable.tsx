"use client";

import { cn } from "@/lib/utils";
import type { Ortholog } from "@/lib/types";

const CONFIDENCE_COLORS: Record<string, string> = {
  high:     "bg-emerald-500/10 text-emerald-400",
  moderate: "bg-amber-500/10 text-amber-400",
  low:      "bg-red-500/10 text-red-400",
};

function IdentityBar({ value }: { value: number }) {
  const color = value >= 85 ? "bg-emerald-500" : value >= 60 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-zinc-800">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs text-zinc-300 w-12 text-right tabular-nums">{value.toFixed(1)}%</span>
    </div>
  );
}

export function OrthologTable({ orthologs }: { orthologs: Ortholog[] }) {
  if (orthologs.length === 0) {
    return <p className="text-sm text-zinc-500 py-4 text-center">No orthologs found.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Species</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Gene</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">UniProt</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500 w-48">% Identity</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Length</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {orthologs.map((orth) => (
            <tr key={orth.uniprot_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20">
              <td className="py-2.5 px-3 text-zinc-300 capitalize">{orth.species}</td>
              <td className="py-2.5 px-3 font-mono text-indigo-400 text-xs">{orth.gene_symbol}</td>
              <td className="py-2.5 px-3">
                <a
                  href={`https://www.uniprot.org/uniprotkb/${orth.uniprot_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-xs text-zinc-400 hover:text-indigo-400 transition-colors"
                >
                  {orth.uniprot_id}
                </a>
              </td>
              <td className="py-2.5 px-3">
                <IdentityBar value={orth.percent_identity} />
              </td>
              <td className="py-2.5 px-3 text-zinc-500 text-xs tabular-nums">{orth.sequence_length} aa</td>
              <td className="py-2.5 px-3">
                <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full capitalize",
                  CONFIDENCE_COLORS[orth.mapping_confidence] ?? "bg-zinc-500/10 text-zinc-400")}>
                  {orth.mapping_confidence}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
