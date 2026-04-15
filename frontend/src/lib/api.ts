import type { DashboardMetrics, HypothesisSet, ExperimentLoop, RunIndex, KBStats, TargetAnalysisRun } from "./types";

const API_BASE =
  typeof window === "undefined"
    ? (process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string }>("/api/health"),

  metrics: (userId = "default") =>
    get<DashboardMetrics>("/api/metrics", { user_id: userId }),

  runs: {
    list: (userId = "default", limit = 20) =>
      get<RunIndex[]>("/api/runs", { user_id: userId, limit: String(limit) }),
    create: (body: { title: string; domain?: string; objective?: string; user_id?: string }) =>
      post<{ run_id: string }>("/api/runs", body),
    get: (runId: string, userId = "default") =>
      get<Record<string, unknown>>(`/api/runs/${runId}`, { user_id: userId }),
    eln: (runId: string, userId = "default") =>
      get<{ content: string }>(`/api/runs/${runId}/eln`, { user_id: userId }),
  },

  hypotheses: {
    list: (userId = "default", limit = 20) =>
      get<HypothesisSet[]>("/api/hypotheses", { user_id: userId, limit: String(limit) }),
    get: (setId: string, userId = "default") =>
      get<HypothesisSet>(`/api/hypotheses/${setId}`, { user_id: userId }),
  },

  experiments: {
    list: (userId = "default", limit = 20) =>
      get<ExperimentLoop[]>("/api/experiments", { user_id: userId, limit: String(limit) }),
  },

  kb: {
    stats: (userId = "default") =>
      get<KBStats>("/api/kb/stats", { user_id: userId }),
    search: (query: string, collection = "papers", userId = "default") =>
      post<unknown[]>("/api/kb/search", { query, collection, user_id: userId }),
  },

  targetAnalysis: {
    run: (body: {
      target: string;
      reference_species?: string;
      comparison_species?: string[];
      ptm_types?: string[];
      tissue_filter?: string;
      user_id?: string;
    }) => post<TargetAnalysisRun>("/api/target-analysis", body),

    list: (userId = "default", limit = 20) =>
      get<TargetAnalysisRun[]>("/api/target-analyses", { user_id: userId, limit: String(limit) }),

    get: (analysisId: string, userId = "default") =>
      get<TargetAnalysisRun>(`/api/target-analyses/${analysisId}`, { user_id: userId }),
  },

  wsUrl: () => (API_BASE.replace(/^http/, "ws") + "/api/chat"),
};
