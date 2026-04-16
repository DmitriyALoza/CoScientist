"use client";

import { Loader2, MapPin, Navigation } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SearchStatus } from "./types";

const RADIUS_OPTIONS = [
  { label: "500 m", value: 500 },
  { label: "1 km", value: 1000 },
  { label: "5 km", value: 5000 },
  { label: "10 km", value: 10000 },
  { label: "25 km", value: 25000 },
];

interface MapSearchControlsProps {
  status: SearchStatus;
  radius: number;
  onRadiusChange: (r: number) => void;
  onSearch: () => void;
  resultCount: number;
  disabled: boolean;
}

export function MapSearchControls({
  status,
  radius,
  onRadiusChange,
  onSearch,
  resultCount,
  disabled,
}: MapSearchControlsProps) {
  const isLoading = status === "locating" || status === "searching";
  const buttonLabel =
    status === "locating" ? "Getting location…" :
    status === "searching" ? "Searching…" :
    "Search Near Me";

  return (
    <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
      {/* Search button */}
      <button
        onClick={onSearch}
        disabled={disabled || isLoading}
        className={cn(
          "flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium shadow-lg transition-colors",
          disabled || isLoading
            ? "bg-zinc-800 text-zinc-600 cursor-not-allowed"
            : "bg-indigo-600 text-white hover:bg-indigo-500"
        )}
      >
        {isLoading
          ? <Loader2 size={14} className="animate-spin" />
          : <Navigation size={14} />
        }
        {buttonLabel}
        {status === "results" && resultCount > 0 && (
          <span className="ml-1 px-1.5 py-0.5 rounded-full bg-white/20 text-[10px] font-semibold">
            {resultCount}
          </span>
        )}
      </button>

      {/* Radius select */}
      <select
        value={radius}
        onChange={(e) => onRadiusChange(Number(e.target.value))}
        className="bg-zinc-900/90 border border-zinc-700 rounded-lg px-2.5 py-2 text-xs text-zinc-300 shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 backdrop-blur"
      >
        {RADIUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>

      {/* Empty state badge */}
      {status === "empty" && (
        <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-zinc-900/90 border border-zinc-700 text-xs text-zinc-400 shadow-lg backdrop-blur">
          <MapPin size={12} />
          No labs found — try a wider radius
        </div>
      )}

      {/* Error badge */}
      {status === "error" && (
        <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 shadow-lg backdrop-blur">
          Location access denied
        </div>
      )}
    </div>
  );
}
