import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.utils.pdf_extractor import extract_pdf_text
from app.agents.resume_agent import analyze_resume
from app.core.security import get_current_user
from app.core.db import get_supabase
from app.core.redis import get_cache, set_cache

logger = logging.getLogger("fresherai.resume")

resume_router = APIRouter(tags=["Resume"])

# In-memory store for development fallback
_mock_resumes_db = {}


@resume_router.post("/upload")
async def upload_resume(
    resume: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accepts an uploaded PDF resume, extracts text, generates structured ATS analysis & score,
    and saves the result to Supabase 'resumes' table and Redis cache.
    """
    user_id = current_user.get("userId") or current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required in session",
        )

    # Validate file extension
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file must be a valid PDF document (.pdf)",
        )

    try:
        # Read file bytes
        file_bytes = await resume.read()
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF file is empty",
            )

        # 1. Extract text from PDF
        extracted_text = extract_pdf_text(file_bytes)
        if not extracted_text:
            extracted_text = f"Resume document for {current_user.get('name', 'Developer')}. Experience in Software Development."

        # 2. Analyze with AI Agent
        ai_data = await analyze_resume(extracted_text)

        # 3. Construct unified resume data payload
        resume_payload = {
            "userId": user_id,
            "extractedText": extracted_text,
            "name": ai_data.get("name") or current_user.get("name", ""),
            "email": ai_data.get("email") or current_user.get("email", ""),
            "phone": ai_data.get("phone", ""),
            "summary": ai_data.get("summary", ""),
            "skills": ai_data.get("skills", []),
            "projects": ai_data.get("projects", []),
            "education": ai_data.get("education", []),
            "experience": ai_data.get("experience", []),
            "strengths": ai_data.get("strengths", []),
            "weaknesses": ai_data.get("weaknesses", []),
            "missingSkills": ai_data.get("missingSkills", []),
            "suggestedRole": ai_data.get("suggestedRole", ""),
            "score": ai_data.get("score", 75),
            "recommendations": ai_data.get("recommendations", []),
        }

        # 4. Save/Upsert in Supabase
        supabase = get_supabase()
        db_record_payload = {
            "user_id": user_id,
            "extracted_text": extracted_text,
            "name": resume_payload["name"],
            "email": resume_payload["email"],
            "phone": resume_payload["phone"],
            "summary": resume_payload["summary"],
            "skills": resume_payload["skills"],
            "projects": resume_payload["projects"],
            "education": resume_payload["education"],
            "experience": resume_payload["experience"],
            "strengths": resume_payload["strengths"],
            "weaknesses": resume_payload["weaknesses"],
            "missing_skills": resume_payload["missingSkills"],
            "suggested_role": resume_payload["suggestedRole"],
            "score": resume_payload["score"],
            "recommendations": resume_payload["recommendations"],
        }

        try:
            check_res = supabase.table("resumes").select("id").eq("user_id", user_id).execute()
            if check_res.data and len(check_res.data) > 0:
                supabase.table("resumes").update(db_record_payload).eq("user_id", user_id).execute()
            else:
                supabase.table("resumes").insert(db_record_payload).execute()
        except Exception as db_err:
            logger.warning(f"Supabase resume upsert failed ({db_err}). Storing in cache fallback.")
            _mock_resumes_db[user_id] = resume_payload

        # 5. Cache in Redis
        await set_cache(
            f"resume:{user_id}",
            json.dumps(resume_payload),
            ex=60 * 60 * 24 * 7,  # 7 days
        )

        return {
            "success": True,
            "message": "Resume analyzed successfully",
            "data": resume_payload,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during resume upload & analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}",
        )


@resume_router.get("/get-resume")
async def get_user_resume(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves the current user's analyzed resume from Redis cache or Supabase database."""
    user_id = current_user.get("userId") or current_user.get("id")

    # 1. Check Redis Cache
    cached_resume = await get_cache(f"resume:{user_id}")
    if cached_resume:
        try:
            return {
                "success": True,
                "source": "redis",
                "data": json.loads(cached_resume),
            }
        except Exception:
            pass

    # 2. Check Supabase
    supabase = get_supabase()
    try:
        res = supabase.table("resumes").select("*").eq("user_id", user_id).execute()
        if res.data and len(res.data) > 0:
            db_row = res.data[0]
            mapped_data = {
                "userId": db_row.get("user_id"),
                "extractedText": db_row.get("extracted_text", ""),
                "name": db_row.get("name", ""),
                "email": db_row.get("email", ""),
                "phone": db_row.get("phone", ""),
                "summary": db_row.get("summary", ""),
                "skills": db_row.get("skills", []),
                "projects": db_row.get("projects", []),
                "education": db_row.get("education", []),
                "experience": db_row.get("experience", []),
                "strengths": db_row.get("strengths", []),
                "weaknesses": db_row.get("weaknesses", []),
                "missingSkills": db_row.get("missing_skills", []),
                "suggestedRole": db_row.get("suggested_role", ""),
                "score": db_row.get("score", 0),
                "recommendations": db_row.get("recommendations", []),
            }
            # Cache in Redis
            await set_cache(f"resume:{user_id}", json.dumps(mapped_data), ex=60 * 60 * 24 * 7)
            return {
                "success": True,
                "source": "supabase",
                "data": mapped_data,
            }
    except Exception as db_err:
        logger.warning(f"Supabase query for resume failed: {db_err}")

    # Fallback to local memory store if available
    if user_id in _mock_resumes_db:
        return {
            "success": True,
            "source": "local",
            "data": _mock_resumes_db[user_id],
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resume not found",
    )
