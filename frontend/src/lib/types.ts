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

// ── Cross-Species Target Intelligence ─────────────────────────
export interface ResolvedTarget {
  gene_symbol: string;
  protein_name: string;
  uniprot_id: string;
  organism: string;
  synonyms: string[];
}

export interface Ortholog {
  species: string;
  uniprot_id: string;
  gene_symbol: string;
  percent_identity: number;
  sequence_length: number;
  mapping_confidence: "high" | "moderate" | "low";
}

export type PTMStatus = "conserved" | "shifted" | "residue_changed" | "no_evidence";

export interface PTMSite {
  residue: string;
  ptm_type: string;
  position: number;
  species_status: Record<string, PTMStatus>;
  evidence_source: string;
}

export interface AntibodyRecord {
  ab_id: string;
  clone_name: string | null;
  vendor: string;
  catalog_number: string | null;
  host_species: string | null;
  reactivity_species: string[];
  applications: string[];
  epitope_info: string | null;
  validation_source: string | null;
}

export interface ConservationSummary {
  ortholog_conservation: "High" | "Moderate" | "Low" | "Unclear";
  ptm_conservation: "High" | "Moderate" | "Unclear";
  antibody_coverage: "Strong" | "Partial" | "Limited";
  translational_risk: "Low" | "Moderate" | "High" | "Unclear";
}

export interface TargetAnalysisRun {
  analysis_id: string;
  user_id: string;
  target_input: string;
  comparison_species: string[];
  ptm_filter: string[];
  tissue_filter: string | null;
  status: "pending" | "running" | "complete" | "error";
  resolved_target: ResolvedTarget | null;
  orthologs: Ortholog[];
  ptm_sites: PTMSite[];
  antibodies: AntibodyRecord[];
  conservation_summary: ConservationSummary | null;
  ai_interpretation: string | null;
  warnings: string[];
  created_at: string;
  completed_at: string | null;
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
