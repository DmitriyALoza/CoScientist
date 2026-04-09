// TypeScript mirrors of the Python Pydantic models

export type Domain =
  | "flow_cytometry"
  | "ihc"
  | "cell_culture"
  | "imaging"
  | "wet_lab"
  | "other";

export interface RunIndex {
  run_id: string;
  title: string;
  domain: Domain | string;
  timestamp: string;
  has_eln: boolean;
  chat_session_count?: number;
}

export interface Hypothesis {
  hypothesis_id: string;
  statement: string;
  novelty_score: number;
  feasibility_score: number;
  evidence_score: number;
  cost_estimate: number;
  composite_score: number;
  rank: number;
  status: "proposed" | "testing" | "supported" | "refuted";
  supporting_citations?: string[];
}

export interface HypothesisSet {
  set_id: string;
  query: string;
  hypotheses: Hypothesis[];
  created_at: string;
  debate_id?: string;
}

export interface Experiment {
  experiment_id: string;
  hypothesis_id?: string;
  run_id?: string;
  protocol: string;
  parameters: Record<string, string>;
  expected_outcome: string;
  actual_result?: string;
  success_metric: string;
  status: "planned" | "running" | "completed" | "failed";
  iteration: number;
  created_at: string;
  completed_at?: string;
}

export interface ExperimentLoop {
  loop_id: string;
  hypothesis_id?: string;
  experiments: Experiment[];
  current_iteration: number;
  max_iterations: number;
  status: "active" | "converged" | "exhausted" | "abandoned";
  learnings: string[];
}

export interface Citation {
  citation_id: string;
  source_type: string;
  source_id?: string;
  title?: string;
  authors?: string[];
  year?: number;
  excerpt?: string;
  location?: string;
}

export interface KBStats {
  by_collection: Record<string, number>;
  total_documents: number;
}

export interface DashboardMetrics {
  eln_count: number;
  citation_count: number;
  hypothesis_count: number;
  testing_count: number;
  active_experiments: number;
  completed_experiments: number;
  deviation_count: number;
  recent_runs: RunIndex[];
  kb_stats: KBStats;
  activity: ActivityItem[];
}

export interface ActivityItem {
  type: string;
  label: string;
  ts: string;
}

// Chat
export type ChatMode = "normal" | "validation" | "protocol";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  citations?: Citation[];
  timestamp: number;
}

export interface AttachedDoc {
  name: string;
  text: string;
  chars: number;
}

// WebSocket message types
export type WsServerMessage =
  | { type: "token"; text: string; agent?: string }
  | { type: "citation"; citation: Citation }
  | { type: "tool_call"; tool_call: Record<string, unknown> }
  | { type: "done"; thread_id: string; agent?: string }
  | { type: "error"; message: string };
