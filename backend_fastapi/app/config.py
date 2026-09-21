import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure .env in backend_fastapi or current directory is explicitly loaded and overrides stale system/process env vars
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)
else:
    load_dotenv(override=True)


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

    # Qdrant Vector DB configuration
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_KB_COLLECTION: str = "fresher_ai_knowledge"

    # Embedding configuration
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIMENSION: int = 768

    # RAG caching configuration
    RAG_CACHE_TTL: int = 1800  # 30 minutes

    # Reranking configuration
    RERANKING_ENABLED: bool = True
    RERANKER_PROVIDER: str = "lexical_cross_encoder"  # lexical_cross_encoder | cross_encoder | llm | none
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_N: int = 20
    RERANK_FINAL_K: int = 5

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

    # Support configuration (site-owner configurable)
    SUPPORT_EMAIL: str = "support@fresherai.com"
    SUPPORT_PHONE: str = ""  # Explicitly empty: phone support is not currently offered
    SUPPORT_URL: str = "https://fresherai-silk.vercel.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
