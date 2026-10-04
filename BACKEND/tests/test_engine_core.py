"""Core engine tests with a toy domain and a scripted model (no network, no DB)."""
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agentic.core.registry import AgentSpec, DomainPack, PolicyDecision, ToolResult, ToolSpec
from app.agentic.core.graph import Engine
from app.agentic.core.llm import ModelGateway, ScriptedProvider
from app.agentic.core.journal import MemoryJournal
from app.agentic.core.memory import InMemoryStore

LEDGER = {"balance": 100}

class Amount(BaseModel):
    amount: int

class Empty(BaseModel):
    pass

def get_balance(tc, a): return ToolResult(True, f"balance is {LEDGER['balance']} for {tc.user_id}", {"balance": LEDGER["balance"]})
def pay(tc, a):
    LEDGER["balance"] -= a.amount
    return ToolResult(True, f"paid {a.amount}", {"paid": a.amount}, ui={"type": "receipt", "amount": a.amount})
def pay_policy(tc, a):
    if a.amount <= 0: return PolicyDecision("deny", "positive_amount", "amount must be positive")
    if a.amount > 50: return PolicyDecision("approve", "large_payment", f"{a.amount} exceeds 50", approver="staff")
    return PolicyDecision("allow", "small_payment")

def pack():
    return DomainPack(
        name="toy", persona="You are a toy bank.",
        agents=[AgentSpec("accounts", "Accounts Agent", "balances", "Read balances.", ["get_balance"]),
                AgentSpec("payments", "Payments Agent", "payments", "Make payments.", ["pay"])],
        tools={"get_balance": ToolSpec("get_balance", "read balance", Empty, get_balance),
               "pay": ToolSpec("pay", "pay an amount", Amount, pay, effect="sensitive", policy=pay_policy)},
        load_context=lambda tc: {"user": tc.user_id, "channel": tc.channel},
        render_context=lambda c: str(c),
        handoff=lambda tc, r, s: ToolResult(True, "queued", {"handoff_id": "h1"}),
        handoff_phrases=["human please"], injection_markers=["ignore previous"])

def script_factory(amount):
    state = {"pay_calls": 0, "bal_calls": 0}
    def script(node, system, user):
        if node == "planner":
            return {"reasoning": "check then pay", "respond_directly": False,
                    "steps": [{"agent": "accounts", "objective": "read balance"},
                              {"agent": "payments", "objective": f"pay {amount}"}]}
        if node == "agent_accounts":
            if "get_balance(" in user: return {"thought": "done", "action": "finish", "summary": "balance read"}
            return {"thought": "read it", "action": "call_tool", "tool": "get_balance", "args": {}}
        if node == "agent_payments":
            if "pay(" in user or "rejected" in user or "denied" in user:
                return {"thought": "done", "action": "finish", "summary": "payment handled", "remember": "pays rent monthly"}
            return {"thought": "pay", "action": "call_tool", "tool": "pay", "args": {"amount": amount}}
        if node == "reflect": return {"satisfied": True, "critique": "ok"}
        if node == "synthesize": return {"reply": "All done."}
        raise AssertionError(node)
    return script

def run(amount, resume=None):
    LEDGER["balance"] = 100
    sp = ScriptedProvider(script_factory(amount))
    gw = ModelGateway(providers=[sp])
    j, mem = MemoryJournal(), InMemoryStore()
    eng = Engine(pack(), memory=mem, journal=j, gateway_fn=lambda: gw)
    app = eng.build().compile(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t1"}, "recursion_limit": eng.recursion_limit()}
    out = app.invoke({"thread_id": "t1", "user_id": "u1", "session_id": "s1", "channel": "web", "mode": "chat",
                      "input": f"pay {amount}"}, cfg)
    if resume is not None:
        out = app.invoke(Command(resume=resume), cfg)
    return out, sp, j, mem

def test_small_payment_runs_end_to_end():
    out, sp, j, mem = run(20)
    assert LEDGER["balance"] == 80
    assert out["reply"] == "All done."
    assert [p["status"] for p in out["plan"]] == ["done", "done"]
    assert sp.calls[0] == "planner" and "agent_payments" in sp.calls
    assert len(j.actions) == 2
    assert any("pays rent" in m.content for m in mem.recall("toy", "payments", "u1", "pay", 10))
    assert mem.recall("toy", "accounts", "u1", "pays rent", 10)[0].content.startswith("Asked")  # memories are per agent

def test_large_payment_interrupts_then_executes_on_approval():
    out, sp, j, _ = run(70)
    assert "__interrupt__" in out and LEDGER["balance"] == 100
    out, sp, j, _ = run(70, resume={"approved": True, "by": "staff-1"})
    assert LEDGER["balance"] == 30
    assert len(j.approvals) == 1

def test_rejection_skips_execution():
    out, _, j, _ = run(70, resume={"approved": False, "by": "staff-1", "note": "too big"})
    assert LEDGER["balance"] == 100
    assert out["reply"] == "All done."

def test_policy_deny_never_executes():
    out, _, j, _ = run(-5)
    assert LEDGER["balance"] == 100
    assert any(p["verdict"] == "deny" for p in j.policies)
