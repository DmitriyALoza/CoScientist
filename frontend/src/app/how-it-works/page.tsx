import { PageShell } from "@/components/layout/PageShell";

interface Agent {
  name: string;
  category: "Core" | "Innovation";
  description: string;
}

const AGENTS: Agent[] = [
  { name: "literature_scout", category: "Core", description: "Finds and extracts methods from papers, producing structured citation objects." },
  { name: "sop_adapter", category: "Core", description: "Generates SOP addenda, diffs, and risk flags for protocol adaptation." },
  { name: "controls_generator", category: "Core", description: "Produces controls checklists tailored to specific assay types." },
  { name: "troubleshooter", category: "Core", description: "Interactive diagnosis of experimental failures with next-run test suggestions." },
  { name: "eln_scribe", category: "Core", description: "Renders run schema into structured ELN.md documents and manifests." },
  { name: "memory_agent", category: "Innovation", description: "Maintains persistent context and cross-run learnings for the workspace." },
  { name: "hypothesis_generator", category: "Innovation", description: "Proposes ranked scientific hypotheses with novelty, feasibility, and cost scores." },
  { name: "tool_executor", category: "Innovation", description: "Orchestrates MCP tool calls with allowlisting, logging, and provenance tracking." },
  { name: "debate_manager", category: "Innovation", description: "Facilitates structured multi-agent debate to stress-test hypotheses." },
  { name: "experiment_manager", category: "Innovation", description: "Plans, tracks, and iterates on experiment loops to convergence." },
  { name: "structure_analyst", category: "Innovation", description: "Analyzes molecular structures and predicts binding interactions." },
  { name: "data_analyst", category: "Innovation", description: "Processes experimental datasets and generates statistical summaries." },
  { name: "image_analyst", category: "Innovation", description: "Interprets microscopy, flow cytometry, and gel images with AI vision." },
  { name: "target_intelligence", category: "Innovation", description: "Compares target proteins across preclinical species — mapping orthologs, PTM conservation, and antibody availability for translational risk assessment." },
];

const FEATURES = [
  {
    emoji: "🔬",
    title: "Literature Scout",
    description: "Automatically retrieves and summarizes relevant papers from your knowledge base, extracting methods and producing citation objects for every claim.",
  },
  {
    emoji: "📋",
    title: "SOP Adapter",
    description: "Adapts standard operating procedures to your specific reagents, equipment, and cell lines — generating diffs and flagging deviations before you run.",
  },
  {
    emoji: "✅",
    title: "Controls Generator",
    description: "Suggests positive, negative, and isotype controls appropriate for your assay type and experimental design.",
  },
  {
    emoji: "🩺",
    title: "Troubleshooter",
    description: "Diagnoses failed experiments interactively, proposing root causes and designing next-iteration tests to isolate variables.",
  },
  {
    emoji: "📝",
    title: "ELN Scribe",
    description: "Transforms your experimental session into a structured, audit-ready Electronic Lab Notebook with reagent manifests and parameter logs.",
  },
  {
    emoji: "💡",
    title: "Hypothesis Generator",
    description: "Generates ranked scientific hypotheses scored on novelty, feasibility, evidence strength, and estimated cost — then debates them for robustness.",
  },
  {
    emoji: "🧪",
    title: "Experiment Manager",
    description: "Plans iterative experiment loops, tracks results, extracts learnings, and converges toward validated outcomes automatically.",
  },
  {
    emoji: "🎯",
    title: "Target Analysis",
    description: "Compares a human protein target across toxicology-relevant preclinical species — fetching orthologs, aligning sequences, mapping PTM conservation, and searching antibody databases, with an AI-generated translational risk summary.",
  },
  {
    emoji: "🔒",
    title: "Audit Trail",
    description: "Every agent action, tool call, retrieved document, and model response is logged with hashes for complete reproducibility and compliance.",
  },
];

export default function HowItWorksPage() {
  const coreAgents = AGENTS.filter((a) => a.category === "Core");
  const innovationAgents = AGENTS.filter((a) => a.category === "Innovation");

  return (
    <PageShell
      title="AI Co-Scientist for Biology"
      subtitle="Autonomous scientific reasoning system for wet-lab biology research"
    >
      {/* Hero */}
      <div className="bg-gradient-to-br from-indigo-500/10 via-zinc-900 to-zinc-900 rounded-xl border border-indigo-500/20 p-8">
        <p className="text-zinc-300 text-base leading-relaxed max-w-3xl">
          CoScientist is a post-run, multi-model assistant that transforms how biologists
          document, analyze, and extend their experiments. It orchestrates specialized AI
          agents across literature retrieval, protocol adaptation, hypothesis generation,
          and experiment planning — all grounded in your private knowledge base.
        </p>
        <div className="mt-4 inline-flex items-center gap-2 text-xs text-zinc-500 bg-zinc-800/60 rounded-lg px-3 py-2 font-mono">
          Built on LangGraph + LangChain with provider-agnostic LLM support (Anthropic, OpenAI, Gemini, Ollama)
        </div>
      </div>

      {/* Features grid */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-200 mb-4">Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="bg-zinc-900 rounded-xl border border-zinc-800 p-5 flex flex-col gap-3"
            >
              <span className="text-2xl" aria-hidden="true">{feature.emoji}</span>
              <div>
                <h3 className="text-sm font-semibold text-zinc-100">{feature.title}</h3>
                <p className="text-xs text-zinc-500 mt-1.5 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent roster */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-200 mb-4">Agent Roster</h2>

        <div className="space-y-6">
          {/* Core agents */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded px-2 py-0.5">
                Core
              </span>
              <span className="text-xs text-zinc-500">Production-ready, fully integrated</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {coreAgents.map((agent) => (
                <AgentCard key={agent.name} agent={agent} />
              ))}
            </div>
          </div>

          {/* Innovation agents */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-medium text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded px-2 py-0.5">
                Innovation
              </span>
              <span className="text-xs text-zinc-500">Advanced capabilities, experimental</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {innovationAgents.map((agent) => (
                <AgentCard key={agent.name} agent={agent} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Architecture */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-xs font-medium text-zinc-400 mb-2">Orchestration</p>
            <ul className="space-y-1 text-xs text-zinc-500">
              <li>Supervisor + Subagents pattern</li>
              <li>Isolated context windows per agent</li>
              <li>Strict output schemas (Pydantic)</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-medium text-zinc-400 mb-2">Knowledge</p>
            <ul className="space-y-1 text-xs text-zinc-500">
              <li>ChromaDB vector store</li>
              <li>Multi-collection retrieval</li>
              <li>Citation-grounded responses</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-medium text-zinc-400 mb-2">Compliance</p>
            <ul className="space-y-1 text-xs text-zinc-500">
              <li>Append-only audit log</li>
              <li>SHA-256 artifact hashing</li>
              <li>Prompt hash tracking</li>
            </ul>
          </div>
        </div>
      </div>
    </PageShell>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  const isCore = agent.category === "Core";
  return (
    <div className="bg-zinc-800/40 rounded-lg border border-zinc-800 p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <code className="text-xs font-mono text-zinc-200">{agent.name}</code>
        <span
          className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${
            isCore
              ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              : "text-amber-400 bg-amber-400/10 border-amber-400/20"
          }`}
        >
          {agent.category}
        </span>
      </div>
      <p className="text-xs text-zinc-500 leading-relaxed">{agent.description}</p>
    </div>
  );
}
