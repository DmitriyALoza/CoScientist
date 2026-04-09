"use client";
import type { KBStats } from "@/lib/types";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface KBPieChartProps {
  stats: KBStats;
}

const COLLECTION_CONFIG: Record<string, { label: string; color: string }> = {
  papers: { label: "Papers", color: "#6366f1" },
  sops_internal: { label: "SOPs (Internal)", color: "#10b981" },
  sops_manufacturer: { label: "SOPs (Mfr)", color: "#06b6d4" },
  reports: { label: "Reports", color: "#f59e0b" },
  eln_entries: { label: "ELN Entries", color: "#a855f7" },
  reference_docs: { label: "Reference Docs", color: "#f43f5e" },
};

const DEFAULT_COLOR = "#71717a";

export function KBPieChart({ stats }: KBPieChartProps) {
  const data = Object.entries(stats.by_collection)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({
      name: key,
      label: COLLECTION_CONFIG[key]?.label ?? key,
      value: count,
      color: COLLECTION_CONFIG[key]?.color ?? DEFAULT_COLOR,
    }));

  const isEmpty = data.length === 0 || stats.total_documents === 0;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-zinc-400">Knowledge Base</h3>
        <span className="text-xs text-zinc-500 font-mono">
          {stats.total_documents} docs
        </span>
      </div>

      {isEmpty ? (
        <div className="flex items-center justify-center h-40 text-zinc-600 text-sm">
          No documents ingested yet
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f4f4f5",
                }}
                formatter={(value, name) => [
                  value,
                  COLLECTION_CONFIG[String(name)]?.label ?? String(name),
                ]}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="w-full grid grid-cols-2 gap-x-4 gap-y-2">
            {data.map((entry) => (
              <div key={entry.name} className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-xs text-zinc-400 truncate">{entry.label}</span>
                <span className="text-xs text-zinc-600 ml-auto font-mono shrink-0">
                  {entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
