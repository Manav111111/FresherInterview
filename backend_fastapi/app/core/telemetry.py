"""
Fresher.AI — Centralized AI Engineering Observability & Telemetry Framework
Provides:
- Request correlation IDs (contextvars + X-Request-ID propagation)
- Structured token tracking (actual, estimated, unavailable)
- Component-level latency measurement using time.perf_counter()
- Real-world model pricing calculation
- Safe structured JSON event logging with secret & sensitive data scrubbing
"""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger("fresherai.telemetry")

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONTEXT-SCOPED REQUEST CORRELATION
# ─────────────────────────────────────────────────────────────────────────────

_request_id_ctx: ContextVar[str] = ContextVar("fresherai_request_id", default="")


def get_current_request_id() -> str:
    """Returns the current request ID from context or generates a new 8-char hex if absent."""
    rid = _request_id_ctx.get()
    if not rid:
        rid = f"req-{uuid.uuid4().hex[:8]}"
        _request_id_ctx.set(rid)
    return rid


def set_current_request_id(request_id: Optional[str] = None) -> str:
    """Sets the current request ID in contextvar, sanitizing input."""
    if not request_id or not str(request_id).strip():
        request_id = f"req-{uuid.uuid4().hex[:8]}"
    else:
        # Sanitize to alphanumeric, dashes, and underscores (max 64 chars)
        clean_id = re.sub(r"[^\w\-]", "", str(request_id).strip())[:64]
        request_id = clean_id or f"req-{uuid.uuid4().hex[:8]}"
    _request_id_ctx.set(request_id)
    return request_id


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA MODELS FOR TOKENS, PRICING, & METRICS
# ─────────────────────────────────────────────────────────────────────────────

class UsageType(str, Enum):
    ACTUAL = "actual"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class TokenUsage(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    usage_type: UsageType = UsageType.UNAVAILABLE


# Configured Pricing Structure per 1M tokens (USD)
# Groq: Llama 3.3 70B ($0.59 input / $0.79 output), GPT-OSS 120B / OpenAI ($0.50 / $0.80)
# Gemini: Gemini 2.0 Flash ($0.10 input / $0.40 output), Gemini 2.5 Pro ($1.25 input / $5.00 output)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Groq Models
    "groq:llama-3.3-70b-versatile": {"input_per_1m": 0.59, "output_per_1m": 0.79},
    "groq:openai/gpt-oss-120b": {"input_per_1m": 0.50, "output_per_1m": 0.80},
    "groq:llama-3.1-8b-instant": {"input_per_1m": 0.05, "output_per_1m": 0.08},
    # Gemini Models
    "gemini:gemini-2.0-flash": {"input_per_1m": 0.10, "output_per_1m": 0.40},
    "gemini:gemini-2.5-pro": {"input_per_1m": 1.25, "output_per_1m": 5.00},
    "gemini:gemini-1.5-flash": {"input_per_1m": 0.075, "output_per_1m": 0.30},
    "gemini:gemini-1.5-pro": {"input_per_1m": 1.25, "output_per_1m": 5.00},
}


def calculate_cost(
    provider: str,
    model: str,
    tokens: TokenUsage,
) -> Optional[float]:
    """
    Calculates estimated cost in USD based on configured pricing dictionary.
    Returns None if token count or pricing is unavailable.
    """
    if tokens.usage_type == UsageType.UNAVAILABLE or tokens.input_tokens is None or tokens.output_tokens is None:
        return None

    key = f"{provider.lower()}:{model.lower()}"
    pricing = MODEL_PRICING.get(key)
    if not pricing:
        # Check if model substring matches
        for p_key, p_val in MODEL_PRICING.items():
            if provider.lower() in p_key and model.lower() in p_key:
                pricing = p_val
                break

    if not pricing:
        return None

    cost = (tokens.input_tokens / 1_000_000.0 * pricing["input_per_1m"]) + (
        tokens.output_tokens / 1_000_000.0 * pricing["output_per_1m"]
    )
    return round(cost, 6)


class ProviderAttempt(BaseModel):
    provider: str
    model: str
    latency_ms: float
    status: str  # "success" or "error"
    error_type: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    estimated_cost: Optional[float] = None


class AIRequestMetrics(BaseModel):
    request_id: str = Field(default_factory=get_current_request_id)
    operation: str
    provider: str
    model: str
    latency_ms: float
    status: str = "success"
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    estimated_cost: Optional[float] = None
    fallback_used: bool = False
    attempts: List[ProviderAttempt] = Field(default_factory=list)
    error_type: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 3. SECRET AND SENSITIVE DATA SCRUBBING
# ─────────────────────────────────────────────────────────────────────────────

SECRET_SCRUB_PATTERNS = [
    (r"gsk_[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]"),
    (r"AIzaSy[a-zA-Z0-9_-]{30,}", "[REDACTED_API_KEY]"),
    (r"sb_secret_[a-zA-Z0-9_-]{15,}", "[REDACTED_SECRET]"),
    (r"rzp_(?:test|live)_[a-zA-Z0-9]{10,}", "[REDACTED_KEY]"),
    (r"postgres(?:ql)?:\/\/[^\s]+", "[REDACTED_DATABASE_URL]"),
    (r"redis:\/\/[^\s]+", "[REDACTED_REDIS_URL]"),
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer [REDACTED_TOKEN]"),
    (r"password['\":\s=]+[^\s,'\"]+", "password=[REDACTED]"),
]


def scrub_log_data(data: Union[str, Dict[str, Any], List[Any]]) -> Any:
    """Recursively redacts secrets and sensitive keys from log payloads."""
    if isinstance(data, str):
        cleaned = data
        for pat, repl in SECRET_SCRUB_PATTERNS:
            cleaned = re.sub(pat, repl, cleaned)
        return cleaned

    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ["key", "secret", "token", "password", "auth", "resume_text", "prompt", "useranswer"]):
                if isinstance(v, str):
                    sanitized[k] = f"[PROTECTED_DATA len={len(v)}]"
                else:
                    sanitized[k] = "[PROTECTED_DATA]"
            else:
                sanitized[k] = scrub_log_data(v)
        return sanitized

    if isinstance(data, list):
        return [scrub_log_data(item) for item in data]

    return data


# ─────────────────────────────────────────────────────────────────────────────
# 4. STRUCTURED TELEMETRY LOGGER
# ─────────────────────────────────────────────────────────────────────────────

class TelemetryLogger:
    """Emits scrubbed, structured JSON-compatible operational events."""

    @staticmethod
    def log_llm_event(metrics: AIRequestMetrics):
        event = {
            "event": "llm_call_completed" if metrics.status == "success" else "llm_call_failed",
            "request_id": metrics.request_id,
            "operation": metrics.operation,
            "provider": metrics.provider,
            "model": metrics.model,
            "latency_ms": metrics.latency_ms,
            "status": metrics.status,
            "fallback_used": metrics.fallback_used,
            "input_tokens": metrics.token_usage.input_tokens,
            "output_tokens": metrics.token_usage.output_tokens,
            "total_tokens": metrics.token_usage.total_tokens,
            "usage_type": metrics.token_usage.usage_type.value,
            "estimated_cost_usd": metrics.estimated_cost,
        }
        if metrics.attempts:
            event["attempts"] = [
                {
                    "provider": att.provider,
                    "model": att.model,
                    "latency_ms": att.latency_ms,
                    "status": att.status,
                    "error_type": att.error_type,
                }
                for att in metrics.attempts
            ]
        if metrics.error_type:
            event["error_type"] = metrics.error_type

        safe_event = scrub_log_data(event)
        if metrics.status == "success":
            logger.info(json.dumps(safe_event))
        else:
            logger.warning(json.dumps(safe_event))

    @staticmethod
    def log_retrieval_event(
        operation: str,
        latency_ms: float,
        top_k: int,
        result_count: int,
        collection: str = "fresher_ai_knowledge",
        request_id: Optional[str] = None,
        cached: bool = False,
    ):
        event = {
            "event": "retrieval_completed",
            "request_id": request_id or get_current_request_id(),
            "operation": operation,
            "collection": collection,
            "latency_ms": round(latency_ms, 2),
            "top_k": top_k,
            "result_count": result_count,
            "cached": cached,
            "status": "success",
        }
        logger.info(json.dumps(scrub_log_data(event)))

    @staticmethod
    def log_reranker_event(
        operation: str,
        latency_ms: float,
        candidate_count_before: int,
        candidate_count_after: int,
        model: str,
        status: str = "success",
        error_type: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        event = {
            "event": "reranker_completed" if status == "success" else "reranker_failed",
            "request_id": request_id or get_current_request_id(),
            "operation": operation,
            "latency_ms": round(latency_ms, 2),
            "candidate_count_before": candidate_count_before,
            "candidate_count_after": candidate_count_after,
            "reranker_model": model,
            "status": status,
        }
        if error_type:
            event["error_type"] = error_type
        safe_event = scrub_log_data(event)
        if status == "success":
            logger.info(json.dumps(safe_event))
        else:
            logger.warning(json.dumps(safe_event))

    @staticmethod
    def log_embedding_event(
        model: str,
        dimension: int,
        latency_ms: float,
        item_count: int = 1,
        is_fallback: bool = False,
        request_id: Optional[str] = None,
    ):
        event = {
            "event": "embedding_completed",
            "request_id": request_id or get_current_request_id(),
            "model": model,
            "dimension": dimension,
            "latency_ms": round(latency_ms, 2),
            "item_count": item_count,
            "is_fallback": is_fallback,
            "status": "success",
        }
        logger.info(json.dumps(scrub_log_data(event)))

    @staticmethod
    def log_cache_event(
        operation: str,
        key_prefix: str,
        latency_ms: float,
        hit: bool,
        request_id: Optional[str] = None,
    ):
        event = {
            "event": "cache_operation_completed",
            "request_id": request_id or get_current_request_id(),
            "operation": operation,
            "key_prefix": key_prefix,
            "latency_ms": round(latency_ms, 2),
            "cache_hit": hit,
            "status": "success",
        }
        logger.info(json.dumps(scrub_log_data(event)))

    @staticmethod
    def log_db_event(
        operation: str,
        table: str,
        latency_ms: float,
        status: str = "success",
        request_id: Optional[str] = None,
    ):
        event = {
            "event": "database_operation_completed",
            "request_id": request_id or get_current_request_id(),
            "operation": operation,
            "table": table,
            "latency_ms": round(latency_ms, 2),
            "status": status,
        }
        logger.info(json.dumps(scrub_log_data(event)))


telemetry = TelemetryLogger()
