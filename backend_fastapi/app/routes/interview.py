import json
import uuid
import time
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
        "readiness": row.get("readiness") or row.get("readiness_label") or ("Strong / Nearly Ready" if row.get("overall_score", 0) >= 75 else "Developing / Needs Practice"),
        "readinessDescription": row.get("readiness_description", ""),
        "questionsCount": row.get("questions_count", len(row.get("questions", []))),
        "correctCount": row.get("correct_count", 0),
        "partialCount": row.get("partial_count", 0),
        "incorrectCount": row.get("incorrect_count", 0),
        "insufficientCount": row.get("insufficient_count", 0),
        "averageScore": row.get("average_score", row.get("overall_score", 0)),
        "categoryScores": row.get("category_scores", {}),
        "topicAccuracy": row.get("topic_accuracy", []),
        "topStrengths": row.get("top_strengths", row.get("strengths", [])),
        "priorityImprovements": row.get("priority_improvements", row.get("weaknesses", [])),
        "questionReviews": row.get("question_reviews", []),
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
    Initializes a new stateful mock interview session using LangGraph adaptive engine.
    Builds interview plan, extracts verified resume evidence, and returns Question 1.
    """
    user_id = current_user.get("userId") or current_user.get("id")

    if not body.type or not body.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview type and role are required",
        )

    # 1. Run LangGraph to build plan and select Question 1
    try:
        result = await interview_graph.ainvoke({
            "action": "start",
            "type": body.type.lower(),
            "role": body.role,
            "useResume": body.useResume,
            "resume": body.resume or {},
        })
        first_q = result.get("current_question")
    except Exception as e:
        logger.error(f"Failed to initialize adaptive interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize interview: {str(e)}",
        )

    if not first_q:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview question",
        )

    # Formatted initial question object with canonical tracking
    from app.utils.interview_dedup import normalize_question_fingerprint
    q1_fp = first_q.get("normalized_fingerprint") or normalize_question_fingerprint(first_q.get("question", ""))

    q1 = {
        "question_id": first_q.get("question_id", "q_001"),
        "question": first_q.get("question", ""),
        "difficulty": first_q.get("difficulty", "medium"),
        "timer": first_q.get("timer", 90),
        "topic": first_q.get("topic", "Core Fundamentals"),
        "source": first_q.get("source", "standard"),
        "is_follow_up": False,
        "resume_reference": first_q.get("resume_reference"),
        "related_question_ids": first_q.get("related_question_ids", []),
        "normalized_fingerprint": q1_fp,
        "userAnswer": "",
        "feedback": {},
    }

    interview_id = str(uuid.uuid4())
    db_payload = {
        "id": interview_id,
        "user_id": user_id,
        "type": body.type.lower(),
        "role": body.role,
        "use_resume": body.useResume,
        "questions": [q1],
        "current_question": 0,
        "status": "in-progress",
        "overall_score": 0,
        "primary_question_count": result.get("primary_question_count", 1),
        "target_primary_questions": 6,
        "followup_count": 0,
        "max_followups_total": 2,
        "followups_for_current_question": 0,
        "question_ids_asked": result.get("question_ids_asked", [q1["question_id"]]),
        "question_fingerprints_asked": result.get("question_fingerprints_asked", [q1_fp] if q1_fp else []),
        "concepts_covered": result.get("concepts_covered", []),
        "verified_resume_projects": result.get("verified_resume_projects", []),
        "verified_resume_skills": result.get("verified_resume_skills", []),
        "skill_gaps": result.get("skill_gaps", []),
        "answers": [],
        "evaluations": [],
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "summary": "",
    }

    # 2. Insert into Supabase with local fallback
    supabase = get_supabase()
    db_start = time.perf_counter()
    try:
        supabase.table("interviews").insert(db_payload).execute()
        db_latency = (time.perf_counter() - db_start) * 1000.0
        from app.core.telemetry import telemetry
        telemetry.log_db_event("insert", "interviews", db_latency, status="success")
    except Exception as db_err:
        db_latency = (time.perf_counter() - db_start) * 1000.0
        from app.core.telemetry import telemetry
        telemetry.log_db_event("insert", "interviews", db_latency, status="fallback")
        logger.warning(f"Supabase interview creation failed ({db_err}). Storing in local fallback.")
        _mock_interviews_db[interview_id] = db_payload

    # 3. Cache session in Redis
    try:
        await set_cache(f"interview:session:{interview_id}", db_payload, ttl=24 * 3600)
        await delete_cache(f"interviews:{user_id}")
    except Exception:
        pass

    return {
        "success": True,
        "interviewId": interview_id,
        "currentQuestion": 0,
        "totalQuestions": 6,
        "question": q1,
    }


@interview_router.post("/answer")
async def submit_answer(
    body: SubmitAnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submits candidate's answer to current question, evaluates with partial credit,
    decides next action, and returns Question N+1 (or completed final report).
    """
    user_id = current_user.get("userId") or current_user.get("id")

    if not body.interviewId or not body.answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview Id and Answer are required",
        )

    # 1. Fetch interview from Redis, Supabase, or memory store
    interview = None
    try:
        cached_sess = await get_cache(f"interview:session:{body.interviewId}")
        if cached_sess:
            interview = json.loads(cached_sess) if isinstance(cached_sess, str) else cached_sess
    except Exception:
        pass

    if not interview:
        supabase = get_supabase()
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

    # 2. Get current question & idempotency guard
    curr_idx = interview.get("current_question", 0)
    questions = list(interview.get("questions", []))

    if curr_idx >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index",
        )

    current_q = questions[curr_idx]

    # Idempotency check: if current question already evaluated with this exact answer and next question exists
    if current_q.get("userAnswer") == body.answer and current_q.get("feedback") and curr_idx + 1 < len(questions):
        logger.info(f"Duplicate submission detected for interview {body.interviewId} question {curr_idx}; returning existing next question.")
        next_existing_q = questions[curr_idx + 1]
        return {
            "success": True,
            "completed": False,
            "currentQuestion": curr_idx + 1,
            "question": next_existing_q,
            "feedback": current_q.get("feedback", {}),
            "isFollowUp": next_existing_q.get("is_follow_up", False),
            "questionSource": next_existing_q.get("source", "standard"),
        }

    current_q["userAnswer"] = body.answer

    # 3. Reconstruct complete canonical exclusion history (works across restarts and restored sessions)
    from app.utils.interview_dedup import extract_session_excluded_history
    session_history = extract_session_excluded_history(interview)

    # 4. Invoke LangGraph Adaptive Feedback & Decision
    try:
        result = await interview_graph.ainvoke({
            "action": "feedback",
            "role": interview.get("role", "Software Engineer"),
            "type": interview.get("type", "technical"),
            "current_question": current_q,
            "answer": body.answer,
            "primary_question_count": interview.get("primary_question_count", 1),
            "target_primary_questions": interview.get("target_primary_questions", 6),
            "followup_count": interview.get("followup_count", 0),
            "max_followups_total": interview.get("max_followups_total", 2),
            "followups_for_current_question": interview.get("followups_for_current_question", 0),
            "question_ids_asked": list(session_history["excluded_ids"]),
            "question_fingerprints_asked": list(session_history["asked_fingerprints"]),
            "concepts_covered": interview.get("concepts_covered", []),
            "verified_resume_projects": interview.get("verified_resume_projects", []),
            "verified_resume_skills": interview.get("verified_resume_skills", []),
            "skill_gaps": interview.get("skill_gaps", []),
            "questions": questions,
            "answers": interview.get("answers", []),
            "evaluations": interview.get("evaluations", []),
        })
    except Exception as e:
        logger.error(f"LangGraph adaptive evaluation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )

    feedback_data = result.get("feedback", {})
    completed = result.get("completed", False)

    # Update current question with evaluation
    current_q["feedback"] = feedback_data
    current_q["score"] = feedback_data.get("score", 70)
    questions[curr_idx] = current_q

    # 4. Handle Completion
    if completed:
        report = result.get("report", {})
        interview["status"] = "completed"
        interview["overall_score"] = report.get("overallScore", feedback_data.get("score", 75))
        interview["readiness"] = report.get("readiness", "Strong / Nearly Ready")
        interview["readiness_description"] = report.get("readinessDescription", "")
        interview["questions_count"] = report.get("questionsCount", len(questions))
        interview["correct_count"] = report.get("correctCount", 0)
        interview["partial_count"] = report.get("partialCount", 0)
        interview["incorrect_count"] = report.get("incorrectCount", 0)
        interview["insufficient_count"] = report.get("insufficientCount", 0)
        interview["average_score"] = report.get("averageScore", interview["overall_score"])
        interview["category_scores"] = report.get("categoryScores", {})
        interview["topic_accuracy"] = report.get("topicAccuracy", [])
        interview["top_strengths"] = report.get("topStrengths", report.get("strengths", []))
        interview["priority_improvements"] = report.get("priorityImprovements", report.get("weaknesses", []))
        interview["question_reviews"] = report.get("questionReviews", [])
        interview["summary"] = report.get("summary", "")
        interview["strengths"] = report.get("topStrengths", report.get("strengths", []))
        interview["weaknesses"] = report.get("priorityImprovements", report.get("weaknesses", []))
        interview["recommendations"] = report.get("recommendations", [])

    else:
        # Continue interview: append next question
        next_q = result.get("current_question")
        questions = result.get("questions", questions)
        interview["current_question"] = curr_idx + 1
        interview["primary_question_count"] = result.get("primary_question_count", interview.get("primary_question_count", 1))
        interview["followup_count"] = result.get("followup_count", 0)
        interview["followups_for_current_question"] = result.get("followups_for_current_question", 0)
        interview["question_ids_asked"] = result.get("question_ids_asked", list(session_history["excluded_ids"]))
        interview["question_fingerprints_asked"] = result.get("question_fingerprints_asked", list(session_history["asked_fingerprints"]))
        interview["concepts_covered"] = result.get("concepts_covered", [])
        interview["answers"] = result.get("answers", [])
        interview["evaluations"] = result.get("evaluations", [])

    interview["questions"] = questions

    # 5. Persist to Supabase and cache in Redis
    update_payload = {
        "questions": questions,
        "current_question": interview["current_question"],
        "status": interview["status"],
        "overall_score": interview.get("overall_score", 0),
        "readiness": interview.get("readiness", ""),
        "readiness_description": interview.get("readiness_description", ""),
        "questions_count": interview.get("questions_count", len(questions)),
        "correct_count": interview.get("correct_count", 0),
        "partial_count": interview.get("partial_count", 0),
        "incorrect_count": interview.get("incorrect_count", 0),
        "insufficient_count": interview.get("insufficient_count", 0),
        "average_score": interview.get("average_score", 0),
        "category_scores": interview.get("category_scores", {}),
        "topic_accuracy": interview.get("topic_accuracy", []),
        "top_strengths": interview.get("top_strengths", []),
        "priority_improvements": interview.get("priority_improvements", []),
        "question_reviews": interview.get("question_reviews", []),
        "summary": interview.get("summary", ""),
        "strengths": interview.get("strengths", []),
        "weaknesses": interview.get("weaknesses", []),
        "recommendations": interview.get("recommendations", []),
    }

    try:
        supabase = get_supabase()
        supabase.table("interviews").update(update_payload).eq("id", body.interviewId).execute()
    except Exception as e:
        logger.warning(f"Supabase update failed: {e}")
        _mock_interviews_db[body.interviewId] = interview

    try:
        await set_cache(f"interview:session:{body.interviewId}", interview, ttl=24 * 3600)
        await delete_cache(f"interviews:{user_id}")
    except Exception:
        pass

    mapped_interview = _map_interview_from_db(interview)

    if completed:
        return {
            "success": True,
            "completed": True,
            "interview": mapped_interview,
            "feedback": feedback_data,
        }

    next_question_to_return = questions[interview["current_question"]]
    return {
        "success": True,
        "completed": False,
        "currentQuestion": interview["current_question"],
        "question": next_question_to_return,
        "feedback": feedback_data,
        "isFollowUp": next_question_to_return.get("is_follow_up", False),
        "questionSource": next_question_to_return.get("source", "standard"),
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
    await set_cache(cache_key, json.dumps(interviews_list), ttl=60 * 60)

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
