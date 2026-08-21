import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://fresherai-silk.vercel.app"

    # Supabase configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379"

    # AI / LLM configuration - Groq
    GROQ_API_KEY: str = ""
    GROQ_FAST_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_COMPLEX_MODEL: str = "openai/gpt-oss-120b"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.2

    # AI / LLM configuration - Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_FAST_MODEL: str = "gemini-2.0-flash"
    GEMINI_COMPLEX_MODEL: str = "gemini-2.5-pro"

    # Speech-to-text Configuration
    SPEECH_PROVIDER: str = "groq_whisper"  # groq_whisper | gemini | fallback

    # Firebase Admin Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "app/config/serviceAccountKey.json"

    # Razorpay configuration
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
