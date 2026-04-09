import operator
from typing import Annotated

from langgraph.prebuilt.chat_agent_executor import AgentState


class AppState(AgentState):
    """
    Shared graph state for the supervisor and all subagents.

    Extends AgentState which provides:
      - messages: Annotated[list[AnyMessage], add_messages]
      - remaining_steps: NotRequired[Annotated[int, RemainingStepsManager]]

    `citations` and `tool_trace` use `operator.add` so subagents can append
    their results without overwriting each other.
    """

    # Routing mode — set by the UI or CLI before invoking the graph
    mode: str  # "normal" | "validation" | "protocol"

    # Current run context (optional; populated once a run is selected in the UI)
    run_id: str | None

    # Accumulated citations from all subagents
    citations: Annotated[list[dict], operator.add]

    # Tool call trace for the right panel / audit
    tool_trace: Annotated[list[dict], operator.add]

    # Selected output template (serialised DocumentTemplate dict or None)
    selected_template: dict | None

    # Accumulated memory context from memory_agent
    memory_context: Annotated[list[dict], operator.add]

    # Hypothesis sets generated during the session
    hypotheses: Annotated[list[dict], operator.add]

    # Debate records from the debate_manager
    debates: Annotated[list[dict], operator.add]

    # Experiment records from the experiment_manager
    experiments: Annotated[list[dict], operator.add]

    # Images staged by the UI for the image_analyst — consumed per-turn
    pending_images: list[dict]  # {data: base64, mime_type, filename}

    # Accumulated image analysis records
    image_analyses: Annotated[list[dict], operator.add]
