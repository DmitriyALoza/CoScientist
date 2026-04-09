import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short", day: "numeric", year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso.slice(0, 10);
  }
}

export function formatDomain(domain: string): string {
  const map: Record<string, string> = {
    flow_cytometry: "Flow Cytometry",
    ihc: "IHC",
    cell_culture: "Cell Culture",
    imaging: "Imaging",
    wet_lab: "Wet Lab",
    other: "General",
  };
  return map[domain] ?? domain;
}

export function domainColor(domain: string): string {
  const map: Record<string, string> = {
    flow_cytometry: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    ihc: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    cell_culture: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    imaging: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    wet_lab: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    other: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
  };
  return map[domain] ?? map.other;
}
