# app/ai/llm.py
"""
LLM Factory for DAKSHA agents.

Model assignments:
  Gemini 2.5 Flash  →  Orchestrator, RecommendationAgent, OfferAgent
                        (reasoning, vision, nuanced tool selection)
  Groq llama-3.3-70b → CartAgent, PaymentAgent, DeliveryAgent,
                        PostPurchaseAgent, SupportAgent
                        (fast, cheap, deterministic tool calls)
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.core.config import settings
from typing import Literal

ModelRole = Literal["orchestrator", "reasoning", "fast"]


def get_gemini(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Gemini 2.5 Flash — reasoning, vision, complex tool selection."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        api_key=settings.GEMINI_API_KEY,
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
    """Default LLM — Gemini. Use get_llm_for_agent() in new agent files."""
    return get_gemini()
