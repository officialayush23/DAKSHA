# app/ai/message_utils.py
"""
Message trimming utilities for LangGraph agents.

Groq free tier limit: 12,000 TPM.
We keep only the most recent messages to stay safely under that.

Rules:
  1. SystemMessage is always preserved (never trimmed).
  2. ToolMessage is kept with its preceding AIMessage (never orphaned).
  3. Everything else: keep the last `keep_last` messages.
"""
from typing import List
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage


def trim_messages_for_groq(
    messages: List[BaseMessage],
    keep_last: int = 10,
) -> List[BaseMessage]:
    """
    Return a trimmed copy of `messages` safe for Groq's free-tier TPM limit.

    - System messages are always kept at the front.
    - The last `keep_last` non-system messages are kept.
    - ToolMessages are never orphaned — if a ToolMessage is kept, its
      originating AIMessage (the one with tool_calls) is kept too.
    """
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs  = [m for m in messages if not isinstance(m, SystemMessage)]

    # Take the tail
    trimmed = other_msgs[-keep_last:] if len(other_msgs) > keep_last else other_msgs

    # Ensure no orphaned ToolMessage at the start
    # (i.e. first message after trim must not be a ToolMessage)
    while trimmed and isinstance(trimmed[0], ToolMessage):
        trimmed = trimmed[1:]

    return system_msgs + trimmed
