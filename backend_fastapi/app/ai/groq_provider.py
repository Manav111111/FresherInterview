import json
import re
import time
import logging
from typing import Dict, Any, Optional
import httpx
from app.config import settings
from app.ai.schemas import AIResponse, AIProviderName

logger = logging.getLogger("fresherai.groq")


def clean_json_text(text: str) -> str:
    """Strips markdown code blocks, backticks, and trailing artifacts from LLM JSON response."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    return text


class GroqProvider:
    """
    High-performance Groq AI Provider optimized for ultra-low latency inference,
    real-time question generation, and fast first-stage evaluations.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def is_healthy(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("placeholder") and "placeholder" not in self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = True,
        timeout_seconds: float = 30.0,
    ) -> AIResponse:
        start_time = time.perf_counter()
        chosen_model = model or settings.GROQ_FAST_MODEL or "llama-3.3-70b-versatile"

        if not self.api_key or "placeholder" in self.api_key:
            raise ValueError("Groq API Key is not configured or contains placeholder.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        raw_content = data["choices"][0]["message"]["content"]
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        parsed = None
        if json_mode:
            cleaned = clean_json_text(raw_content)
            try:
                parsed = json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Groq JSON parse notice ({e}), raw text was: {cleaned[:100]}...")
                # Attempt regex extract
                try:
                    obj_match = re.search(r"\{[\s\S]*\}", cleaned)
                    if obj_match:
                        parsed = json.loads(obj_match.group(0))
                except Exception:
                    pass

        return AIResponse(
            success=True,
            content=raw_content,
            parsed_json=parsed,
            provider=AIProviderName.GROQ.value,
            model=chosen_model,
            latency_ms=round(latency_ms, 2),
        )
