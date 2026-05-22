# app/ai/llm.py
"""
LLM Factory for DAKSHA agents.

Model assignments:
  Gemini 2.0 Flash  → Orchestrator, RecommendationAgent, OfferAgent
                       (reasoning, vision, nuanced tool selection)
  Groq llama-3.3-70b → CartAgent, PaymentAgent, DeliveryAgent,
                        PostPurchaseAgent, SupportAgent
                        (fast, cheap, deterministic tool calls)

Auth: GEMINI_VERTEX_API_KEY (AQ. prefix key from Google AI Studio / Vertex).
      Passed as google_api_key to ChatGoogleGenerativeAI.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.core.config import settings
from typing import Literal

ModelRole = Literal["orchestrator", "reasoning", "fast"]


def _gemini_api_key() -> str:
    """Return the active Gemini key (AQ. prefix, Vertex AI / Google AI Studio)."""
    return settings.GEMINI_VERTEX_API_KEY or settings.VERTEX_API_KEY or ""


def get_gemini(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Gemini 2.0 Flash — reasoning, vision, complex tool selection."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        temperature=temperature,
        google_api_key=_gemini_api_key(),
    )


def get_groq(temperature: float = 0.1) -> ChatGroq:
    """Groq llama-3.3-70b-versatile — fast deterministic tool calls."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
    )


def get_llm_for_agent(agent_name: str):
    """
    Returns the appropriate LLM for a given agent name.
    Import this in every agent file instead of hard-coding the model.
    """
    GEMINI_AGENTS = {"RecommendationAgent", "OfferAgent", "Orchestrator"}
    if agent_name in GEMINI_AGENTS:
        return get_gemini()
    return get_groq()


# Convenience alias kept for backwards compatibility
def get_llm() -> ChatGoogleGenerativeAI:
    """Default LLM — Gemini 2.0 Flash. Use get_llm_for_agent() in new agent files."""
    return get_gemini()
