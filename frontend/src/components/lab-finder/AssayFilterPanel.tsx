"use client";

import { cn } from "@/lib/utils";
import type { AssayCategory } from "./types";

interface AssayFilterPanelProps {
  categories: AssayCategory[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
}

export function AssayFilterPanel({ categories, selectedIds, onToggle }: AssayFilterPanelProps) {
  const allSelected = selectedIds.size === categories.length;

  const handleSelectAll = () => {
    if (allSelected) {
      categories.forEach((c) => { if (selectedIds.has(c.id)) onToggle(c.id); });
    } else {
      categories.forEach((c) => { if (!selectedIds.has(c.id)) onToggle(c.id); });
    }
  };

  return (
    <div className="w-64 shrink-0 flex flex-col bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-zinc-200">Assay Types</span>
          {selectedIds.size > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 font-medium">
              {selectedIds.size}
            </span>
          )}
        </div>
        <button
          onClick={handleSelectAll}
          className="text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {allSelected ? "Clear all" : "Select all"}
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto py-2">
        {categories.map((cat) => {
          const checked = selectedIds.has(cat.id);
          return (
            <label
              key={cat.id}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors hover:bg-zinc-800/40",
                checked && "bg-zinc-800/20"
              )}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(cat.id)}
                className="sr-only"
              />
              {/* Custom checkbox */}
              <span
                className={cn(
                  "w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors",
                  checked
                    ? "bg-indigo-500 border-indigo-500"
                    : "border-zinc-600 bg-transparent"
                )}
              >
                {checked && (
                  <svg viewBox="0 0 10 8" className="w-2.5 h-2 fill-white">
                    <path d="M1 4l3 3 5-6" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </span>
              <span className={cn("text-xs px-2 py-0.5 rounded-full border font-medium", cat.color)}>
                {cat.label}
              </span>
            </label>
          );
        })}
      </div>

      <div className="px-4 py-2 border-t border-zinc-800">
        <p className="text-[10px] text-zinc-600 leading-relaxed">
          Select assay types to search for nearby labs that offer these services.
        </p>
      </div>
    </div>
  );
}
