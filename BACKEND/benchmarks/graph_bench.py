"""
Orchestration overhead and termination bounds, with the REAL commerce graph but a
scripted model and stub tools (no network, no database).

1. Overhead: wall time of one turn minus the time spent inside model calls and
   tools, for plans of 1-4 steps x 1-3 tool calls each.
2. Termination: a hostile model that never says "finish" and keeps calling
   tools; we count supersteps until the graph stops.

    python benchmarks/graph_bench.py
"""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("DATABASE_URL", "postgresql://x:y@localhost:1/none")
for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET"):
    os.environ.setdefault(k, "x")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from app.agentic.commerce import pack as commerce  # noqa: E402
from app.agentic.core.graph import Engine  # noqa: E402
from app.agentic.core.journal import MemoryJournal  # noqa: E402
from app.agentic.core.llm import ModelGateway, ScriptedProvider  # noqa: E402
from app.agentic.core.memory import InMemoryStore  # noqa: E402
from app.agentic.core.registry import ToolResult  # noqa: E402

READ_TOOLS = ["view_cart", "my_orders", "loyalty_status", "trending_now", "my_offers", "my_profile", "my_returns"]


def stub_pack():
    p = commerce.build_pack()
    p.load_context = lambda tc: {"customer": {"name": "bench", "tier": "silver"}, "cart": {"items": [], "total": 0},
                                 "channel": tc.channel, "channels_used": [tc.channel]}
    for t in p.tools.values():
        t.fn = (lambda name: (lambda tc, a: ToolResult(True, f"{name} ok", {})))(t.name)
        t.policy = None
    p.handoff = lambda tc, r, s: ToolResult(True, "handoff", {"handoff_id": "h"})
    return p


def run(steps: int, calls: int, trials: int = 30):
    pack = stub_pack()
    agents = ["support", "fulfillment", "offers", "post_purchase"][:steps]
    tool_for = {"support": "my_profile", "fulfillment": "my_orders", "offers": "loyalty_status", "post_purchase": "my_returns"}

    def script(node, system, user):
        if node == "planner":
            return {"reasoning": "bench", "respond_directly": False,
                    "steps": [{"agent": a, "objective": f"objective {i}"} for i, a in enumerate(agents)]}
        if node.startswith("agent_"):
            done = user.count("→ OK")
            if done >= calls:
                return {"thought": "done", "action": "finish", "summary": "ok"}
            return {"thought": "act", "action": "call_tool", "tool": tool_for[node[6:]], "args": {}}
        if node == "reflect":
            return {"satisfied": True, "critique": "ok"}
        return {"reply": "done"}

    sp = ScriptedProvider(script)
    gw = ModelGateway(providers=[sp])
    eng = Engine(pack, memory=InMemoryStore(), journal=MemoryJournal(), gateway_fn=lambda: gw)
    app = eng.build().compile(checkpointer=MemorySaver())
    times, llm_calls, supersteps = [], [], []
    for i in range(trials):
        cfg = {"configurable": {"thread_id": f"b{steps}{calls}{i}"}, "recursion_limit": eng.recursion_limit()}
        n0 = len(sp.calls)
        t0 = time.perf_counter()
        steps_seen = 0
        for _ in app.stream({"thread_id": cfg["configurable"]["thread_id"], "user_id": "u", "session_id": "s",
                             "channel": "web", "mode": "chat", "input": "bench"}, cfg, stream_mode="updates"):
            steps_seen += 1
        times.append((time.perf_counter() - t0) * 1000)
        llm_calls.append(len(sp.calls) - n0)
        supersteps.append(steps_seen)
    return {"plan_steps": steps, "tools_per_step": calls, "llm_calls": statistics.mean(llm_calls),
            "supersteps": statistics.mean(supersteps), "overhead_ms_p50": round(statistics.median(times), 2),
            "overhead_ms_p95": round(sorted(times)[int(len(times) * 0.95) - 1], 2)}


def hostile():
    """Model never finishes and keeps calling tools; count supersteps until stop."""
    pack = stub_pack()

    def script(node, system, user):
        if node == "planner":
            return {"reasoning": "x", "respond_directly": False,
                    "steps": [{"agent": a, "objective": "loop forever"} for a in ["support", "fulfillment", "offers", "cart", "discovery", "post_purchase"]]}
        if node.startswith("agent_"):
            tools = {"support": "my_profile", "fulfillment": "my_orders", "offers": "loyalty_status", "cart": "view_cart",
                     "discovery": "trending_now", "post_purchase": "my_returns"}
            return {"thought": "again", "action": "call_tool", "tool": tools[node[6:]], "args": {}}
        if node == "reflect":
            return {"satisfied": False, "critique": "try again", "retry_hint": "keep going"}
        return {"reply": "stopped"}

    sp = ScriptedProvider(script)
    gw = ModelGateway(providers=[sp])
    eng = Engine(pack, memory=InMemoryStore(), journal=MemoryJournal(), gateway_fn=lambda: gw, critic_on_success=True)
    app = eng.build().compile(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "hostile"}, "recursion_limit": eng.recursion_limit()}
    n = 0
    final = None
    for upd in app.stream({"thread_id": "hostile", "user_id": "u", "session_id": "s", "channel": "web", "mode": "chat",
                           "input": "x"}, cfg, stream_mode="updates"):
        n += 1
        final = upd
    st = app.get_state(cfg).values
    return {"supersteps": n, "tool_actions": st.get("actions_used"), "llm_calls": len(sp.calls),
            "recursion_limit": eng.recursion_limit(), "terminated": True,
            "plan_status": [p["status"] for p in st.get("plan", [])]}


if __name__ == "__main__":
    rows = [run(s, c) for s in (1, 2, 4) for c in (1, 3)]
    h = hostile()
    print(json.dumps({"overhead": rows, "hostile_model": h}, indent=1))
    json.dump({"overhead": rows, "hostile_model": h}, open(os.path.join(os.path.dirname(__file__), "graph_bench.json"), "w"), indent=1)
