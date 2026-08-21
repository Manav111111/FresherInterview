import os
import io
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from fastapi import UploadFile, HTTPException, status
from app.config import settings

logger = logging.getLogger("fresherai.speech")

ALLOWED_MIME_TYPES = {
    "audio/webm", "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mp3", "audio/mpeg", "audio/ogg", "audio/mp4", "audio/m4a",
    "audio/x-m4a", "video/webm", "application/octet-stream"
}

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25MB


class BaseSpeechProvider(ABC):
    @abstractmethod
    async def transcribe(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        pass


class GroqWhisperProvider(BaseSpeechProvider):
    """Groq Whisper STT Provider using whisper-large-v3 for fast high-accuracy speech-to-text."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    async def transcribe(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        if not self.api_key or "placeholder" in self.api_key:
            raise ValueError("Groq API Key is not configured.")

        # Prepare multipart form upload
        files = {
            "file": (filename or "audio.webm", file_bytes, content_type or "audio/webm")
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "json",
            "language": "en",
            "temperature": "0.0",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.endpoint, files=files, data=data, headers=headers)
            resp.raise_for_status()
            res_data = resp.json()

        transcript = res_data.get("text", "").strip()
        return {
            "success": True,
            "transcript": transcript,
            "language": res_data.get("language", "en"),
            "duration_seconds": res_data.get("duration", None),
            "provider": "groq_whisper",
        }


class GeminiSpeechProvider(BaseSpeechProvider):
    """Gemini Multimodal Audio STT Provider using gemini-2.0-flash."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def transcribe(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        if not self.api_key or "placeholder" in self.api_key:
            raise ValueError("Gemini API Key is not configured.")

        import base64
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        mime = content_type if content_type in ALLOWED_MIME_TYPES else "audio/webm"

        url = f"{self.base_url}/gemini-2.0-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": b64_data,
                            }
                        },
                        {
                            "text": "Transcribe the spoken words in this audio exactly into plain English text. Return only the transcription without any preamble or quotes."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
            }
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            transcript = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            transcript = ""

        return {
            "success": True,
            "transcript": transcript,
            "language": "en",
            "duration_seconds": None,
            "provider": "gemini_flash",
        }


class SpeechService:
    """Central Speech-to-Text service with provider routing and fallback support."""

    def __init__(self):
        self.groq_whisper = GroqWhisperProvider()
        self.gemini_speech = GeminiSpeechProvider()

    async def transcribe_audio(self, file: UploadFile) -> Dict[str, Any]:
        # 1. Validate file size and MIME type
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file provided.",
            )

        if file_size > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio file exceeds maximum size limit of 25MB (received {file_size // (1024*1024)}MB).",
            )

        content_type = file.content_type or "audio/webm"
        filename = file.filename or "recording.webm"

        start_time = time.perf_counter()
        primary_provider = settings.SPEECH_PROVIDER or "groq_whisper"
        
        # Try primary provider (Groq Whisper)
        try:
            if primary_provider == "gemini":
                result = await self.gemini_speech.transcribe(file_bytes, filename, content_type)
            else:
                result = await self.groq_whisper.transcribe(file_bytes, filename, content_type)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(f"[Speech] Transcribed {file_size} bytes in {elapsed_ms:.1f}ms using {result.get('provider')}")
            return result
        except Exception as e:
            logger.warning(f"[Speech] Primary transcription ({primary_provider}) failed: {e}. Trying fallback provider...")

        # Fallback to alternative provider
        try:
            if primary_provider == "gemini":
                result = await self.groq_whisper.transcribe(file_bytes, filename, content_type)
            else:
                result = await self.gemini_speech.transcribe(file_bytes, filename, content_type)
            result["fallback_used"] = True
            return result
        except Exception as fallback_err:
            logger.warning(f"[Speech] Server speech providers notice ({fallback_err}), returning graceful fallback.")
            return {
                "success": False,
                "transcript": "",
                "message": "Server transcription unavailable, using browser speech recognition.",
                "provider": "client_fallback",
            }



speech_service = SpeechService()
