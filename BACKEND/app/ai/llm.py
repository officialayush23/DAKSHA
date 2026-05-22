# app/ai/llm.py
"""
LLM Factory for DAKSHA agents.

Authentication priority
────────────────────────
1. Vertex AI (production) — no free-tier limits, pay-as-you-go
   Requires: GOOGLE_CLOUD_PROJECT + one of:
     a) GOOGLE_APPLICATION_CREDENTIALS_JSON  (full SA JSON as env var, for Render)
     b) GOOGLE_APPLICATION_CREDENTIALS       (path to SA JSON file, for local/K8s)
     c) Workload Identity / ADC              (GCE / Cloud Run)

2. Google AI Studio API key (fallback, dev only)
   Requires: GEMINI_VERTEX_API_KEY or VERTEX_API_KEY  (AQ. prefix)
   ⚠️  Hard daily limit of 20 requests/day on free tier.

Model assignments
──────────────────
  gemini-2.5-flash  → Unified agent (all reasoning, tool selection, vision)
  Groq llama-3.3-70b → fast/deterministic fallback (unused in unified flow)
"""
import asyncio
import base64
import json
import logging
import os
import tempfile
from typing import Any, List, Literal, Optional

import httpx
from pydantic import PrivateAttr
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_groq import ChatGroq

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

ModelRole = Literal["orchestrator", "reasoning", "fast"]
GEMINI_MODEL = "gemini-2.5-flash"


# ─────────────────────────────────────────────────────────────────────────────
# One-time credential bootstrap (runs at module import)
# ─────────────────────────────────────────────────────────────────────────────

def _bootstrap_credentials() -> None:
    """
    If GOOGLE_APPLICATION_CREDENTIALS_JSON is set (typical on Render / Heroku
    where you can't mount files), write the JSON to a temp file and point
    GOOGLE_APPLICATION_CREDENTIALS at it so google-auth ADC picks it up.
    """
    raw = settings.GOOGLE_APPLICATION_CREDENTIALS_JSON.strip()
    if not raw:
        return
    # Already bootstrapped in this process
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    try:
        # Validate it's real JSON
        json.loads(raw)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="gcp_sa_"
        )
        tmp.write(raw)
        tmp.flush()
        tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
        logger.info(f"✅ GCP credentials written to {tmp.name}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to bootstrap GCP credentials: {e}")


_bootstrap_credentials()


# ─────────────────────────────────────────────────────────────────────────────
# Client factory
# ─────────────────────────────────────────────────────────────────────────────

def _make_client() -> genai.Client:
    """
    Returns a google-genai Client.

    Uses Vertex AI when GOOGLE_CLOUD_PROJECT is set — this routes requests to
    aiplatform.googleapis.com (no free-tier daily cap, purely pay-as-you-go).

    Falls back to Google AI Studio API key when no project is configured.
    """
    project = settings.GOOGLE_CLOUD_PROJECT.strip()
    if project:
        location = (
            settings.GOOGLE_CLOUD_LOCATION.strip()
            or settings.VERTEX_AI_LOCATION.strip()
            or "us-central1"
        )
        return genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    # Fallback: Google AI Studio API key
    api_key = settings.GEMINI_VERTEX_API_KEY or settings.VERTEX_API_KEY
    if not api_key:
        raise RuntimeError(
            "No Gemini credentials configured. Set GOOGLE_CLOUD_PROJECT "
            "(+ service account) or GEMINI_VERTEX_API_KEY."
        )
    return genai.Client(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# Message conversion helpers
# ─────────────────────────────────────────────────────────────────────────────

def _lc_to_genai(messages: List[BaseMessage]):
    """
    Convert LangChain messages → (system_instruction, contents).
    Handles: plain text, multimodal image_url (remote + base64), tool calls,
    tool responses.
    """
    system_instruction: Optional[str] = None
    contents: list = []

    for msg in messages:

        # ── System ──────────────────────────────────────────────────────────
        if isinstance(msg, SystemMessage):
            system_instruction = str(msg.content)

        # ── Human / User ────────────────────────────────────────────────────
        elif isinstance(msg, HumanMessage):
            if isinstance(msg.content, list):
                parts = []
                for block in msg.content:
                    btype = block.get("type")
                    if btype == "text":
                        parts.append(types.Part(text=block["text"]))
                    elif btype == "image_url":
                        url: str = block["image_url"]["url"]
                        if url.startswith("data:"):
                            header, b64 = url.split(",", 1)
                            mime = header.split(";")[0].split(":")[1]
                            parts.append(types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime,
                                    data=base64.b64decode(b64),
                                )
                            ))
                        else:
                            resp = httpx.get(url, timeout=15, follow_redirects=True)
                            mime = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                            parts.append(types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime,
                                    data=resp.content,
                                )
                            ))
                contents.append(types.Content(role="user", parts=parts))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=str(msg.content))],
                ))

        # ── AI / Model ───────────────────────────────────────────────────────
        elif isinstance(msg, AIMessage):
            parts = []
            if msg.content:
                parts.append(types.Part(text=str(msg.content)))
            for tc in msg.tool_calls or []:
                parts.append(types.Part(
                    function_call=types.FunctionCall(
                        name=tc["name"],
                        args=tc["args"],
                    )
                ))
            if not parts:
                parts = [types.Part(text="")]
            contents.append(types.Content(role="model", parts=parts))

        # ── Tool result ──────────────────────────────────────────────────────
        elif isinstance(msg, ToolMessage):
            contents.append(types.Content(
                role="user",
                parts=[types.Part(
                    function_response=types.FunctionResponse(
                        name=msg.name or "tool_result",
                        response={"output": str(msg.content)},
                    )
                )],
            ))

    return system_instruction, contents


def _tools_to_genai(tools: list) -> Optional[types.Tool]:
    """LangChain tools → google-genai Tool with FunctionDeclarations."""
    if not tools:
        return None
    declarations = []
    for t in tools:
        schema = None
        if hasattr(t, "args_schema") and t.args_schema:
            schema = t.args_schema.model_json_schema()
        declarations.append(types.FunctionDeclaration(
            name=t.name,
            description=getattr(t, "description", ""),
            parameters=schema,
        ))
    return types.Tool(function_declarations=declarations)


def _parse_response(response) -> AIMessage:
    """google-genai GenerateContentResponse → LangChain AIMessage."""
    if not response or not response.candidates:
        return AIMessage(content="")

    candidate = response.candidates[0]

    # Guard against safety blocks / empty candidates (content is None)
    if candidate.content is None or not candidate.content.parts:
        finish = getattr(candidate, "finish_reason", None)
        reason = str(finish) if finish else "unknown"
        logger.warning(f"Gemini response blocked — finish_reason: {reason}")
        return AIMessage(content=f"[Response blocked — finish_reason: {reason}]")

    text_parts: list[str] = []
    tool_calls: list[dict] = []

    for i, part in enumerate(candidate.content.parts):
        if getattr(part, "text", None):
            text_parts.append(part.text)
        fc = getattr(part, "function_call", None)
        if fc:
            tool_calls.append({
                "name": fc.name,
                "args": dict(fc.args),
                "id": f"call_{fc.name}_{i}",
                "type": "tool_call",
            })

    return AIMessage(content="".join(text_parts), tool_calls=tool_calls)


# ─────────────────────────────────────────────────────────────────────────────
# Custom LangChain-compatible Gemini model
# ─────────────────────────────────────────────────────────────────────────────

class GeminiVertexChat(BaseChatModel):
    """
    LangChain BaseChatModel backed by google-genai SDK.

    Supports:
      • Vertex AI (production — aiplatform.googleapis.com, no free-tier cap)
      • Google AI Studio API keys (dev fallback)
      • Tool / function calling via bind_tools()
      • Multimodal vision — remote URLs and base64 image_url blocks
    """
    model: str = GEMINI_MODEL
    temperature: float = 0.2
    _bound_tools: list = PrivateAttr(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "gemini-vertex-genai"

    def bind_tools(self, tools: list, **kwargs) -> "GeminiVertexChat":
        clone = self.__class__(model=self.model, temperature=self.temperature)
        clone._bound_tools = list(tools)
        return clone

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs,
    ) -> ChatResult:
        client = _make_client()
        system_instruction, contents = _lc_to_genai(messages)

        cfg: dict = {"temperature": self.temperature}
        if system_instruction:
            cfg["system_instruction"] = system_instruction
        if self._bound_tools:
            tool_obj = _tools_to_genai(self._bound_tools)
            if tool_obj:
                cfg["tools"] = [tool_obj]

        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**cfg),
        )
        return ChatResult(generations=[ChatGeneration(message=_parse_response(response))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs,
    ) -> ChatResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._generate(messages, stop, run_manager, **kwargs)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Public factory functions — same interface as before, drop-in replacement
# ─────────────────────────────────────────────────────────────────────────────

def get_gemini(temperature: float = 0.2) -> GeminiVertexChat:
    """Gemini 2.5 Flash — Vertex AI (production) or Google AI Studio (dev fallback)."""
    return GeminiVertexChat(model=GEMINI_MODEL, temperature=temperature)


def get_groq(temperature: float = 0.1) -> ChatGroq:
    """Groq llama-3.3-70b — fast deterministic tool calls."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
    )


def get_llm_for_agent(agent_name: str) -> BaseChatModel:
    """Returns Gemini for reasoning agents, Groq for fast/transactional agents."""
    GEMINI_AGENTS = {"RecommendationAgent", "OfferAgent", "Orchestrator"}
    return get_gemini() if agent_name in GEMINI_AGENTS else get_groq()


def get_llm() -> GeminiVertexChat:
    """Default LLM — Gemini 2.5 Flash."""
    return get_gemini()
