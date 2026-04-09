"use client";
import { useState, useRef, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { KBStats } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Upload, Search, FileText, AlertTriangle } from "lucide-react";

const COLLECTIONS = [
  { value: "papers", label: "Research Papers" },
  { value: "sops_internal", label: "SOPs (Internal)" },
  { value: "sops_manufacturer", label: "SOPs (Manufacturer)" },
  { value: "reports", label: "Reports" },
  { value: "reference_docs", label: "Reference Docs" },
] as const;

const COLLECTION_COLORS: Record<string, string> = {
  papers: "text-indigo-400",
  sops_internal: "text-emerald-400",
  sops_manufacturer: "text-cyan-400",
  reports: "text-amber-400",
  eln_entries: "text-purple-400",
  reference_docs: "text-rose-400",
};

function KBStatsPanel({ stats }: { stats: KBStats }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-zinc-400">Total Documents</p>
        <span className="text-sm font-bold text-zinc-50 font-mono">
          {stats.total_documents}
        </span>
      </div>
      <div className="border-t border-zinc-800 pt-3 space-y-2">
        {Object.entries(stats.by_collection).map(([key, count]) => (
          <div key={key} className="flex items-center justify-between">
            <span className={cn("text-xs", COLLECTION_COLORS[key] ?? "text-zinc-400")}>
              {key.replace(/_/g, " ")}
            </span>
            <span className="text-xs font-mono text-zinc-500">{count}</span>
          </div>
        ))}
        {Object.keys(stats.by_collection).length === 0 && (
          <p className="text-xs text-zinc-600">No documents ingested yet.</p>
        )}
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [collection, setCollection] = useState<string>("papers");
  const [searchQuery, setSearchQuery] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: kbStats } = useQuery({
    queryKey: ["kb-stats"],
    queryFn: () => api.kb.stats("default"),
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleIngest = async () => {
    if (!selectedFile) return;
    setIngesting(true);
    // Placeholder — actual upload handled in a future phase
    await new Promise((r) => setTimeout(r, 1500));
    setIngesting(false);
    alert(
      `Ingest via CLI: uv run eln --ingest "${selectedFile.name}" --kb-type ${collection}`
    );
    setSelectedFile(null);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-50">Documents</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Manage your knowledge base — papers, SOPs, and reference documents.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Upload */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-zinc-300">Ingest Document</h2>

          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 cursor-pointer transition-colors",
              dragging
                ? "border-indigo-500 bg-indigo-500/10"
                : "border-zinc-700 hover:border-zinc-600 bg-zinc-900 hover:bg-zinc-800/40"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="sr-only"
              onChange={handleFileSelect}
              aria-label="Select file to ingest"
            />
            <Upload
              size={28}
              className={cn(dragging ? "text-indigo-400" : "text-zinc-600")}
            />
            {selectedFile ? (
              <div className="text-center">
                <p className="text-sm font-medium text-zinc-200 flex items-center gap-2">
                  <FileText size={14} className="text-indigo-400" />
                  {selectedFile.name}
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  {(selectedFile.size / 1024).toFixed(0)} KB
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-zinc-400">
                  Drop a PDF or text file here
                </p>
                <p className="text-xs text-zinc-600 mt-1">or click to browse</p>
              </div>
            )}
          </div>

          {/* Collection selector */}
          <div>
            <label htmlFor="collection" className="block text-xs font-medium text-zinc-400 mb-1.5">
              Collection
            </label>
            <select
              id="collection"
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {COLLECTIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Ingest button */}
          <button
            type="button"
            onClick={handleIngest}
            disabled={!selectedFile || ingesting}
            className={cn(
              "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
              selectedFile && !ingesting
                ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                : "bg-zinc-800 text-zinc-600 cursor-not-allowed"
            )}
          >
            {ingesting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Ingesting...
              </>
            ) : (
              <>
                <Upload size={14} />
                Ingest Document
              </>
            )}
          </button>
        </div>

        {/* Right: KB stats + search */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-zinc-300">Knowledge Base</h2>

          {/* Search box */}
          <div className="relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search knowledge base..."
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-9 pr-4 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {searchQuery && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-sm text-zinc-500">
              Search via Chat or CLI:{" "}
              <code className="font-mono text-xs bg-zinc-800 px-1.5 py-0.5 rounded">
                uv run eln --search &quot;{searchQuery}&quot;
              </code>
            </div>
          )}

          {/* KB stats */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5">
            <h3 className="text-sm font-medium text-zinc-400 mb-4">
              Collection Stats
            </h3>
            {kbStats ? (
              <KBStatsPanel stats={kbStats} />
            ) : (
              <div className="space-y-2 animate-pulse">
                <div className="h-3 bg-zinc-800 rounded w-3/4" />
                <div className="h-3 bg-zinc-800 rounded w-1/2" />
                <div className="h-3 bg-zinc-800 rounded w-2/3" />
              </div>
            )}
          </div>

          {/* CLI hint */}
          <div className="bg-zinc-800/40 rounded-lg border border-zinc-800 p-4 text-xs font-mono text-zinc-500 leading-relaxed">
            <p className="text-zinc-400 font-sans font-medium mb-2 text-xs">CLI usage</p>
            <p>uv run eln --ingest paper.pdf --kb-type papers</p>
            <p>uv run eln --ingest sop.pdf --kb-type sops_internal</p>
            <p>uv run eln --search &quot;flow cytometry protocol&quot;</p>
          </div>
        </div>
      </div>

      {/* Coming soon: R Analysis import */}
      <div className="flex items-start gap-3 bg-amber-400/8 border border-amber-400/20 rounded-xl p-4">
        <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-400">R Analysis Import — Coming Soon</p>
          <p className="text-xs text-zinc-500 mt-1">
            Import and analyze R scripts, Rmd notebooks, and statistical outputs directly
            in CoScientist. This premium feature will be available in a future release.
          </p>
        </div>
      </div>
    </div>
  );
}
