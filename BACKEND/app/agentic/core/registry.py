"""
Domain-agnostic building blocks.

A *domain pack* tells the engine what agents exist, which tools each one may
call, which policies guard those tools and how to load the unified context for
a principal (customer, patient, citizen ...). The graph itself never imports
anything domain-specific, so the same engine can run commerce today and, say,
clinic scheduling tomorrow by registering a different pack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Type

from pydantic import BaseModel

Effect = Literal["read", "write", "sensitive"]
Verdict = Literal["allow", "deny", "approve"]
Approver = Literal["customer", "staff"]


@dataclass
class ToolContext:
    """Everything a tool may know about *who* is acting. Built by the engine,
    never by the model: the LLM cannot choose whose cart it touches."""

    user_id: Optional[str]
    session_id: Optional[str]          # chat thread / conversation id
    channel: str = "web"               # web | pwa | kiosk | telegram | proactive
    store_id: Optional[str] = None     # kiosk / pickup store, if any
    thread_id: Optional[str] = None
    agent: str = ""
    ctx: Dict[str, Any] = field(default_factory=dict)   # unified context snapshot
    run_id: Optional[str] = None


@dataclass
class ToolResult:
    ok: bool
    message: str                                   # short text the model reads
    data: Dict[str, Any] = field(default_factory=dict)
    ui: Optional[Dict[str, Any]] = None            # card payload for the client


@dataclass
class PolicyDecision:
    verdict: Verdict
    rule: str
    reason: str = ""
    approver: Optional[Approver] = None
    args: Optional[Dict[str, Any]] = None          # normalized/clamped args, if changed


@dataclass
class ToolSpec:
    name: str
    description: str
    args: Type[BaseModel]                          # model-visible arguments only
    fn: Callable[[ToolContext, BaseModel], ToolResult]
    effect: Effect = "read"
    policy: Optional[Callable[[ToolContext, BaseModel], PolicyDecision]] = None

    def catalog_entry(self) -> Dict[str, Any]:
        schema = self.args.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "effect": self.effect,
            "args": {k: v.get("type", v.get("anyOf", "any")) for k, v in schema.get("properties", {}).items()},
            "required": schema.get("required", []),
        }


@dataclass
class AgentSpec:
    name: str                      # node-safe id, e.g. "discovery"
    title: str                     # human label, e.g. "Discovery Agent"
    purpose: str                   # one line, shown to the planner
    instructions: str              # role prompt for the agent itself
    tools: List[str]
    max_actions: int = 4           # tool calls per plan step (bounds the inner cycle)


@dataclass
class DomainPack:
    name: str
    persona: str                                           # who the assistant is
    agents: List[AgentSpec]
    tools: Dict[str, ToolSpec]
    load_context: Callable[[ToolContext], Dict[str, Any]]  # unified context loader
    render_context: Callable[[Dict[str, Any]], str]        # compact text for prompts
    handoff: Callable[[ToolContext, str, str], ToolResult] # escalate to a human
    handoff_phrases: List[str] = field(default_factory=list)
    injection_markers: List[str] = field(default_factory=list)
    max_failures_before_handoff: int = 3
    max_plan_steps: int = 4
    max_total_actions: int = 10

    def agent(self, name: str) -> AgentSpec:
        for a in self.agents:
            if a.name == name:
                return a
        raise KeyError(name)

    def tools_for(self, agent: str) -> List[ToolSpec]:
        return [self.tools[t] for t in self.agent(agent).tools if t in self.tools]
