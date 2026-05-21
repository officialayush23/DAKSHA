# app/ai/logging_nodes.py
"""
LoggingToolNode — wraps LangGraph's ToolNode to write every tool invocation
to the agent_actions table.  Drop-in replacement for ToolNode in graph.py.
"""

import time
import uuid
import json
import logging
from typing import Any

from langgraph.prebuilt import ToolNode
from app.core.database import SessionLocal
from app.models.models import AgentAction

logger = logging.getLogger(__name__)


def _safe_uuid(val: Any):
    """Convert a string/UUID to uuid.UUID, returning None on failure."""
    if val is None:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _truncate(obj: Any, max_len: int = 2000) -> Any:
    """Ensure serialised output doesn't blow the JSONB column budget."""
    try:
        s = json.dumps(obj, default=str)
        if len(s) > max_len:
            return {"_truncated": True, "preview": s[:max_len]}
        return obj
    except Exception:
        return {"_raw": str(obj)[:max_len]}


def make_logging_tool_node(tools: list, agent_name: str):
    """
    Returns an async LangGraph node that:
      1. Runs the underlying ToolNode (executes the tools)
      2. Logs every tool call + result to agent_actions table

    Usage in graph.py:
        from app.ai.logging_nodes import make_logging_tool_node
        builder.add_node("cart_tools", make_logging_tool_node(cart_tools, "CartAgent"))
    """
    inner_node = ToolNode(tools)

    async def _logging_node(state: dict) -> dict:
        t_start = time.time()

        # --- run the actual tool(s) ---
        result = await inner_node.ainvoke(state)

        total_latency_ms = int((time.time() - t_start) * 1000)

        # --- extract tool-call metadata from the last AI message ---
        last_ai_msg = state["messages"][-1]
        tool_calls = getattr(last_ai_msg, "tool_calls", []) or []

        # ToolNode returns {"messages": [ToolMessage, ...]}
        tool_messages = result.get("messages", [])

        session_id_raw = state.get("session_id")
        user_id_raw    = state.get("user_id")
        per_call_ms    = total_latency_ms // max(len(tool_calls), 1)

        try:
            with SessionLocal() as db:
                for idx, tc in enumerate(tool_calls):
                    # parse output from the corresponding ToolMessage
                    output_content = None
                    success        = True
                    error_msg      = None

                    if idx < len(tool_messages):
                        tm = tool_messages[idx]
                        raw = getattr(tm, "content", None)

                        # Try to parse as JSON for richer storage
                        if isinstance(raw, str):
                            try:
                                output_content = json.loads(raw)
                            except json.JSONDecodeError:
                                output_content = raw

                        # Detect tool-level failures by checking common error prefixes
                        if isinstance(raw, str) and any(
                            raw.startswith(p)
                            for p in ("Action failed:", "Search failed:", "Error:", "Trending fetch failed:")
                        ):
                            success   = False
                            error_msg = raw[:500]

                    action = AgentAction(
                        session_id    = _safe_uuid(session_id_raw),
                        user_id       = _safe_uuid(user_id_raw),
                        agent_name    = agent_name,
                        tool_name     = tc.get("name", "unknown"),
                        tool_input    = _truncate(tc.get("args")),
                        tool_output   = _truncate(output_content),
                        latency_ms    = per_call_ms,
                        success       = success,
                        error_message = error_msg,
                    )
                    db.add(action)

                db.commit()
        except Exception as log_err:
            # Logging must NEVER break the agent flow
            logger.warning(f"⚠️ AgentAction log failed for {agent_name}: {log_err}")

        return result

    # give the node a helpful __name__ for LangGraph's debug traces
    _logging_node.__name__ = f"{agent_name}_logging_tool_node"
    return _logging_node
