"use client";

import type { AntibodyRecord } from "@/lib/types";

export function AntibodyTable({ antibodies }: { antibodies: AntibodyRecord[] }) {
  if (antibodies.length === 0) {
    return (
      <p className="text-sm text-zinc-500 py-4 text-center">
        No antibody records found. Check vendor sites for commercial availability.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Clone</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Vendor</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Catalog #</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Host</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Reactivity</th>
            <th className="text-left py-2 px-3 text-xs font-medium text-zinc-500">Applications</th>
          </tr>
        </thead>
        <tbody>
          {antibodies.map((ab) => (
            <tr key={ab.ab_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20">
              <td className="py-2.5 px-3 font-mono text-xs text-zinc-300">
                {ab.clone_name ?? <span className="text-zinc-600">—</span>}
              </td>
              <td className="py-2.5 px-3 text-xs text-zinc-400">{ab.vendor || "—"}</td>
              <td className="py-2.5 px-3">
                {ab.validation_source && ab.catalog_number ? (
                  <a
                    href={ab.validation_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    {ab.catalog_number}
                  </a>
                ) : (
                  <span className="font-mono text-xs text-zinc-500">{ab.catalog_number ?? "—"}</span>
                )}
              </td>
              <td className="py-2.5 px-3 text-xs text-zinc-500 capitalize">
                {ab.host_species ?? "—"}
              </td>
              <td className="py-2.5 px-3">
                <div className="flex flex-wrap gap-1">
                  {ab.reactivity_species.slice(0, 4).map((sp) => (
                    <span
                      key={sp}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 capitalize"
                    >
                      {sp}
                    </span>
                  ))}
                  {ab.reactivity_species.length > 4 && (
                    <span className="text-[10px] text-zinc-600">+{ab.reactivity_species.length - 4}</span>
                  )}
                </div>
              </td>
              <td className="py-2.5 px-3">
                <div className="flex flex-wrap gap-1">
                  {ab.applications.slice(0, 3).map((app) => (
                    <span
                      key={app}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                    >
                      {app}
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
