import { api } from "@/lib/api";
import type { DashboardMetrics } from "@/lib/types";
import { PageShell } from "@/components/layout/PageShell";
import { StatCard } from "@/components/dashboard/StatCard";
import { RecentRunsTable } from "@/components/dashboard/RecentRunsTable";
import { KBPieChart } from "@/components/dashboard/KBPieChart";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import {
  FileText,
  Quote,
  Lightbulb,
  FlaskConical,
} from "lucide-react";

const EMPTY_METRICS: DashboardMetrics = {
  eln_count: 0,
  citation_count: 0,
  hypothesis_count: 0,
  testing_count: 0,
  active_experiments: 0,
  completed_experiments: 0,
  deviation_count: 0,
  recent_runs: [],
  kb_stats: { by_collection: {}, total_documents: 0 },
  activity: [],
};

const HYPOTHESIS_STATUSES = [
  { label: "Proposed", key: "proposed", color: "bg-blue-500" },
  { label: "Testing", key: "testing", color: "bg-amber-400" },
  { label: "Supported", key: "supported", color: "bg-emerald-500" },
  { label: "Refuted", key: "refuted", color: "bg-red-500" },
] as const;

export default async function DashboardPage() {
  let metrics: DashboardMetrics = EMPTY_METRICS;

  try {
    metrics = await api.metrics("default");
  } catch {
    // Backend not available — show empty state
  }

  return (
    <PageShell title="Dashboard" subtitle="Workspace overview">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="ELNs Generated"
          value={metrics.eln_count}
          icon={<FileText size={16} />}
          color="indigo"
          subtitle="Total lab notebooks"
        />
        <StatCard
          title="Citations"
          value={metrics.citation_count}
          icon={<Quote size={16} />}
          color="emerald"
          subtitle="Across all runs"
        />
        <StatCard
          title="Hypotheses"
          value={metrics.hypothesis_count}
          icon={<Lightbulb size={16} />}
          color="amber"
          subtitle={`${metrics.testing_count} under testing`}
        />
        <StatCard
          title="Active Experiments"
          value={metrics.active_experiments}
          icon={<FlaskConical size={16} />}
          color="cyan"
          subtitle={`${metrics.completed_experiments} completed`}
        />
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RecentRunsTable runs={metrics.recent_runs} />
        <KBPieChart stats={metrics.kb_stats} />
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Hypothesis status distribution */}
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Hypothesis Status</h3>
          <div className="space-y-3">
            {HYPOTHESIS_STATUSES.map(({ label, color }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="flex items-center gap-2 w-24 shrink-0">
                  <span className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-xs text-zinc-400">{label}</span>
                </div>
                <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${color} opacity-70`}
                    style={{
                      width:
                        metrics.hypothesis_count > 0
                          ? `${Math.round(
                              (label === "Proposed"
                                ? metrics.hypothesis_count - metrics.testing_count
                                : label === "Testing"
                                ? metrics.testing_count
                                : 0) /
                                metrics.hypothesis_count *
                                100
                            )}%`
                          : "0%",
                    }}
                  />
                </div>
                <span className="text-xs font-mono text-zinc-600 w-6 text-right">
                  {label === "Proposed"
                    ? Math.max(0, metrics.hypothesis_count - metrics.testing_count)
                    : label === "Testing"
                    ? metrics.testing_count
                    : 0}
                </span>
              </div>
            ))}
          </div>

          {metrics.hypothesis_count === 0 && (
            <p className="text-xs text-zinc-600 mt-4">
              No hypotheses generated yet.
            </p>
          )}
        </div>

        <ActivityFeed items={metrics.activity} />
      </div>
    </PageShell>
  );
}
