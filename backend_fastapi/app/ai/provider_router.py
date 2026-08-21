import uuid
import logging
from typing import Optional, Dict, Any
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
        Executes an AI request with primary routing and automatic fallback.
        """
        request_id = str(uuid.uuid4())[:8]
        primary = self.select_primary_provider(req.task_type, req.preferred_provider)
        secondary = AIProviderName.GEMINI if primary == AIProviderName.GROQ else AIProviderName.GROQ

        providers_to_try = [primary, secondary]
        last_error = None

        for idx, provider_name in enumerate(providers_to_try):
            is_fallback = idx > 0
            try:
                if provider_name == AIProviderName.GROQ:
                    model = settings.GROQ_FAST_MODEL if req.task_type == TaskType.FAST_INTERVIEW_QUESTION else settings.GROQ_COMPLEX_MODEL
                    res = await self.groq.generate(
                        prompt=req.prompt,
                        system_prompt=req.system_prompt,
                        model=model,
                        temperature=req.temperature,
                        json_mode=req.json_mode,
                        timeout_seconds=req.timeout_seconds,
                    )
                else:
                    model = settings.GEMINI_COMPLEX_MODEL if req.task_type in [TaskType.FINAL_REPORT, TaskType.RESUME_ATS_ANALYSIS] else settings.GEMINI_FAST_MODEL
                    res = await self.gemini.generate(
                        prompt=req.prompt,
                        system_prompt=req.system_prompt,
                        model=model,
                        temperature=req.temperature,
                        json_mode=req.json_mode,
                        images=req.images,
                        timeout_seconds=req.timeout_seconds,
                    )

                res.fallback_used = is_fallback
                
                # Structured Observability Telemetry
                logger.info(
                    f"[AI-Router] req_id={request_id} task={req.task_type.value} "
                    f"provider={res.provider} model={res.model} latency={res.latency_ms}ms "
                    f"fallback={is_fallback} status=SUCCESS"
                )
                return res

            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"[AI-Router] req_id={request_id} task={req.task_type.value} "
                    f"provider={provider_name.value} FAILED ({exc}). "
                    f"{'Switching to fallback...' if not is_fallback else 'All providers failed.'}"
                )

        # If both providers fail, return a structured fallback response or raise
        logger.error(f"[AI-Router] req_id={request_id} task={req.task_type.value} FATAL: All providers failed. Last error: {last_error}")
        return AIResponse(
            success=False,
            content="",
            parsed_json=None,
            provider="none",
            model="none",
            latency_ms=0.0,
            fallback_used=True,
            error=str(last_error),
        )


ai_router = AIProviderRouter()
