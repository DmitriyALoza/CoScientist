"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Target, AlertTriangle, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { PageShell } from "@/components/layout/PageShell";
import { ConservationBadges } from "@/components/target-analysis/ConservationBadges";
import { OrthologTable } from "@/components/target-analysis/OrthologTable";
import { PTMGrid } from "@/components/target-analysis/PTMGrid";
import { AntibodyTable } from "@/components/target-analysis/AntibodyTable";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { TargetAnalysisRun } from "@/lib/types";

const ALL_SPECIES = ["rat", "mouse", "dog", "cynomolgus monkey", "minipig"];

const EXAMPLE_TARGETS = ["TP53", "EGFR", "BRCA1", "VEGFA", "TNF"];

function Section({
  title,
  count,
  children,
}: {
  title: string;
  count?: number;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-zinc-800/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown size={14} className="text-zinc-500" /> : <ChevronRight size={14} className="text-zinc-500" />}
          <span className="text-sm font-semibold text-zinc-200">{title}</span>
          {count !== undefined && (
            <span className="text-xs text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded-full">{count}</span>
          )}
        </div>
      </button>
      {open && <div className="px-5 pb-5 pt-1">{children}</div>}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 rounded-xl bg-zinc-800" />
        ))}
      </div>
      {[...Array(3)].map((_, i) => (
        <div key={i} className="h-40 rounded-xl bg-zinc-800" />
      ))}
    </div>
  );
}

export default function TargetAnalysisPage() {
  const [targetInput, setTargetInput] = useState("");
  const [selectedSpecies, setSelectedSpecies] = useState<string[]>(["rat", "mouse", "dog"]);
  const [result, setResult] = useState<TargetAnalysisRun | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      api.targetAnalysis.run({
        target: targetInput.trim(),
        comparison_species: selectedSpecies,
        user_id: "default",
      }),
    onSuccess: (data) => setResult(data),
  });

  const toggleSpecies = (sp: string) => {
    setSelectedSpecies((prev) =>
      prev.includes(sp) ? prev.filter((s) => s !== sp) : [...prev, sp],
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetInput.trim() || selectedSpecies.length === 0) return;
    setResult(null);
    mutation.mutate();
  };

  return (
    <PageShell
      title="Target Analysis"
      subtitle="Compare a protein target across preclinical species — orthologs, PTMs, and antibody availability"
    >
      <div className="max-w-6xl space-y-6">
        {/* Input form */}
        <form
          onSubmit={handleSubmit}
          className="bg-zinc-900 rounded-xl border border-zinc-800 p-5 space-y-4"
        >
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 space-y-1.5">
              <label htmlFor="target-input" className="text-xs font-medium text-zinc-400">
                Target protein or gene
              </label>
              <input
                id="target-input"
                type="text"
                value={targetInput}
                onChange={(e) => setTargetInput(e.target.value)}
                placeholder="e.g. TP53, EGFR, BRCA1"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {EXAMPLE_TARGETS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTargetInput(t)}
                    className="text-[11px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 transition-colors font-mono"
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-xs font-medium text-zinc-400">Comparison species</p>
              <div className="flex flex-wrap gap-2">
                {ALL_SPECIES.map((sp) => (
                  <label
                    key={sp}
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs cursor-pointer transition-colors capitalize",
                      selectedSpecies.includes(sp)
                        ? "border-indigo-500/50 bg-indigo-500/10 text-indigo-300"
                        : "border-zinc-700 bg-zinc-800/40 text-zinc-500 hover:border-zinc-600",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={selectedSpecies.includes(sp)}
                      onChange={() => toggleSpecies(sp)}
                      className="sr-only"
                    />
                    {sp}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-zinc-600">
              Data sources: UniProt · OMA Browser · Antibody Registry · Biopython alignment
            </p>
            <button
              type="submit"
              disabled={mutation.isPending || !targetInput.trim() || selectedSpecies.length === 0}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                mutation.isPending || !targetInput.trim() || selectedSpecies.length === 0
                  ? "bg-zinc-800 text-zinc-600 cursor-not-allowed"
                  : "bg-indigo-600 text-white hover:bg-indigo-500",
              )}
            >
              {mutation.isPending && <Loader2 size={14} className="animate-spin" />}
              <Target size={14} />
              {mutation.isPending ? "Analysing…" : "Analyse Target"}
            </button>
          </div>
        </form>

        {/* Loading skeleton */}
        {mutation.isPending && <Skeleton />}

        {/* Error */}
        {mutation.isError && (
          <div className="flex items-start gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/5">
            <AlertTriangle size={16} className="text-red-400 mt-0.5 shrink-0" />
            <p className="text-sm text-red-400">{(mutation.error as Error).message}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="flex gap-5">
            {/* Left: results panels */}
            <div className="flex-1 min-w-0 space-y-4">
              {/* Resolved target header */}
              {result.resolved_target && (
                <div className="flex items-center gap-3 px-5 py-3 bg-zinc-900 rounded-xl border border-zinc-800">
                  <Target size={16} className="text-indigo-400 shrink-0" />
                  <div>
                    <span className="font-semibold text-zinc-100">{result.resolved_target.gene_symbol}</span>
                    <span className="text-zinc-400 text-sm ml-2">{result.resolved_target.protein_name}</span>
                  </div>
                  <a
                    href={`https://www.uniprot.org/uniprotkb/${result.resolved_target.uniprot_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-auto font-mono text-xs text-indigo-400 hover:text-indigo-300"
                  >
                    {result.resolved_target.uniprot_id}
                  </a>
                </div>
              )}

              {/* Conservation badges */}
              {result.conservation_summary && (
                <ConservationBadges summary={result.conservation_summary} />
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="space-y-1.5">
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-amber-400 bg-amber-500/5 border border-amber-500/20 rounded-lg px-3 py-2">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      {w}
                    </div>
                  ))}
                </div>
              )}

              <Section title="Orthologs" count={result.orthologs.length}>
                <OrthologTable orthologs={result.orthologs} />
              </Section>

              <Section title="PTM Conservation" count={result.ptm_sites.length}>
                <PTMGrid ptmSites={result.ptm_sites} />
              </Section>

              <Section title="Antibody Availability" count={result.antibodies.length}>
                <AntibodyTable antibodies={result.antibodies} />
              </Section>
            </div>

            {/* Right: AI interpretation panel */}
            {result.ai_interpretation && (
              <div className="w-72 shrink-0">
                <div className="sticky top-0 bg-zinc-900 rounded-xl border border-zinc-800 p-4 space-y-3 max-h-[calc(100vh-12rem)] overflow-y-auto">
                  <h3 className="text-xs font-semibold text-zinc-300 border-b border-zinc-800 pb-2">
                    AI Interpretation
                  </h3>
                  <div className="prose prose-sm prose-invert max-w-none text-xs prose-p:my-1 prose-headings:text-zinc-200 prose-headings:text-sm prose-ul:my-1 prose-li:my-0.5 prose-strong:text-zinc-200">
                    <ReactMarkdown>{result.ai_interpretation}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!result && !mutation.isPending && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
              <Target size={20} className="text-indigo-400" />
            </div>
            <p className="text-zinc-400 text-sm">Enter a target above to start the analysis</p>
            <p className="text-zinc-600 text-xs max-w-sm">
              The pipeline retrieves orthologs, aligns sequences, maps PTM sites, and searches antibody databases automatically.
            </p>
          </div>
        )}
      </div>
    </PageShell>
  );
}
