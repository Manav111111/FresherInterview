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

# In-memory store for development fallback
_mock_roadmaps_db: Dict[str, Dict[str, Any]] = {}


def _map_roadmap_from_db(row: Dict[str, Any]) -> Dict[str, Any]:
    """Maps database row (snake_case) to frontend expected format (camelCase)."""
    return {
        "_id": str(row.get("id")),
        "id": str(row.get("id")),
        "userId": str(row.get("user_id")),
        "title": row.get("title", ""),
        "targetPackage": row.get("target_package", ""),
        "duration": row.get("duration", ""),
        "level": row.get("level", "Intermediate"),
        "modules": row.get("modules", []),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
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
            "title": result.get("title", f"{body.role} Career Roadmap"),
            "target_package": result.get("targetPackage", body.targetPackage),
            "duration": result.get("duration", "12 Weeks"),
            "level": result.get("level", "Intermediate"),
            "modules": result.get("modules", []),
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
