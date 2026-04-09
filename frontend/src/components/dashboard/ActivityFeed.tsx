import type { ActivityItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5">
      <h3 className="text-sm font-medium text-zinc-400 mb-4">Recent Activity</h3>

      {items.length === 0 ? (
        <div className="flex items-center justify-center py-8 text-zinc-600 text-sm">
          No activity yet
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="mt-1.5 w-2 h-2 rounded-full bg-indigo-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-zinc-200 leading-snug">{item.label}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{formatDate(item.ts)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
