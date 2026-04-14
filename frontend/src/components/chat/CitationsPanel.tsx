"use client";

import { BookOpen, ExternalLink } from "lucide-react";
import type { Citation } from "@/lib/types";

const SOURCE_LABELS: Record<string, string> = {
  pubmed: "PubMed",
  semantic_scholar: "Semantic Scholar",
  local_kb: "Knowledge Base",
  kb: "Knowledge Base",
  arxiv: "arXiv",
};

interface Props {
  citations: Citation[];
}

export function CitationsPanel({ citations }: Props) {
  return (
    <div className="w-72 shrink-0 border-l border-zinc-800 bg-zinc-900 overflow-y-auto flex flex-col">
      <div className="px-4 py-3 border-b border-zinc-800">
        <h3 className="text-xs font-semibold text-zinc-300">Citations</h3>
        <p className="text-[10px] text-zinc-600 mt-0.5">{citations.length} source{citations.length !== 1 ? "s" : ""} collected</p>
      </div>

      {citations.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 gap-2 p-6 text-center">
          <BookOpen size={20} className="text-zinc-700" />
          <p className="text-xs text-zinc-600">Citations will appear here as the AI finds supporting evidence.</p>
        </div>
      ) : (
        <div className="p-3 space-y-2">
          {citations.map((c) => (
            <div
              key={c.citation_id}
              className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 space-y-1.5"
            >
              {/* Source type badge */}
              <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {SOURCE_LABELS[c.source_type] ?? c.source_type}
              </span>

              {/* Title */}
              {c.title && (
                <p className="text-xs font-medium text-zinc-200 leading-snug">{c.title}</p>
              )}

              {/* Authors + year */}
              {(c.authors?.length || c.year) && (
                <p className="text-[10px] text-zinc-500">
                  {c.authors?.slice(0, 3).join(", ")}
                  {c.authors && c.authors.length > 3 && " et al."}
                  {c.year && ` (${c.year})`}
                </p>
              )}

              {/* Excerpt */}
              {c.excerpt && (
                <p className="text-[10px] text-zinc-500 italic leading-snug line-clamp-3">
                  "{c.excerpt}"
                </p>
              )}

              {/* External link if source_id looks like a URL or PMID */}
              {c.source_id && c.source_type === "pubmed" && (
                <a
                  href={`https://pubmed.ncbi.nlm.nih.gov/${c.source_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300"
                >
                  <ExternalLink size={10} />
                  View on PubMed
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
