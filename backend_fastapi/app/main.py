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

# Configure CORS for Frontend (Vercel & Vite localhost)
cors_origins = list(set(settings.cors_origin_list + [
    "https://fresherai-silk.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
from app.routes.resume import resume_router
from app.routes.interview import interview_router
from app.routes.roadmap import roadmap_router
from app.routes.billing import billing_router
from app.routes.video_solution import video_solution_router
from app.routes.audio import audio_router

# Include routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api")
app.include_router(resume_router, prefix="/api/resume")
app.include_router(interview_router, prefix="/api/interview")
app.include_router(roadmap_router, prefix="/api/roadmap")
app.include_router(billing_router, prefix="/api/billing")
app.include_router(video_solution_router, prefix="/api/video")
app.include_router(audio_router)


