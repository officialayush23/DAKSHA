"""
Model gateway for the DAKSHA orchestration engine.

Every reasoning node in the graph talks to models through `ModelGateway.json()`.
The gateway asks for a JSON object that matches a Pydantic schema, validates it,
and retries once with the validation error if the model got it wrong. Nodes
never see raw model text, so a malformed answer can't leak into state.

Providers (tried in order, see LLM_PROVIDER_ORDER):
  gemini   - google-genai SDK. Works with an AI Studio key, a Vertex express
             key ("AQ." prefix) or a Vertex service account.
  bedrock  - Amazon Bedrock Converse API with a Bedrock API key (bearer token).
             Default model is xAI Grok via the US cross-region profile.
  scripted - deterministic fake used by tests and offline benchmarks.

A small circuit breaker skips a provider for COOLDOWN_S seconds after
FAIL_THRESHOLD consecutive failures, so one dead provider doesn't add its
timeout to every turn.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

log = logging.getLogger("daksha.llm")

T = TypeVar("T", bound=BaseModel)

FAIL_THRESHOLD = 2
COOLDOWN_S = 60.0


def _is_rate_limit(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "503" in s or "UNAVAILABLE" in s or "overloaded" in s.lower()


def _retry_after(e: Exception) -> float:
    m = re.search(r"retry in ([0-9.]+)s", str(e)) or re.search(r"'retryDelay': '([0-9.]+)s'", str(e))
    secs = float(m.group(1)) if m else 60.0
    return min(max(secs, 5.0), 3600.0)


class LLMUnavailable(RuntimeError):
    """Raised when every configured provider failed for a call."""


@dataclass
class CallStats:
    provider: str
    model: str
    latency_ms: float
    attempts: int
    ok: bool
    error: Optional[str] = None


@dataclass
class _Breaker:
    failures: int = 0
    open_until: float = 0.0

    def available(self) -> bool:
        return time.monotonic() >= self.open_until

    def record(self, ok: bool) -> None:
        if ok:
            self.failures = 0
            self.open_until = 0.0
            return
        self.failures += 1
        if self.failures >= FAIL_THRESHOLD:
            self.open_until = time.monotonic() + COOLDOWN_S


def _env(*names: str, default: str = "") -> str:
    for n in names:
        v = os.environ.get(n)
        if v is None:
            try:
                from app.core.config import settings  # late import, optional in tests
                v = getattr(settings, n, None)
            except Exception:
                v = None
        if v:
            return str(v).strip().strip('"').strip("'")
    return default


def _extract_json(text: str) -> Any:
    """Pull the first JSON object out of a model reply (handles ``` fences)."""
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start : end + 1])


# ─────────────────────────────────────────────────────────────────────────────
# Providers
# ─────────────────────────────────────────────────────────────────────────────

class Provider:
    name = "base"
    model = ""

    def configured(self) -> bool:
        return False

    def complete(self, system: str, user: str, schema: Dict[str, Any]) -> str:
        raise NotImplementedError


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self) -> None:
        self.model = _env("GEMINI_MODEL", default="gemini-3.5-flash")
        fallbacks = _env("GEMINI_FALLBACK_MODELS", default="gemini-3.5-flash-lite,gemini-3-flash-preview,gemini-2.5-flash")
        self.models = [self.model] + [m.strip() for m in fallbacks.split(",") if m.strip() and m.strip() != self.model]
        self.thinking_level = _env("GEMINI_THINKING_LEVEL", default="low")
        self._client = None
        self._lock = threading.Lock()
        self._cool: Dict[str, float] = {}     # model -> monotonic time it may be used again

    def configured(self) -> bool:
        return bool(
            _env("GEMINI_API_KEY", "GEMINI_VERTEX_API_KEY", "VERTEX_API_KEY")
            or _env("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        )

    def _candidates(self):
        from google import genai

        keys = []
        for n in ("GEMINI_API_KEY", "GEMINI_VERTEX_API_KEY", "VERTEX_API_KEY"):
            k = _env(n)
            if k and k not in keys:
                keys.append(k)
        project = _env("GOOGLE_CLOUD_PROJECT")
        location = _env("GOOGLE_CLOUD_LOCATION", "VERTEX_AI_LOCATION", default="us-central1")
        for i, key in enumerate(keys):
            # AI Studio style first, then Vertex express mode (same "AQ." key format)
            yield f"studio#{i}", (lambda k=key: genai.Client(api_key=k))
            yield f"vertex-express#{i}", (lambda k=key: genai.Client(vertexai=True, api_key=k))
        if project and _env("GOOGLE_APPLICATION_CREDENTIALS_JSON", "GOOGLE_APPLICATION_CREDENTIALS"):
            yield "vertex-sa", lambda: genai.Client(vertexai=True, project=project, location=location)

    def _config(self, model: str, system: str, schema: Dict[str, Any]):
        from google.genai import types

        cfg: Dict[str, Any] = {
            "system_instruction": system,
            "response_mime_type": "application/json",
            "response_json_schema": schema,
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        }
        if model.startswith("gemini-3"):
            cfg["thinking_config"] = types.ThinkingConfig(thinking_level=self.thinking_level)
        elif model.startswith("gemini-2.5-flash"):
            cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        return types.GenerateContentConfig(**cfg)

    def _client_for_call(self, model, system, user, schema):
        if self._client is not None:
            return self._client, self._client.models.generate_content(
                model=model, contents=user, config=self._config(model, system, schema))
        last: Optional[Exception] = None
        for label, factory in self._candidates():
            try:
                client = factory()
                r = client.models.generate_content(model=model, contents=user, config=self._config(model, system, schema))
                with self._lock:
                    self._client = client
                log.info("gemini auth mode selected: %s", label)
                return client, r
            except Exception as e:
                if _is_rate_limit(e):
                    raise
                last = e
                log.warning("gemini auth mode %s failed: %s", label, str(e)[:200])
        raise last or RuntimeError("gemini not configured")

    def complete(self, system: str, user: str, schema: Dict[str, Any]) -> str:
        """Try the primary model, then fallbacks; a model that hits its quota rests for a while.
        (Free-tier quotas are per model, so rotating keeps the assistant up.)"""
        last: Optional[Exception] = None
        now = time.monotonic()
        for model in self.models:
            if self._cool.get(model, 0) > now:
                continue
            try:
                _, r = self._client_for_call(model, system, user, schema)
                self.last_model = model
                return r.text or ""
            except Exception as e:
                last = e
                if _is_rate_limit(e):
                    self._cool[model] = time.monotonic() + _retry_after(e)
                    log.warning("gemini model %s rate-limited; trying next", model)
                    continue
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    self._cool[model] = time.monotonic() + 86400
                    log.warning("gemini model %s not available; skipping", model)
                    continue
                raise
        raise last or RuntimeError("all gemini models cooling down")


class BedrockProvider(Provider):
    """Bedrock Converse API over HTTPS with a Bedrock API key (bearer token)."""

    name = "bedrock"

    def __init__(self) -> None:
        self.model = _env("BEDROCK_MODEL_ID", default="us.xai.grok-4.7")
        self.region = _env("AWS_REGION", default="us-east-1")

    def _token(self) -> str:
        return _env("AWS_BEARER_TOKEN_BEDROCK", "AWS_API_KEY_BEDROCK_FOR_XAI")

    def configured(self) -> bool:
        return bool(self._token())

    def complete(self, system: str, user: str, schema: Dict[str, Any]) -> str:
        url = f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{self.model}/converse"
        prompt = (
            f"{user}\n\nReply with ONE JSON object only, no prose, matching this JSON schema:\n"
            f"{json.dumps(schema)}"
        )
        body = {
            "system": [{"text": system}],
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 2048, "temperature": 0.1},
        }
        r = httpx.post(
            url,
            json=body,
            headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "application/json"},
            timeout=45,
        )
        r.raise_for_status()
        data = r.json()
        parts = data.get("output", {}).get("message", {}).get("content", [])
        return "".join(p.get("text", "") for p in parts)


class ScriptedProvider(Provider):
    """
    Deterministic stand-in for tests and offline benchmarks.

    `script` is a callable (node_name, system, user) -> dict. The node name is
    passed in the system prompt header so one script can drive a whole graph.
    """

    name = "scripted"

    def __init__(self, script: Callable[[str, str, str], Dict[str, Any]], latency_s: float = 0.0):
        self.script = script
        self.latency_s = latency_s
        self.model = "scripted"
        self.calls: List[str] = []

    def configured(self) -> bool:
        return True

    def complete(self, system: str, user: str, schema: Dict[str, Any]) -> str:
        m = re.search(r"\[node:([a-z_]+)\]", system)
        node = m.group(1) if m else "unknown"
        self.calls.append(node)
        if self.latency_s:
            time.sleep(self.latency_s)
        return json.dumps(self.script(node, system, user))


# ─────────────────────────────────────────────────────────────────────────────
# Gateway
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ModelGateway:
    providers: List[Provider] = field(default_factory=list)
    breakers: Dict[str, _Breaker] = field(default_factory=dict)
    history: List[CallStats] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "ModelGateway":
        order = _env("LLM_PROVIDER_ORDER", default="")
        if not order:
            primary = _env("LLM_PROVIDER", default="gemini").lower()
            order = "gemini,bedrock" if primary != "bedrock" else "bedrock,gemini"
        table = {"gemini": GeminiProvider, "bedrock": BedrockProvider}
        providers = [table[p.strip()]() for p in order.split(",") if p.strip() in table]
        token = _env("AWS_API_KEY_BEDROCK_FOR_XAI")
        if token and not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
        return cls(providers=[p for p in providers if p.configured()])

    def json(self, node: str, system: str, user: str, schema: Type[T], max_attempts: int = 2) -> T:
        """Ask for a JSON object matching `schema`. Validates and self-corrects once."""
        system = f"[node:{node}]\n{system}"
        json_schema = schema.model_json_schema()
        errors: List[str] = []
        for provider in self.providers:
            br = self.breakers.setdefault(provider.name, _Breaker())
            if not br.available():
                continue
            prompt = user
            t0 = time.perf_counter()
            for attempt in range(1, max_attempts + 1):
                try:
                    raw = provider.complete(system, prompt, json_schema)
                    obj = schema.model_validate(_extract_json(raw))
                    br.record(True)
                    self.history.append(CallStats(provider.name, getattr(provider, "last_model", provider.model),
                                                  (time.perf_counter() - t0) * 1000, attempt, True))
                    return obj
                except (ValidationError, ValueError, json.JSONDecodeError) as e:
                    # model answered but the shape was wrong: tell it and retry
                    errors.append(f"{provider.name}: invalid output: {str(e)[:200]}")
                    prompt = (f"{user}\n\nYour previous answer was rejected by the validator:\n"
                              f"{str(e)[:600]}\nReturn a corrected JSON object.")
                except Exception as e:
                    errors.append(f"{provider.name}: {type(e).__name__}: {str(e)[:200]}")
                    break
            # a pure rate-limit on every model is not a broken provider: don't open the breaker
            if not (errors and ("429" in errors[-1] or "RESOURCE_EXHAUSTED" in errors[-1] or "cooling down" in errors[-1])):
                br.record(False)
            self.history.append(CallStats(provider.name, provider.model,
                                          (time.perf_counter() - t0) * 1000, max_attempts, False,
                                          errors[-1] if errors else None))
        if not errors:
            raise LLMUnavailable("no LLM provider available (none configured or all cooling down)")
        raise LLMUnavailable("; ".join(errors))


_gateway: Optional[ModelGateway] = None
_gw_lock = threading.Lock()


def get_gateway() -> ModelGateway:
    global _gateway
    if _gateway is None:
        with _gw_lock:
            if _gateway is None:
                _gateway = ModelGateway.from_env()
    return _gateway


def set_gateway(gw: ModelGateway) -> None:
    """Used by tests/benchmarks to swap in a scripted gateway."""
    global _gateway
    _gateway = gw
