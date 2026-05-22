# app/ai/llm.py
"""
LLM Factory for DAKSHA agents.

Uses google-genai SDK (google-genai 1.x) with Vertex AI / Google AI Studio
API keys (AQ. prefix).  Does NOT use the deprecated google-generativeai pkg
or ChatVertexAI.

Model assignments
─────────────────
  Gemini 2.0 Flash  → Orchestrator, RecommendationAgent, OfferAgent
                       (reasoning, vision, nuanced tool selection)
  Groq llama-3.3-70b → CartAgent, PaymentAgent, DeliveryAgent,
                        PostPurchaseAgent, SupportAgent
                        (fast, cheap, deterministic tool calls)
"""
import asyncio
import base64
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

ModelRole = Literal["orchestrator", "reasoning", "fast"]
GEMINI_MODEL = "gemini-2.5-flash"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_client() -> genai.Client:
    api_key = settings.GEMINI_VERTEX_API_KEY or settings.VERTEX_API_KEY or ""
    return genai.Client(api_key=api_key)


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
                # Multimodal block list
                parts = []
                for block in msg.content:
                    btype = block.get("type")
                    if btype == "text":
                        parts.append(types.Part(text=block["text"]))
                    elif btype == "image_url":
                        url: str = block["image_url"]["url"]
                        if url.startswith("data:"):
                            # Inline base64: data:<mime>;base64,<data>
                            header, b64 = url.split(",", 1)
                            mime = header.split(";")[0].split(":")[1]
                            parts.append(types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime,
                                    data=base64.b64decode(b64),
                                )
                            ))
                        else:
                            # Remote URL — fetch bytes
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
        # Try to surface a finish reason so it's visible in logs
        finish = getattr(candidate, "finish_reason", None)
        reason = str(finish) if finish else "unknown"
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
      • Vertex AI / Google AI Studio API keys (AQ. prefix)
      • Tool / function calling (bind_tools)
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
    """Gemini 2.0 Flash via google-genai SDK — vision + tool calls."""
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
    """Default LLM — Gemini 2.0 Flash. Use get_llm_for_agent() in agent files."""
    return get_gemini()
