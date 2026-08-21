import json
import re
import time
import logging
from typing import Dict, Any, Optional, List
import httpx
from app.config import settings
from app.ai.schemas import AIResponse, AIProviderName

logger = logging.getLogger("fresherai.gemini")


def clean_gemini_json_text(text: str) -> str:
    """Extracts valid JSON payload from Gemini response text."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    return text


class GeminiProvider:
    """
    Google Gemini Multimodal AI Provider optimized for complex reasoning,
    deep ATS resume audits, multimodal document parsing, and final interview reports.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def is_healthy(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("placeholder") and len(self.api_key) > 10)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = True,
        images: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: float = 45.0,
    ) -> AIResponse:
        start_time = time.perf_counter()
        chosen_model = model or settings.GEMINI_FAST_MODEL or "gemini-2.0-flash"

        if not self.api_key or "placeholder" in self.api_key:
            raise ValueError("Gemini API Key is not configured.")

        url = f"{self.base_url}/{chosen_model}:generateContent?key={self.api_key}"

        parts = []
        if images:
            for img in images:
                parts.append({
                    "inline_data": {
                        "mime_type": img.get("mime_type", "image/png"),
                        "data": img.get("data", ""),
                    }
                })

        parts.append({"text": prompt})

        contents = [{"role": "user", "parts": parts}]

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as parse_err:
            raise ValueError(f"Invalid Gemini response structure: {data} ({parse_err})")

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        parsed = None
        if json_mode:
            cleaned = clean_gemini_json_text(raw_content)
            try:
                parsed = json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Gemini JSON parse notice ({e}), raw text was: {cleaned[:100]}...")
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
            provider=AIProviderName.GEMINI.value,
            model=chosen_model,
            latency_ms=round(latency_ms, 2),
        )
