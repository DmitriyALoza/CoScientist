"""
Supervisor orchestrator.

Builds the multi-agent LangGraph using langgraph-supervisor.
The supervisor routes to subagents based on the current mode and user intent.
All subagents load their prompts from SKILL.md files at graph build time.
"""

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph_supervisor import create_supervisor

from eln.agents.controls_generator import build_controls_generator
from eln.agents.eln_scribe import build_eln_scribe
from eln.agents.literature_scout import build_literature_scout
from eln.agents.sop_adapter import build_sop_adapter
from eln.agents.state import AppState
from eln.agents.troubleshooter import build_troubleshooter

_SOUL = (Path(__file__).parent / "SOUL.md").read_text()

_SUPERVISOR_PROMPT = """\
You are the AI Co-Scientist supervisor for a wet-lab biology assistant system.
You coordinate a team of specialist agents. Your job is ROUTING — not answering directly.

## Your team

- **literature_scout**: finds papers (local KB + PubMed + Semantic Scholar),
  extracts methods, returns citations. Use for any scientific question,
  background research, or when citations are needed.
- **sop_adapter**: adapts SOPs to the specific experiment, generates addenda
  and diffs. Use in Protocol mode or when the user asks about a protocol.
- **controls_generator**: generates controls checklists for the experiment's
  assay type. Use when preparing or reviewing controls.
- **troubleshooter**: diagnoses unexpected results interactively. Use in
  Validation mode or when the user reports a problem.
- **eln_scribe**: renders the final ELN.md from all gathered context. Use
  LAST, after other agents have contributed citations and controls.
- **memory_agent**: stores and retrieves scientific knowledge across sessions.
  Use when the user says "remember X", "recall X", or "what do you know about X".
- **hypothesis_generator**: generates, scores, and ranks scientific hypotheses.
  Use when the user asks to generate or brainstorm hypotheses.
- **tool_executor**: runs experiment simulations and cost estimates only.
  Use for protocol simulation or cost estimation — NOT for statistics or plotting.
- **data_analyst**: performs statistical analysis, fold change, plot generation,
  and R-based bioinformatics. Use for p-values, effect sizes, correlation,
  regression, DESeq2, or any quantitative analysis of experimental data.
- **debate_manager**: orchestrates multi-agent debate to stress-test hypotheses.
  Use when the user wants to evaluate, critique, or debate a hypothesis.
- **experiment_manager**: plans and tracks iterative experiment loops.
  Use for experiment planning, recording results, or suggesting next iterations.
- **image_analyst**: classifies and analyses lab images (western blots, gels, microscopy,
  flow cytometry, graphs). Use when images are attached (pending_images is non-empty).
- **structure_analyst**: fetches AlphaFold structures, interprets pLDDT confidence and PAE
  domain architecture, and submits novel sequences via ColabFold (premium).
  Use for any protein structure, folding, or domain question.
- **target_intelligence**: cross-species protein comparison, PTM conservation analysis,
  and antibody/clone availability lookup. Use when the user asks to compare a target
  across species, assess PTM conservation, evaluate translational risk, or find antibodies
  with multi-species reactivity.

## Routing rules by mode

**normal** — General assistant mode:
  - Scientific questions / literature → literature_scout
  - Protocol questions → sop_adapter
  - "Generate ELN" → literature_scout THEN controls_generator THEN eln_scribe (in order)
  - "Remember X" / recall queries → memory_agent
  - "Generate hypotheses for X" → memory_agent (context) THEN hypothesis_generator
  - "Analyze this data" / statistical tests / fold change / plots → data_analyst
  - "Estimate cost" / "simulate experiment" → tool_executor
  - Chart/graph image uploaded → image_analyst THEN data_analyst (if stats requested)
  - R analysis / DESeq2 / limma / survival → data_analyst
  - AlphaFold / protein structure / pLDDT / PAE / fold this sequence → structure_analyst
  - "Compare [target] across species" / PTM conservation / antibody availability → target_intelligence
  - "Debate this hypothesis" → debate_manager
  - "Plan an experiment" / "record result" → experiment_manager
  - Images attached (pending_images non-empty) → image_analyst **immediately**
  - Direct questions you can answer → answer directly (no handoff needed)

**validation** — User is troubleshooting an unexpected result:
  - Always start with troubleshooter
  - Call controls_generator to check controls after troubleshooter
  - Call literature_scout if the troubleshooter needs citations
  - Call memory_agent if prior experiments are relevant
  - Do NOT call eln_scribe until troubleshooting is complete

**protocol** — User is adapting or reviewing a protocol:
  - Always start with sop_adapter
  - Call literature_scout for supporting evidence if needed
  - Call controls_generator for controls review

## Rules
- Hand off to ONE agent at a time (no parallel handoffs).
- Do not call eln_scribe until you have run at least literature_scout and controls_generator.
- When you have a final answer, respond directly — do not hand off again.
- If the user's intent is unclear, ask a clarifying question before routing.
"""


def _make_supervisor_prompt(state: AppState):
    """Dynamic prompt that injects the current mode and run context.

    When ``prompt`` is a callable, ``create_react_agent`` uses its return
    value as the **full** message list sent to the model — it does *not*
    prepend state messages automatically.  We must therefore return the
    system message **plus** the conversation messages from state.
    """
    import json

    mode = state.get("mode", "normal")
    run_id = state.get("run_id")
    context_lines = [f"**Current mode:** {mode}"]
    if run_id:
        context_lines.append(f"**Active run ID:** {run_id}")

    selected_template = state.get("selected_template")
    if selected_template:
        context_lines.append(
            f"**Output template selected** — when generating documents, "
            f"conform to this structure:\n```json\n{json.dumps(selected_template, indent=2)}\n```"
        )
    else:
        context_lines.append(
            "**No template selected** — choose a suitable structure for the document type."
        )

    pending_images = state.get("pending_images", [])
    if pending_images:
        filenames = ", ".join(img.get("filename", "image") for img in pending_images)
        context_lines.append(
            f"**[Images attached: {filenames}]** → Route to image_analyst immediately."
        )

    context_block = "\n".join(context_lines)
    system = SystemMessage(content=f"{_SOUL}\n\n---\n\n{_SUPERVISOR_PROMPT}\n\n## Current context\n{context_block}")
    messages = state.get("messages", [])
    return [system] + list(messages)


def build_supervisor_graph(
    main_model: BaseChatModel,
    supervisor_model: BaseChatModel | None = None,
    checkpointer: MemorySaver | None = None,
    kb_indexes_path: Path | None = None,
    run_path: Path | None = None,
    embedding_provider: str = "local",
    embedding_model: str = "",
    workspace_path: Path | None = None,
) -> CompiledStateGraph:
    """
    Build and compile the full supervisor + subagents graph.

    Args:
        main_model: The full-capability model used by eln_scribe and troubleshooter.
        supervisor_model: A lighter model used by the supervisor for routing.
                          Defaults to main_model if not provided.
        checkpointer: LangGraph checkpointer for state persistence across turns.
                      Defaults to an in-memory saver.
        kb_indexes_path: Path to the Qdrant indexes directory. If provided,
                         enables RAG tools for subagents.
        run_path: Path to the active run folder. If provided, enables
                  file write tools (write_eln, write_report).
        workspace_path: Root workspace path for memory, hypotheses, debates,
                        and experiments. Enables all innovation features.
    """
    router_model = supervisor_model or main_model

    # ------------------------------------------------------------------
    # RAG tools (search local KB)
    # ------------------------------------------------------------------

    rag_tools = []
    if kb_indexes_path is not None:
        from eln.retrieval.indexer import EMBEDDING_PROVIDERS, KBIndexer
        from eln.retrieval.retriever import RAGRetriever
        from eln.tools.retrieval_tools import (
            search_all_kb,
            search_eln_entries,
            search_papers,
            search_reference_docs,
            search_reports,
            search_sops,
            set_retriever,
        )

        em = embedding_model or EMBEDDING_PROVIDERS[embedding_provider]["default"]
        indexer = KBIndexer(
            persist_dir=kb_indexes_path,
            embedding_provider=embedding_provider,
            embedding_model=em,
        )
        retriever = RAGRetriever(indexer=indexer)
        set_retriever(retriever)
        rag_tools = [
            search_papers, search_sops,
            search_reports, search_eln_entries, search_reference_docs,
            search_all_kb,
        ]

    # External literature tools (live HTTP search)
    from eln.tools.literature_tools import search_pubmed, search_semantic_scholar

    literature_tools = rag_tools + [search_pubmed, search_semantic_scholar]

    # SOP tools
    from eln.tools.diff_tools import text_diff

    sop_tools = [t for t in rag_tools if t.name in ("search_sops", "search_all_kb")]
    sop_tools.append(text_diff)

    # File tools (write ELN, reports, read artifacts)
    file_tools = []
    if run_path is not None:
        from eln.tools.file_tools import read_artifact, set_run_path, write_eln, write_report

        set_run_path(run_path)
        file_tools = [write_eln, write_report, read_artifact]

    # Troubleshooter gets KB search + report writing
    troubleshooter_tools = [t for t in rag_tools if t.name == "search_all_kb"]
    troubleshooter_tools.extend([t for t in file_tools if t.name == "write_report"])

    # ELN scribe gets KB search + ELN writing
    scribe_tools = [t for t in rag_tools if t.name == "search_all_kb"]
    scribe_tools.extend([t for t in file_tools if t.name in ("write_eln", "read_artifact")])

    # ------------------------------------------------------------------
    # Memory tools (Phase 1)
    # ------------------------------------------------------------------

    memory_tools = []
    if workspace_path is not None:
        from eln.memory.memory_manager import MemoryManager
        from eln.tools.memory_tools import (
            query_knowledge_graph,
            recall_memory,
            set_memory_manager,
            store_memory,
            update_knowledge_graph,
        )

        memory_manager = MemoryManager(workspace_path / "memory")
        set_memory_manager(memory_manager)
        memory_tools = [recall_memory, store_memory, query_knowledge_graph, update_knowledge_graph]

    # ------------------------------------------------------------------
    # Hypothesis tools (Phase 2)
    # ------------------------------------------------------------------

    hypothesis_tools = []
    if workspace_path is not None:
        from eln.tools.hypothesis_tools import (
            generate_hypotheses,
            load_hypothesis_history,
            rank_hypotheses,
            save_hypothesis_set,
            set_hypothesis_store,
        )
        from eln.workspace.hypothesis_store import HypothesisStore

        hypothesis_store = HypothesisStore(workspace_path / "hypotheses")
        set_hypothesis_store(hypothesis_store)
        hypothesis_tools = [
            generate_hypotheses,
            rank_hypotheses,
            save_hypothesis_set,
            load_hypothesis_history,
        ]

    # ------------------------------------------------------------------
    # Analysis / simulation tools (Phase 3)
    # ------------------------------------------------------------------

    from eln.tools.analysis_tools import compute_statistics, run_python_analysis, run_r_analysis
    from eln.tools.simulation_tools import estimate_cost, simulate_experiment

    # tool_executor: simulation + cost only
    read_artifact_tool = next((t for t in file_tools if t.name == "read_artifact"), None)
    executor_tools = [simulate_experiment, estimate_cost] + ([read_artifact_tool] if read_artifact_tool else [])

    # data_analyst: full analysis stack
    from eln.tools.file_tools import save_csv_artifact, save_plot_artifact
    from eln.config import settings

    data_analyst_tools = [
        run_python_analysis,
        compute_statistics,
        save_plot_artifact,
        save_csv_artifact,
    ] + ([read_artifact_tool] if read_artifact_tool else [])
    if settings.r_analysis_enabled:
        data_analyst_tools.append(run_r_analysis)

    # ------------------------------------------------------------------
    # Debate tools + sub-graph (Phase 4)
    # ------------------------------------------------------------------

    debate_tools = []
    debate_graph = None
    if workspace_path is not None:
        from eln.agents.debate.graph import build_debate_graph
        from eln.tools.debate_tools import (
            get_debate_status,
            load_debate_synthesis,
            set_debate_graph,
            set_debate_store,
            start_debate,
        )
        from eln.workspace.debate_store import DebateStore

        debate_store = DebateStore(workspace_path / "debates")
        set_debate_store(debate_store)
        debate_graph = build_debate_graph(model=main_model)
        set_debate_graph(debate_graph)
        debate_tools = [start_debate, get_debate_status, load_debate_synthesis]

    # ------------------------------------------------------------------
    # Experiment tools (Phase 5)
    # ------------------------------------------------------------------

    experiment_tools = []
    if workspace_path is not None:
        from eln.tools.experiment_tools import (
            get_experiment_history,
            plan_experiment,
            record_result,
            set_experiment_store,
            suggest_next_experiment,
            update_hypothesis_from_results,
        )
        from eln.workspace.experiment_store import ExperimentStore

        experiment_store = ExperimentStore(workspace_path / "experiments")
        set_experiment_store(experiment_store)
        experiment_tools = [
            plan_experiment,
            record_result,
            get_experiment_history,
            suggest_next_experiment,
            update_hypothesis_from_results,
        ]
        # Add search_all_kb to experiment tools if available
        search_all_tool = next((t for t in rag_tools if t.name == "search_all_kb"), None)
        if search_all_tool:
            experiment_tools.append(search_all_tool)

    # ------------------------------------------------------------------
    # Build subagents
    # ------------------------------------------------------------------

    literature_scout = build_literature_scout(model=router_model, tools=literature_tools)
    sop_adapter = build_sop_adapter(model=router_model, tools=sop_tools)
    controls_generator = build_controls_generator(model=router_model, tools=[])
    troubleshooter = build_troubleshooter(model=main_model, tools=troubleshooter_tools)
    eln_scribe = build_eln_scribe(model=main_model, tools=scribe_tools)

    # Innovation agents (always built, but tools empty when workspace not provided)
    from eln.agents.memory_agent import build_memory_agent
    from eln.agents.hypothesis_generator import build_hypothesis_generator
    from eln.agents.tool_executor import build_tool_executor
    from eln.agents.debate_manager import build_debate_manager
    from eln.agents.experiment_manager import build_experiment_manager
    from eln.agents.image_analyst import build_image_analyst
    from eln.agents.data_analyst import build_data_analyst
    from eln.agents.structure_analyst import build_structure_analyst
    from eln.tools.image_tools import image_tools, set_image_run_path

    memory_agent = build_memory_agent(
        model=router_model,
        tools=memory_tools,
    )
    hypothesis_generator = build_hypothesis_generator(
        model=main_model,
        tools=hypothesis_tools + memory_tools[:1] + rag_tools[:2],  # recall + search
    )
    tool_executor = build_tool_executor(
        model=main_model,
        tools=executor_tools,
    )
    debate_manager = build_debate_manager(
        model=main_model,
        tools=debate_tools,
    )
    experiment_manager = build_experiment_manager(
        model=main_model,
        tools=experiment_tools,
    )

    # Image analyst
    if run_path is not None:
        set_image_run_path(run_path)

    # image_analyst gets save_csv_artifact so it can hand off chart data to data_analyst
    image_analyst_tools = list(image_tools) + [save_csv_artifact]
    image_analyst = build_image_analyst(model=main_model, tools=image_analyst_tools)

    # Data analyst
    data_analyst = build_data_analyst(model=main_model, tools=data_analyst_tools)

    # Structure analyst (AlphaFold + ColabFold)
    from eln.tools.alphafold_tools import (
        check_colabfold_job,
        fetch_alphafold_structure,
        get_alphafold_confidence,
        get_alphafold_pae,
        search_uniprot,
        set_structure_run_path,
        submit_colabfold_prediction,
    )

    if run_path is not None:
        set_structure_run_path(run_path)

    structure_tools = [
        search_uniprot,
        fetch_alphafold_structure,
        get_alphafold_confidence,
        get_alphafold_pae,
        submit_colabfold_prediction,
        check_colabfold_job,
    ]
    structure_analyst = build_structure_analyst(model=main_model, tools=structure_tools)

    # ------------------------------------------------------------------
    # Target Intelligence tools (Cross-Species Target Intelligence feature)
    # ------------------------------------------------------------------

    target_intelligence_tools = []
    if workspace_path is not None:
        from eln.agents.target_intelligence import build_target_intelligence
        from eln.tools.target_intelligence_tools import (
            align_sequences,
            get_orthologs,
            get_ptm_annotations,
            resolve_target,
            save_target_analysis,
            search_antibodies,
            set_target_analysis_store,
        )
        from eln.workspace.target_analysis_store import TargetAnalysisStore

        ta_store = TargetAnalysisStore(workspace_path / "target_analyses")
        set_target_analysis_store(ta_store)
        target_intelligence_tools = [
            resolve_target,
            get_orthologs,
            align_sequences,
            get_ptm_annotations,
            search_antibodies,
            save_target_analysis,
        ]

    from eln.agents.target_intelligence import build_target_intelligence

    target_intelligence_agent = build_target_intelligence(
        model=main_model,
        tools=target_intelligence_tools,
    )

    # ------------------------------------------------------------------
    # Build supervisor graph
    # ------------------------------------------------------------------

    agents = [
        literature_scout,
        sop_adapter,
        controls_generator,
        troubleshooter,
        eln_scribe,
        memory_agent,
        hypothesis_generator,
        tool_executor,
        debate_manager,
        experiment_manager,
        image_analyst,
        data_analyst,
        structure_analyst,
        target_intelligence_agent,
    ]

    workflow = create_supervisor(
        agents=agents,
        model=router_model,
        prompt=_make_supervisor_prompt,
        state_schema=AppState,
        output_mode="last_message",
        include_agent_name="inline",
    )

    cp = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=cp)
