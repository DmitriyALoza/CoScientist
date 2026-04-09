"""WebSocket streaming chat endpoint."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["chat"])

# Per-session graph cache keyed by thread_id
_graph_cache: dict[str, Any] = {}


def _get_graph(
    user_id: str,
    provider: str,
    model: str,
    supervisor_model: str,
    run_id: str | None,
) -> Any:
    """Build or retrieve a cached supervisor graph."""
    cache_key = f"{user_id}:{provider}:{model}"
    if cache_key in _graph_cache:
        return _graph_cache[cache_key]

    from eln.config import settings
    from eln.providers import build_provider
    from eln.agents.supervisor import build_supervisor_graph
    from eln.workspace import WorkspaceManager
    from langgraph.checkpoint.memory import MemorySaver

    prov = build_provider(provider, model=model)
    main_llm = prov.llm

    try:
        sup_prov = build_provider(provider, model=supervisor_model)
        sup_llm = sup_prov.llm
    except Exception:
        sup_llm = main_llm

    wm = WorkspaceManager(user_id=user_id)
    run_path = (wm.root / "runs" / run_id) if run_id else None

    graph = build_supervisor_graph(
        main_model=main_llm,
        supervisor_model=sup_llm,
        checkpointer=MemorySaver(),
        kb_indexes_path=wm.indexes_path(),
        run_path=run_path,
        workspace_path=wm.root,
    )
    _graph_cache[cache_key] = graph
    return graph


@router.websocket("/chat")
async def chat_ws(ws: WebSocket) -> None:
    await ws.accept()

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") != "message":
                continue

            content: str = msg.get("content", "")
            mode: str = msg.get("mode", "normal")
            run_id: str | None = msg.get("run_id")
            thread_id: str = msg.get("thread_id") or str(uuid.uuid4())
            user_id: str = msg.get("user_id", "default")
            provider: str = msg.get("provider", "anthropic")
            model: str = msg.get("model", "claude-sonnet-4-6")
            supervisor_model: str = msg.get("supervisor_model", "claude-haiku-4-5-20251001")
            docs: list[dict] = msg.get("docs", [])

            # Inject attached docs into the message
            if docs:
                doc_context = "\n\n".join(
                    f"[Attached: {d['name']}]\n{d['text']}" for d in docs
                )
                content = f"{content}\n\n---\n{doc_context}"

            try:
                graph = _get_graph(user_id, provider, model, supervisor_model, run_id)
            except Exception as e:
                await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
                continue

            state_input = {
                "messages": [{"role": "user", "content": content}],
                "mode": mode,
                "run_id": run_id,
                "citations": [],
                "tool_trace": [],
            }
            config = {"configurable": {"thread_id": thread_id}}

            last_agent: str | None = None

            try:
                async for chunk in graph.astream(state_input, config=config, stream_mode="values"):
                    msgs = chunk.get("messages", [])
                    if msgs:
                        from langchain_core.messages import AIMessage
                        last = msgs[-1]
                        if isinstance(last, AIMessage):
                            content_out = last.content or ""
                            if isinstance(content_out, list):
                                content_out = "\n".join(
                                    p.get("text", "")
                                    for p in content_out
                                    if isinstance(p, dict) and p.get("type") == "text"
                                )
                            if content_out:
                                agent_name = getattr(last, "name", None)
                                if agent_name:
                                    last_agent = agent_name
                                await ws.send_text(json.dumps({
                                    "type": "token",
                                    "text": content_out,
                                    "agent": last_agent,
                                }))

                    # Forward citations and tool_trace
                    for citation in chunk.get("citations", []):
                        await ws.send_text(json.dumps({"type": "citation", "citation": citation}))
                    for tool_call in chunk.get("tool_trace", []):
                        await ws.send_text(json.dumps({"type": "tool_call", "tool_call": tool_call}))

                await ws.send_text(json.dumps({
                    "type": "done",
                    "thread_id": thread_id,
                    "agent": last_agent,
                }))

            except Exception as e:
                await ws.send_text(json.dumps({"type": "error", "message": str(e)}))

    except WebSocketDisconnect:
        pass
