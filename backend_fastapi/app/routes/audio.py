import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.speech_service import speech_service
from app.core.security import get_optional_user

logger = logging.getLogger("fresherai.audio_routes")

audio_router = APIRouter(prefix="/api/audio", tags=["Audio & Speech"])


@audio_router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user: dict = Depends(get_optional_user),
):
    """
    Server-side Speech-to-Text endpoint.
    Accepts multipart microphone audio recording (WebM/WAV/MP3/MP4)
    and returns high-accuracy transcription from Groq Whisper / Gemini.
    """
    try:
        result = await speech_service.transcribe_audio(file)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected audio transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio transcription failed: {str(e)}",
        )
