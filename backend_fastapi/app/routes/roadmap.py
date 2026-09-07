import json
import uuid
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.roadmap import GenerateRoadmapRequest, RoadmapResponse
from app.agents.roadmap_agent import generate_roadmap
from app.core.security import get_current_user
from app.core.db import get_supabase
from app.core.redis import get_cache, set_cache, delete_cache

logger = logging.getLogger("fresherai.roadmap")

roadmap_router = APIRouter(tags=["Roadmap"])

from pydantic import BaseModel, Field

# In-memory store for development fallback
_mock_roadmaps_db: Dict[str, Dict[str, Any]] = {}


class SkillGapPayload(BaseModel):
    role: str = Field(..., description="Target role name")
    skills: List[str] = Field(default_factory=list, description="Candidate skills list")


def _map_roadmap_from_db(row: Dict[str, Any]) -> Dict[str, Any]:
    """Maps database row (snake_case) to frontend expected format (both Section 10 and camelCase)."""
    tools = row.get("tools") or row.get("essential_tools") or row.get("essentialTools") or []
    yt_resources = row.get("youtube_resources") or row.get("youtube_playlists") or row.get("youtubePlaylists") or []
    docs = row.get("official_docs") or row.get("learning_resources") or row.get("learningResources") or []
    career_res = row.get("career_resources") or row.get("careerResources") or []
    projects = row.get("projects") or row.get("portfolio_projects") or row.get("portfolioProjects") or []
    skills = row.get("skills") or row.get("skill_gap_summary") or {"strong": [], "partial": [], "missing": [], "priority": []}

    return {
        # Section 10 Schema
        "role": row.get("role") or row.get("title", "Career Roadmap"),
        "target_salary": row.get("target_salary") or row.get("target_package") or "15 LPA",
        "summary": row.get("summary") or {
            "difficulty": row.get("level", "Intermediate"),
            "duration_weeks": len(row.get("modules", [])) or 12,
            "personalized": bool(row.get("personalized", False)),
        },
        "skills": skills,
        "tools": tools,
        "youtube_resources": yt_resources,
        "official_docs": docs,
        "career_resources": career_res,
        "projects": projects,
        "modules": row.get("modules", []),

        # Backward compatibility fields
        "_id": str(row.get("id")),
        "id": str(row.get("id")),
        "userId": str(row.get("user_id")),
        "title": row.get("title", ""),
        "targetPackage": row.get("target_package") or row.get("target_salary", ""),
        "package": row.get("target_package") or row.get("target_salary", ""),
        "duration": row.get("duration", f"{len(row.get('modules', []))} Weeks"),
        "level": row.get("level", "Intermediate"),
        "syllabus": row.get("syllabus", []),
        "essentialTools": tools,
        "youtubePlaylists": yt_resources,
        "learningResources": docs,
        "careerResources": career_res,
        "portfolioProjects": projects,
        "skillGapSummary": row.get("skill_gap_summary") or row.get("skillGapSummary"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
    }


@roadmap_router.post("/skill-gap")
async def calculate_skill_gap_endpoint(
    body: SkillGapPayload,
    current_user: dict = Depends(get_current_user),
):
    """Calculates skill gap for candidate skills against canonical target role."""
    from app.services.skill_gap_engine import skill_gap_engine
    result = skill_gap_engine.calculate_skill_gap(body.role, body.skills)
    return {
        "success": True,
        "data": result,
    }


@roadmap_router.post("/generate", status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    body: GenerateRoadmapRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generates a personalized career roadmap using AI based on target role,
    target package, and optional candidate resume data.
    """
    user_id = current_user.get("userId") or current_user.get("id")

    if not body.role or not body.targetPackage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role and Target Package are required.",
        )

    if body.useResume and not body.resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume data is required when useResume is true.",
        )

    try:
        # 1. Run AI Roadmap Generator
        result = await generate_roadmap(
            role=body.role,
            target_package=body.targetPackage,
            use_resume=body.useResume,
            resume=body.resume,
        )

        roadmap_id = str(uuid.uuid4())
        db_payload = {
            "id": roadmap_id,
            "user_id": user_id,
            "role": result.get("role", body.role),
            "target_salary": result.get("target_salary", body.targetPackage),
            "title": result.get("title", f"{body.role} Career Roadmap"),
            "target_package": result.get("targetPackage", body.targetPackage),
            "duration": result.get("duration", "12 Weeks"),
            "level": result.get("level", "Intermediate"),
            "summary": result.get("summary", {}),
            "skills": result.get("skills", {}),
            "tools": result.get("tools", []),
            "youtube_resources": result.get("youtube_resources", []),
            "official_docs": result.get("official_docs", []),
            "career_resources": result.get("career_resources", []),
            "projects": result.get("projects", []),
            "syllabus": result.get("syllabus", []),
            "essential_tools": result.get("tools", []),
            "modules": result.get("modules", []),
            "youtube_playlists": result.get("youtube_resources", []),
            "learning_resources": result.get("official_docs", []),
            "portfolio_projects": result.get("projects", []),
            "skill_gap_summary": result.get("skillGapSummary", {}),
            "personalized": result.get("summary", {}).get("personalized", False),
        }

        # 2. Insert into Supabase
        supabase = get_supabase()
        try:
            supabase.table("roadmaps").insert(db_payload).execute()
        except Exception as db_err:
            logger.warning(f"Supabase roadmap insert failed ({db_err}). Saving to local store.")
            _mock_roadmaps_db[roadmap_id] = db_payload

        mapped_roadmap = _map_roadmap_from_db(db_payload)

        # 3. Cache single roadmap and clear user history cache
        await set_cache(f"roadmap:{roadmap_id}", json.dumps(mapped_roadmap), ex=60 * 60)

        await delete_cache(f"userRoadmaps:{user_id}")

        return {
            "success": True,
            "message": "Roadmap generated successfully.",
            "data": mapped_roadmap,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating roadmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap: {str(e)}",
        )


@roadmap_router.get("")
@roadmap_router.get("/all")
async def get_all_roadmaps(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves all generated roadmaps for the current user."""
    user_id = current_user.get("userId") or current_user.get("id")
    cache_key = f"userRoadmaps:{user_id}"

    # 1. Check Redis Cache
    cached = await get_cache(cache_key)
    if cached:
        try:
            return {
                "success": True,
                "data": json.loads(cached),
            }
        except Exception:
            pass

    # 2. Query Supabase
    supabase = get_supabase()
    roadmaps_list = []

    try:
        res = (
            supabase.table("roadmaps")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if res.data:
            roadmaps_list = [_map_roadmap_from_db(row) for row in res.data]
    except Exception as e:
        logger.warning(f"Supabase query for roadmaps failed: {e}")

    # Fallback to local memory store
    if not roadmaps_list:
        roadmaps_list = [
            _map_roadmap_from_db(item)
            for item in _mock_roadmaps_db.values()
            if str(item.get("user_id")) == str(user_id)
        ]

    # Update cache
    await set_cache(cache_key, json.dumps(roadmaps_list), ex=60 * 60)

    return {
        "success": True,
        "data": roadmaps_list,
    }


@roadmap_router.get("/{roadmap_id}")
async def get_roadmap_by_id(
    roadmap_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieves a single roadmap by ID."""
    user_id = current_user.get("userId") or current_user.get("id")

    # 1. Check cache
    cached = await get_cache(f"roadmap:{roadmap_id}")
    if cached:
        try:
            return {
                "success": True,
                "fromCache": True,
                "data": json.loads(cached),
            }
        except Exception:
            pass

    # 2. Query Supabase
    supabase = get_supabase()
    roadmap = None

    try:
        res = (
            supabase.table("roadmaps")
            .select("*")
            .eq("id", roadmap_id)
            .eq("user_id", user_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            roadmap = _map_roadmap_from_db(res.data[0])
    except Exception as e:
        logger.warning(f"Supabase query failed: {e}")

    if not roadmap:
        local_raw = _mock_roadmaps_db.get(roadmap_id)
        if local_raw and str(local_raw.get("user_id")) == str(user_id):
            roadmap = _map_roadmap_from_db(local_raw)

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Cache single roadmap
    await set_cache(f"roadmap:{roadmap_id}", json.dumps(roadmap), ex=60 * 60)

    return {
        "success": True,
        "fromCache": False,
        "data": roadmap,
    }
