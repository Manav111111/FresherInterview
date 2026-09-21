import uuid
import logging
from typing import Optional, Dict, Any, List
from app.config import settings
from app.ai.schemas import (
    TaskType,
    AIProviderName,
    AIRequest,
    AIResponse,
)
from app.ai.groq_provider import GroqProvider
from app.ai.gemini_provider import GeminiProvider

logger = logging.getLogger("fresherai.ai_router")


class AIProviderRouter:
    """
    Centralized Multimodal AI Provider Router for Fresher.AI.
    Dynamically routes tasks between Groq (high-speed) and Gemini (deep reasoning & multimodal)
    with seamless automatic fallback, retry handling, and observability telemetry.
    """

    def __init__(self):
        self.groq = GroqProvider()
        self.gemini = GeminiProvider()

    def select_primary_provider(self, task_type: TaskType, preferred: Optional[AIProviderName] = None) -> AIProviderName:
        """Determines the optimal primary provider based on latency and reasoning requirements."""
        if preferred:
            return preferred

        # Fast latency-critical tasks -> Groq
        if task_type in [
            TaskType.FAST_INTERVIEW_QUESTION,
            TaskType.REAL_TIME_FOLLOWUP,
            TaskType.FAST_EVALUATION,
        ]:
            return AIProviderName.GROQ

        # Deep reasoning, multimodal, and comprehensive analysis -> Gemini
        if task_type in [
            TaskType.DEEP_EVALUATION,
            TaskType.FINAL_REPORT,
            TaskType.RESUME_ATS_ANALYSIS,
            TaskType.VIDEO_STORYBOARD,
            TaskType.ROADMAP_GENERATION,
        ]:
            return AIProviderName.GEMINI

        return AIProviderName.GROQ

    async def execute(self, req: AIRequest) -> AIResponse:
        """
        Executes an AI request with primary routing, detailed attempt tracking, and automatic fallback.
        """
        import time
        from app.core.telemetry import (
            get_current_request_id,
            telemetry,
            AIRequestMetrics,
            ProviderAttempt,
            TokenUsage,
            UsageType,
        )

        request_id = get_current_request_id()
        primary = self.select_primary_provider(req.task_type, req.preferred_provider)
        secondary = AIProviderName.GEMINI if primary == AIProviderName.GROQ else AIProviderName.GROQ

        providers_to_try = [primary, secondary]
        attempts: List[ProviderAttempt] = []
        last_error = None
        router_start = time.perf_counter()

        for idx, provider_name in enumerate(providers_to_try):
            is_fallback = idx > 0
            attempt_start = time.perf_counter()
            chosen_model = ""
            try:
                if provider_name == AIProviderName.GROQ:
                    chosen_model = settings.GROQ_FAST_MODEL if req.task_type == TaskType.FAST_INTERVIEW_QUESTION else settings.GROQ_COMPLEX_MODEL
                    res = await self.groq.generate(
                        prompt=req.prompt,
                        system_prompt=req.system_prompt,
                        model=chosen_model,
                        temperature=req.temperature,
                        json_mode=req.json_mode,
                        timeout_seconds=req.timeout_seconds,
                    )
                else:
                    chosen_model = settings.GEMINI_COMPLEX_MODEL if req.task_type in [TaskType.FINAL_REPORT, TaskType.RESUME_ATS_ANALYSIS] else settings.GEMINI_FAST_MODEL
                    res = await self.gemini.generate(
                        prompt=req.prompt,
                        system_prompt=req.system_prompt,
                        model=chosen_model,
                        temperature=req.temperature,
                        json_mode=req.json_mode,
                        images=req.images,
                        timeout_seconds=req.timeout_seconds,
                    )

                att_latency = (time.perf_counter() - attempt_start) * 1000.0
                attempt_record = ProviderAttempt(
                    provider=res.provider,
                    model=res.model,
                    latency_ms=round(att_latency, 2),
                    status="success",
                    token_usage=TokenUsage(
                        input_tokens=res.input_tokens,
                        output_tokens=res.output_tokens,
                        total_tokens=res.total_tokens,
                        usage_type=UsageType(res.token_usage_type) if res.token_usage_type in ["actual", "estimated", "unavailable"] else UsageType.UNAVAILABLE,
                    ),
                    estimated_cost=res.estimated_cost_usd,
                )
                attempts.append(attempt_record)

                res.fallback_used = is_fallback
                res.request_id = request_id
                res.attempts = [att.model_dump() for att in attempts]

                total_router_latency = (time.perf_counter() - router_start) * 1000.0

                # Emit structured telemetry log
                metrics = AIRequestMetrics(
                    request_id=request_id,
                    operation=req.task_type.value,
                    provider=res.provider,
                    model=res.model,
                    latency_ms=round(total_router_latency, 2),
                    status="success",
                    token_usage=TokenUsage(
                        input_tokens=res.input_tokens,
                        output_tokens=res.output_tokens,
                        total_tokens=res.total_tokens,
                        usage_type=UsageType(res.token_usage_type) if res.token_usage_type in ["actual", "estimated", "unavailable"] else UsageType.UNAVAILABLE,
                    ),
                    estimated_cost=res.estimated_cost_usd,
                    fallback_used=is_fallback,
                    attempts=attempts,
                )
                telemetry.log_llm_event(metrics)

                return res

            except Exception as exc:
                att_latency = (time.perf_counter() - attempt_start) * 1000.0
                last_error = exc
                attempt_record = ProviderAttempt(
                    provider=provider_name.value,
                    model=chosen_model,
                    latency_ms=round(att_latency, 2),
                    status="error",
                    error_type=type(exc).__name__,
                )
                attempts.append(attempt_record)

                logger.warning(
                    f"[AI-Router] req_id={request_id} task={req.task_type.value} "
                    f"provider={provider_name.value} FAILED in {round(att_latency, 2)}ms ({type(exc).__name__}: {exc}). "
                    f"{'Switching to fallback...' if not is_fallback else 'All providers failed.'}"
                )

        # If all providers fail
        total_router_latency = (time.perf_counter() - router_start) * 1000.0
        failed_metrics = AIRequestMetrics(
            request_id=request_id,
            operation=req.task_type.value,
            provider="none",
            model="none",
            latency_ms=round(total_router_latency, 2),
            status="error",
            token_usage=TokenUsage(usage_type=UsageType.UNAVAILABLE),
            fallback_used=True,
            attempts=attempts,
            error_type=type(last_error).__name__ if last_error else "ProviderFailure",
        )
        telemetry.log_llm_event(failed_metrics)

        return AIResponse(
            success=False,
            content="",
            parsed_json=None,
            provider="none",
            model="none",
            latency_ms=round(total_router_latency, 2),
            fallback_used=True,
            error=str(last_error),
            request_id=request_id,
            attempts=[att.model_dump() for att in attempts],
        )


ai_router = AIProviderRouter()
