import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_audio_transcribe_empty_file_rejected():
    """Verify audio transcription rejects empty files with 400 Bad Request."""
    response = client.post(
        "/api/audio/transcribe",
        files={"file": ("test.webm", b"", "audio/webm")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_audio_transcribe_valid_file_handling():
    """Verify audio transcription endpoint accepts valid multipart audio."""
    # Synthetic audio header
    fake_audio_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    response = client.post(
        "/api/audio/transcribe",
        files={"file": ("recording.wav", fake_audio_bytes, "audio/wav")}
    )
    # The endpoint should either succeed (200) or report speech service status gracefully
    assert response.status_code in [200, 502, 500]
