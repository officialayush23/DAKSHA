# app/ai/llm.py
"""
LLM Factory for DAKSHA agents — Vertex AI backend.

Model assignments:
  Gemini 2.0 Flash (Vertex AI) → Orchestrator, RecommendationAgent, OfferAgent
                                  (reasoning, vision, nuanced tool selection)
  Groq llama-3.3-70b-versatile → CartAgent, PaymentAgent, DeliveryAgent,
                                  PostPurchaseAgent, SupportAgent
                                  (fast, cheap, deterministic tool calls)

Auth: uses GEMINI_VERTEX_API_KEY (new AQ. format AI-Studio key routed via Vertex)
      with location=asia-south1 for low-latency from India.
"""
from langchain_google_vertexai import ChatVertexAI
from langchain_groq import ChatGroq
from app.core.config import settings
from typing import Literal

ModelRole = Literal["orchestrator", "reasoning", "fast"]

# Pick the best available Gemini key (prefer the Vertex-issued one)
def _gemini_api_key() -> str:
    return (
        settings.GEMINI_VERTEX_API_KEY
        or settings.VERTEX_API_KEY
        or settings.GEMINI_API_KEY
        or ""
    )


def get_gemini(temperature: float = 0.2) -> ChatVertexAI:
    """Gemini 2.0 Flash via Vertex AI — reasoning, vision, complex tool selection."""
    return ChatVertexAI(
        model="gemini-2.0-flash-001",
        temperature=temperature,
        location=settings.VERTEX_AI_LOCATION,   # asia-south1
        api_key=_gemini_api_key(),
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


# Convenience aliases kept for backwards compatibility
def get_llm():
    """Default LLM — Gemini via Vertex AI. Use get_llm_for_agent() in new agent files."""
    return get_gemini()
