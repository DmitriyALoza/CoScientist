import type { RunIndex } from "@/lib/types";
import { formatDate, formatDomain, domainColor } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface RecentRunsTableProps {
  runs: RunIndex[];
}

export function RecentRunsTable({ runs }: RecentRunsTableProps) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-800">
        <h3 className="text-sm font-medium text-zinc-400">Recent Runs</h3>
      </div>

      {runs.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-zinc-500 text-sm">
          No runs yet
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table-auto w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="px-5 py-3 text-left text-xs text-zinc-500 uppercase tracking-wider font-medium">
                  Title
                </th>
                <th className="px-5 py-3 text-left text-xs text-zinc-500 uppercase tracking-wider font-medium">
                  Domain
                </th>
                <th className="px-5 py-3 text-left text-xs text-zinc-500 uppercase tracking-wider font-medium">
                  Date
                </th>
                <th className="px-5 py-3 text-left text-xs text-zinc-500 uppercase tracking-wider font-medium">
                  ELN
                </th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.run_id}
                  className="border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/40 transition-colors"
                >
                  <td className="px-5 py-3 text-sm text-zinc-200 font-medium max-w-[180px] truncate">
                    {run.title}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center text-xs px-2 py-0.5 rounded-md border",
                        domainColor(run.domain)
                      )}
                    >
                      {formatDomain(run.domain)}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-zinc-400 whitespace-nowrap">
                    {formatDate(run.timestamp)}
                  </td>
                  <td className="px-5 py-3 text-sm">
                    {run.has_eln ? (
                      <span className="text-emerald-400" title="ELN generated">
                        ✓
                      </span>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
