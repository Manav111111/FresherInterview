import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.redis import get_redis, close_redis
from app.core.db import get_supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fresherai.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    logger.info("Starting FresherAI FastAPI backend...")
    # Initialize Redis connection test
    redis_client = await get_redis()
    if redis_client:
        logger.info("Redis ready.")
    else:
        logger.warning("Redis is not connected. Some caching features may degrade.")

    # Initialize Supabase client
    supabase = get_supabase()
    if supabase:
        logger.info("Supabase client initialized.")

    yield

    logger.info("Shutting down FresherAI FastAPI backend...")
    await close_redis()


app = FastAPI(
    title="FresherAI API",
    description="High-performance AI backend for Resume ATS Scoring, Mock Interviews, and Career Roadmaps",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for Frontend (Vite on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "success": True,
        "message": "FresherAI Backend API is Running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    redis_client = await get_redis()
    redis_status = "connected" if redis_client else "disconnected"

    return {
        "status": "healthy",
        "database": "supabase",
        "cache": redis_status,
        "llm_model": settings.LLM_MODEL,
    }


from app.routes.auth import auth_router, user_router

# Include routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api")
