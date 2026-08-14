import json
import uuid
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.interview import (
    StartInterviewRequest,
    SubmitAnswerRequest,
    StartInterviewResponse,
    SubmitAnswerResponse,
)
from app.agents.interview_graph import interview_graph
from app.core.security import get_current_user
from app.core.db import get_supabase
from app.core.redis import get_cache, set_cache, delete_cache

logger = logging.getLogger("fresherai.interview")

interview_router = APIRouter(tags=["Interview"])

# In-memory interview storage for development fallback
_mock_interviews_db: Dict[str, Dict[str, Any]] = {}


def _map_interview_from_db(row: Dict[str, Any]) -> Dict[str, Any]:
    """Maps database column names (snake_case) to frontend expected names (camelCase)."""
    return {
        "_id": str(row.get("id")),
        "id": str(row.get("id")),
        "userId": str(row.get("user_id")),
        "type": row.get("type", "technical"),
        "role": row.get("role", ""),
        "useResume": row.get("use_resume", False),
        "currentQuestion": row.get("current_question", 0),
        "questions": row.get("questions", []),
        "overallScore": row.get("overall_score", 0),
        "strengths": row.get("strengths", []),
        "weaknesses": row.get("weaknesses", []),
        "recommendations": row.get("recommendations", []),
        "summary": row.get("summary", ""),
        "status": row.get("status", "in-progress"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
    }


@interview_router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_interview(
    body: StartInterviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Initializes a new mock interview session using LangGraph agent questions.
    Saves interview state in Supabase and returns the first question.
    """
    user_id = current_user.get("userId") or current_user.get("id")

    if not body.type or not body.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview type and role are required",
        )

    # 1. Run LangGraph to generate tailored questions
    try:
        result = await interview_graph.ainvoke({
            "action": "start",
            "type": body.type.lower(),
            "role": body.role,
            "useResume": body.useResume,
            "resume": body.resume or {},
        })
        questions = result.get("questions", [])
    except Exception as e:
        logger.error(f"Failed to generate questions with LangGraph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview questions: {str(e)}",
        )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview questions",
        )

    # Ensure default structure on questions
    formatted_questions = []
    for q in questions:
        formatted_questions.append({
            "question": q.get("question", ""),
            "difficulty": q.get("difficulty", "easy"),
            "timer": q.get("timer", 90),
            "userAnswer": "",
            "feedback": {},
        })

    interview_id = str(uuid.uuid4())
    db_payload = {
        "id": interview_id,
        "user_id": user_id,
        "type": body.type.lower(),
        "role": body.role,
        "use_resume": body.useResume,
        "questions": formatted_questions,
        "current_question": 0,
        "status": "in-progress",
        "overall_score": 0,
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "summary": "",
    }

    # 2. Insert into Supabase
    supabase = get_supabase()
    try:
        supabase.table("interviews").insert(db_payload).execute()
    except Exception as db_err:
        logger.warning(f"Supabase interview creation failed ({db_err}). Storing in local fallback.")
        _mock_interviews_db[interview_id] = db_payload

    # 3. Clear user interviews cache
    await delete_cache(f"interviews:{user_id}")

    return {
        "success": True,
        "interviewId": interview_id,
        "currentQuestion": 0,
        "totalQuestions": len(formatted_questions),
        "question": formatted_questions[0],
    }


@interview_router.post("/answer")
async def submit_answer(
    body: SubmitAnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submits the candidate's answer to the current question, evaluates answer via LangGraph feedback agent,
    and returns feedback along with the next question or final summary.
    """
    user_id = current_user.get("userId") or current_user.get("id")

    if not body.interviewId or not body.answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview Id and Answer are required",
        )

    # 1. Fetch interview from Supabase or memory store
    supabase = get_supabase()
    interview = None

    try:
        res = (
            supabase.table("interviews")
            .select("*")
            .eq("id", body.interviewId)
            .eq("user_id", user_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            interview = res.data[0]
    except Exception as e:
        logger.warning(f"Supabase query failed: {e}")

    if not interview:
        interview = _mock_interviews_db.get(body.interviewId)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    if interview.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview already completed",
        )

    # 2. Get current question
    curr_idx = interview.get("current_question", 0)
    questions = interview.get("questions", [])

    if curr_idx >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index",
        )

    current_q = questions[curr_idx]
    current_q["userAnswer"] = body.answer

    # 3. Check if this is the final question
    completed = (curr_idx + 1 >= len(questions))

    # 4. Invoke LangGraph Feedback & Summary nodes
    try:
        result = await interview_graph.ainvoke({
            "action": "feedback",
            "question": current_q.get("question", ""),
            "answer": body.answer,
            "difficulty": current_q.get("difficulty", "medium"),
            "completed": completed,
            "role": interview.get("role", ""),
            "type": interview.get("type", "technical"),
            "questions": questions,
        })
    except Exception as e:
        logger.error(f"LangGraph evaluation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )

    feedback_data = result.get("feedback", {})
    current_q["feedback"] = feedback_data
    interview["current_question"] = curr_idx + 1

    # 5. Handle completion
    if completed:
        report = result.get("report", {})
        interview["status"] = "completed"
        interview["overall_score"] = report.get("overallScore", feedback_data.get("score", 75))
        interview["summary"] = report.get("summary", "")
        interview["strengths"] = report.get("strengths", [])
        interview["weaknesses"] = report.get("weaknesses", [])
        interview["recommendations"] = report.get("recommendations", [])

    # 6. Save update to Supabase
    update_payload = {
        "questions": questions,
        "current_question": interview["current_question"],
        "status": interview["status"],
        "overall_score": interview.get("overall_score", 0),
        "summary": interview.get("summary", ""),
        "strengths": interview.get("strengths", []),
        "weaknesses": interview.get("weaknesses", []),
        "recommendations": interview.get("recommendations", []),
    }

    try:
        supabase.table("interviews").update(update_payload).eq("id", body.interviewId).execute()
    except Exception as e:
        logger.warning(f"Supabase update failed: {e}")
        _mock_interviews_db[body.interviewId] = interview

    await delete_cache(f"interviews:{user_id}")

    mapped_interview = _map_interview_from_db(interview)

    if completed:
        return {
            "success": True,
            "completed": True,
            "interview": mapped_interview,
        }

    next_question = questions[interview["current_question"]]
    return {
        "success": True,
        "completed": False,
        "currentQuestion": interview["current_question"],
        "question": next_question,
        "feedback": feedback_data,
    }


@interview_router.get("/all")
async def get_all_interviews(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves all past interview sessions for the current user."""
    user_id = current_user.get("userId") or current_user.get("id")
    cache_key = f"interviews:{user_id}"

    # 1. Check Redis
    cached = await get_cache(cache_key)
    if cached:
        try:
            return {
                "success": True,
                "interviews": json.loads(cached),
            }
        except Exception:
            pass

    # 2. Query Supabase
    supabase = get_supabase()
    interviews_list = []

    try:
        res = (
            supabase.table("interviews")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if res.data:
            interviews_list = [_map_interview_from_db(row) for row in res.data]
    except Exception as e:
        logger.warning(f"Supabase query for interviews failed: {e}")

    # Fallback to local memory store
    if not interviews_list:
        interviews_list = [
            _map_interview_from_db(item)
            for item in _mock_interviews_db.values()
            if str(item.get("user_id")) == str(user_id)
        ]

    # Cache in Redis
    await set_cache(cache_key, json.dumps(interviews_list), ex=60 * 60)

    return {
        "success": True,
        "interviews": interviews_list,
    }


@interview_router.get("/{interview_id}")
async def get_interview_by_id(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieves a single interview report by ID."""
    user_id = current_user.get("userId") or current_user.get("id")

    supabase = get_supabase()
    interview = None

    try:
        res = (
            supabase.table("interviews")
            .select("*")
            .eq("id", interview_id)
            .eq("user_id", user_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            interview = _map_interview_from_db(res.data[0])
    except Exception as e:
        logger.warning(f"Supabase query failed: {e}")

    if not interview:
        local_raw = _mock_interviews_db.get(interview_id)
        if local_raw and str(local_raw.get("user_id")) == str(user_id):
            interview = _map_interview_from_db(local_raw)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    return {
        "success": True,
        "interview": interview,
    }
