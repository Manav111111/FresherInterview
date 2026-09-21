"""
Tests for Phase 2: AI Engineering Observability, Token & Cost Tracking.

Covers:
1. Request ID Middleware & Generation (X-Request-ID preservation and creation)
2. ContextVar request ID propagation across async tasks
3. Token usage normalization (actual vs unavailable vs estimated)
4. Cost calculation with configured MODEL_PRICING and missing pricing
5. Component latency measurements (time.perf_counter positive duration)
6. Dual-provider fallback telemetry (primary fails -> secondary succeeds with attempt logs)
7. Sensitive data and secret scrubbing in structured log payloads
"""

import asyncio
import json
import logging
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.telemetry import (
    get_current_request_id,
    set_current_request_id,
    UsageType,
    TokenUsage,
    MODEL_PRICING,
    calculate_cost,
    scrub_log_data,
    telemetry,
    AIRequestMetrics,
    ProviderAttempt,
)
from app.ai.provider_router import AIProviderRouter
from app.ai.schemas import AIResponse, AIProviderName


@pytest.fixture
def client():
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 1. REQUEST ID & CONTEXT PROPAGATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_request_id_generated_when_missing(client):
    """When client provides no X-Request-ID, the server generates one and returns it."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    req_id = response.headers["x-request-id"]
    assert req_id.startswith("req-")
    assert "x-response-time-ms" in response.headers


def test_request_id_preserved_when_supplied(client):
    """When client passes X-Request-ID, the server respects and propagates it."""
    custom_id = "test-req-correlation-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


def test_request_id_sanitized(client):
    """Request ID is sanitized to alphanumeric and hyphens, preventing header injection."""
    malicious_id = "req;drop-table\r\nBadHeader: evil"
    response = client.get("/health", headers={"X-Request-ID": malicious_id})
    assert response.status_code == 200
    returned_id = response.headers.get("x-request-id")
    assert "\r" not in returned_id
    assert "\n" not in returned_id
    assert ";" not in returned_id


@pytest.mark.asyncio
async def test_contextvar_request_id_isolation():
    """ContextVar preserves per-coroutine request IDs across concurrent tasks."""
    async def task_worker(task_id: str):
        set_current_request_id(task_id)
        await asyncio.sleep(0.01)
        return get_current_request_id()

    results = await asyncio.gather(
        task_worker("req-task-alpha"),
        task_worker("req-task-beta"),
        task_worker("req-task-gamma"),
    )
    assert results == ["req-task-alpha", "req-task-beta", "req-task-gamma"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. TOKEN USAGE NORMALIZATION & COST ESTIMATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_token_usage_actual_calculation():
    """Actual token counts compute precise cost according to configured pricing."""
    tokens = TokenUsage(
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        usage_type=UsageType.ACTUAL,
    )
    # Groq Llama 3.3 70B: $0.59 / 1M in, $0.79 / 1M out
    # 1000/1e6 * 0.59 + 500/1e6 * 0.79 = 0.00059 + 0.000395 = 0.000985
    cost = calculate_cost("groq", "llama-3.3-70b-versatile", tokens)
    assert cost is not None
    assert round(cost, 6) == 0.000985


def test_token_usage_unavailable_returns_none():
    """When token usage is UNAVAILABLE, cost estimation must return None, not fake 0."""
    tokens = TokenUsage(
        input_tokens=None,
        output_tokens=None,
        total_tokens=None,
        usage_type=UsageType.UNAVAILABLE,
    )
    cost = calculate_cost("groq", "llama-3.3-70b-versatile", tokens)
    assert cost is None


def test_unconfigured_model_cost_returns_none():
    """If model pricing is not in MODEL_PRICING, cost returns None without error."""
    tokens = TokenUsage(
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        usage_type=UsageType.ACTUAL,
    )
    cost = calculate_cost("unknown_provider", "mystery-model-v99", tokens)
    assert cost is None


def test_gemini_pricing_calculation():
    """Gemini 2.0 Flash cost matches official rate table ($0.10 in / $0.40 out per 1M)."""
    tokens = TokenUsage(
        input_tokens=10000,
        output_tokens=2000,
        total_tokens=12000,
        usage_type=UsageType.ACTUAL,
    )
    cost = calculate_cost("gemini", "gemini-2.0-flash", tokens)
    assert cost is not None
    # 10,000 / 1e6 * 0.10 + 2,000 / 1e6 * 0.40 = 0.0010 + 0.0008 = 0.0018
    assert round(cost, 6) == 0.0018


# ─────────────────────────────────────────────────────────────────────────────
# 3. SECRET & SENSITIVE DATA SCRUBBING TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_secret_scrubbing_api_keys_and_passwords():
    """Verify secrets (Groq, Gemini, Bearer tokens, DB credentials) are redacted."""
    raw_payload = {
        "event": "llm_call",
        "api_key": "gsk_1234567890abcdef1234567890abcdef",
        "gemini_key": "AIzaSyDummyKeyForGoogleCloudAPIChecks12345",
        "auth_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz",
        "database_url": "postgresql://postgres:secretpassword@localhost:5432/fresherai",
        "redis_url": "redis://:supersecretpass@localhost:6379/0",
        "prompt": "Applicant resume content with private phone numbers",
        "user_data": {
            "token": "sensitive_session_token",
            "safe_field": "public_data"
        }
    }

    scrubbed = scrub_log_data(raw_payload)

    # Convert to json string to ensure no leak
    serialized = json.dumps(scrubbed)
    assert "gsk_" not in serialized
    assert "AIzaSy" not in serialized
    assert "secretpassword" not in serialized
    assert "supersecretpass" not in serialized
    assert "Applicant resume content" not in serialized
    assert "sensitive_session_token" not in serialized
    assert scrubbed["user_data"]["safe_field"] == "public_data"


# ─────────────────────────────────────────────────────────────────────────────
# 4. DUAL-PROVIDER FALLBACK TELEMETRY TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_router_fallback_telemetry(monkeypatch):
    """
    Simulate Groq failing and Gemini succeeding.
    Verify:
    1. Overall response succeeds
    2. Telemetry records both attempts (Groq error + Gemini success)
    3. Latencies are captured
    """
    router = AIProviderRouter()

    # Mock groq to raise Exception
    mock_groq = AsyncMock()
    mock_groq.generate = AsyncMock(side_effect=RuntimeError("Groq 429 Rate Limit Exceeded"))
    mock_groq.model_name = "llama-3.3-70b-versatile"

    # Mock gemini to succeed
    mock_gemini = AsyncMock()
    mock_gemini.generate = AsyncMock(return_value=AIResponse(
        content='{"feedback": "Great interview answer"}',
        provider=AIProviderName.GEMINI,
        model="gemini-2.0-flash",
        latency_ms=310.5,
        input_tokens=450,
        output_tokens=60,
        total_tokens=510,
        token_usage_type=UsageType.ACTUAL,
        estimated_cost_usd=0.000069,
    ))
    mock_gemini.model_name = "gemini-2.0-flash"

    router.groq = mock_groq
    router.gemini = mock_gemini

    with patch.object(telemetry, "log_llm_event") as mock_log_event:
        from app.ai.schemas import AIRequest, TaskType
        req = AIRequest(
            task_type=TaskType.FAST_INTERVIEW_QUESTION,
            prompt="Evaluate candidate response",
            operation="interview_evaluation",
        )
        response = await router.execute(req)

        assert response is not None
        assert response.provider == AIProviderName.GEMINI
        assert response.latency_ms > 0
        assert len(response.attempts) == 2

        # Verify attempt 1 is Groq error
        att1 = response.attempts[0]
        assert att1["provider"] == "groq"
        assert att1["status"] == "error"
        assert "RuntimeError" in att1["error_type"]

        # Verify attempt 2 is Gemini success
        att2 = response.attempts[1]
        assert att2["provider"] == "gemini"
        assert att2["status"] == "success"

        # Verify telemetry event was logged
        assert mock_log_event.called
        call_arg = mock_log_event.call_args[0][0]
        assert isinstance(call_arg, AIRequestMetrics)
        assert call_arg.fallback_used is True
        assert call_arg.status == "success"
        assert call_arg.provider == "gemini"


# ─────────────────────────────────────────────────────────────────────────────
# 5. COMPONENT-LEVEL LATENCY TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_component_events_log_positive_duration(caplog):
    """Verify retrieval, embedding, cache, and db events log positive latency and correlation id."""
    caplog.set_level(logging.INFO)
    set_current_request_id("req-test-timing-101")

    # Log events
    telemetry.log_retrieval_event(
        operation="interview_questions",
        latency_ms=45.2,
        top_k=5,
        result_count=5,
        collection="fresher_ai_knowledge",
    )

    telemetry.log_embedding_event(
        model="text-embedding-004",
        dimension=768,
        latency_ms=32.1,
        item_count=1,
    )

    telemetry.log_cache_event(
        operation="get",
        key_prefix="chat:session",
        latency_ms=1.45,
        hit=True,
    )

    telemetry.log_db_event(
        operation="insert",
        table="interview_sessions",
        latency_ms=15.8,
    )

    records = [json.loads(rec.message) for rec in caplog.records if "req-test-timing-101" in rec.message]
    assert len(records) == 4

    # Check retrieval record
    ret_rec = next(r for r in records if r["event"] == "retrieval_completed")
    assert ret_rec["latency_ms"] == 45.2
    assert ret_rec["top_k"] == 5
    assert ret_rec["request_id"] == "req-test-timing-101"

    # Check embedding record
    emb_rec = next(r for r in records if r["event"] == "embedding_completed")
    assert emb_rec["latency_ms"] == 32.1
    assert emb_rec["model"] == "text-embedding-004"

    # Check cache record
    cache_rec = next(r for r in records if r["event"] == "cache_operation_completed")
    assert cache_rec["cache_hit"] is True
    assert cache_rec["latency_ms"] == 1.45

    # Check db record
    db_rec = next(r for r in records if r["event"] == "database_operation_completed")
    assert db_rec["table"] == "interview_sessions"
    assert db_rec["latency_ms"] == 15.8
