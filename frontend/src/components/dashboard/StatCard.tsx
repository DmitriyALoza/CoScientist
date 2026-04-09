import { cn } from "@/lib/utils";

interface TrendProps {
  value: number;
  label: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: TrendProps;
  color?: "indigo" | "emerald" | "amber" | "cyan";
}

const colorMap = {
  indigo: "bg-indigo-500/15 text-indigo-400",
  emerald: "bg-emerald-500/15 text-emerald-400",
  amber: "bg-amber-400/15 text-amber-400",
  cyan: "bg-cyan-500/15 text-cyan-400",
};

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = "indigo",
}: StatCardProps) {
  const iconBg = colorMap[color];
  const isPositive = trend && trend.value >= 0;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <p className="text-sm text-zinc-400 font-medium">{title}</p>
        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center shrink-0", iconBg)}>
          {icon}
        </div>
      </div>

      <div>
        <p className="text-3xl font-bold text-zinc-50 tabular-nums">{value}</p>
        {subtitle && <p className="text-xs text-zinc-500 mt-1">{subtitle}</p>}
      </div>

      {trend && (
        <div className="flex items-center gap-1.5 text-xs">
          <span className={cn("font-medium", isPositive ? "text-emerald-400" : "text-red-400")}>
            {isPositive ? "▲" : "▼"} {Math.abs(trend.value)}
          </span>
          <span className="text-zinc-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
