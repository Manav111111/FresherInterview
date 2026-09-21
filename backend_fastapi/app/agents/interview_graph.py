"""
Fresher.AI — Production Adaptive Mock Interview Brain
Stateful, Resume-Aware, RAG-Grounded LangGraph Engine.
Implements:
- 6 Primary Questions + Max 2 Adaptive Follow-ups (Max 8 total turns)
- Qdrant 760-Question RAG Grounding + Resilient In-Memory Fallback
- Strict Resume Evidence Anti-Hallucination
- Partial Credit Evaluation & Kind 'I Don't Know' Handling
- Question Deduplication & Dynamic Difficulty Progression
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, TypedDict
from collections import Counter

try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

from app.ai.provider_router import ai_router
from app.ai.schemas import (
    TaskType,
    AIRequest,
    AnswerEvaluationSchema,
    NextActionDecision,
    TechnicalRubric,
    HRRubric,
    QuestionReviewItem,
    TopicAccuracyItem,
    StandardizedInterviewReport,
)
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("fresherai.interview_graph")


# ==========================================
# 1. STRONGLY TYPED INTERVIEW STATE
# ==========================================

class AdaptiveInterviewState(TypedDict, total=False):
    # Lifecycle & Action
    action: str  # 'start', 'answer', 'feedback', 'summary'
    session_id: str
    user_id: str
    completed: bool

    # Candidate Profile & Target
    role: str
    type: str  # 'technical' or 'hr'
    candidate_level: str  # 'fresher', 'junior', 'mid'
    target_difficulty: str  # 'easy', 'medium', 'hard'

    # Verified Resume Evidence
    useResume: bool
    resume: Dict[str, Any]
    verified_resume_projects: List[Dict[str, Any]]
    verified_resume_skills: List[str]
    verified_resume_claims: List[str]
    skill_gaps: List[str]

    # Interview Strategy & Progress Counters
    interview_plan: Dict[str, Any]
    target_primary_questions: int  # Default 6
    primary_question_count: int    # Strictly 0..6
    max_followups_total: int       # Default 2
    followup_count: int            # Strictly 0..2
    max_followups_per_question: int  # Default 1
    followups_for_current_question: int  # Strictly 0..1

    # Question Tracking & Deduplication
    current_question: Dict[str, Any]
    current_question_id: str
    question_ids_asked: List[str]
    concepts_covered: List[str]
    asked_domains: List[str]
    asked_subcategories: List[str]
    recent_question_embeddings: List[List[float]]

    # Answers & Evaluations History
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    last_evaluation: Dict[str, Any]
    next_action: Dict[str, Any]
    report: Dict[str, Any]


# ==========================================
# 2. RESUME VERIFICATION HELPERS (ANTI-HALLUCINATION)
# ==========================================

def extract_verified_resume_evidence(resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts strictly verified resume evidence without hallucinations.
    Only items explicitly declared in projects, skills, and experience are accepted.
    """
    if not resume or not isinstance(resume, dict):
        return {"projects": [], "skills": [], "claims": []}

    # Verified skills
    raw_skills = resume.get("skills", [])
    if isinstance(raw_skills, list):
        verified_skills = [str(s).strip() for s in raw_skills if str(s).strip()]
    elif isinstance(raw_skills, str):
        verified_skills = [s.strip() for s in re.split(r"[,;\n]", raw_skills) if s.strip()]
    else:
        verified_skills = []

    # Verified projects
    raw_projects = resume.get("projects", [])
    verified_projects = []
    if isinstance(raw_projects, list):
        for p in raw_projects:
            if isinstance(p, dict):
                p_name = p.get("name") or p.get("title") or "Project"
                p_tech = p.get("technologies") or p.get("tech_stack") or p.get("tools") or []
                if isinstance(p_tech, str):
                    p_tech = [t.strip() for t in re.split(r"[,;\n]", p_tech) if t.strip()]
                p_desc = p.get("description") or p.get("summary") or ""
                verified_projects.append({
                    "name": str(p_name).strip(),
                    "technologies": p_tech if isinstance(p_tech, list) else [],
                    "description": str(p_desc).strip()[:200],
                })
            elif isinstance(p, str) and p.strip():
                verified_projects.append({
                    "name": p.strip(),
                    "technologies": [],
                    "description": "",
                })

    # Verified claims / summary
    summary = resume.get("summary") or resume.get("objective") or ""
    verified_claims = [summary.strip()] if summary.strip() else []

    return {
        "projects": verified_projects,
        "skills": verified_skills,
        "claims": verified_claims,
    }


def identify_candidate_skill_gaps(role: str, candidate_skills: List[str]) -> List[str]:
    """Identifies priority technical skill gaps by comparing candidate skills against role."""
    r_lower = role.lower()
    c_skills_lower = [s.lower() for s in candidate_skills]

    # Core expectations by domain
    role_benchmarks = {
        "ai": ["rag", "langgraph", "embeddings", "qdrant", "vector_search", "prompt_caching", "llm_evaluation"],
        "backend": ["fastapi", "redis", "postgresql", "indexing", "concurrency", "docker", "caching"],
        "frontend": ["react", "fiber", "state_management", "performance", "typescript", "core_web_vitals"],
        "devops": ["kubernetes", "docker", "terraform", "ci_cd", "observability", "linux"],
        "data": ["sql", "window_functions", "indexing", "query_optimization", "transactions"],
        "ml": ["data_leakage", "feature_engineering", "model_drift", "evaluation_metrics", "cross_validation"],
        "system": ["load_balancing", "caching", "sharding", "eventual_consistency", "rate_limiting"],
    }

    gaps = []
    for key, benchmarks in role_benchmarks.items():
        if key in r_lower:
            for b in benchmarks:
                if not any(b in s for s in c_skills_lower):
                    gaps.append(b)

    # General software engineer fallback
    if not gaps:
        for b in ["system_design", "testing", "caching", "database_indexing"]:
            if not any(b in s for s in c_skills_lower):
                gaps.append(b)

    return gaps[:5]


# ==========================================
# 3. DETERMINISTIC REPORT & READINESS HELPERS
# ==========================================

DIFFICULTY_WEIGHTS = {
    "easy": 0.8,
    "medium": 1.0,
    "hard": 1.2,
}


def classify_score_result(score: int, answer_text: str = "") -> str:
    ans_clean = (answer_text or "").strip().lower()
    if len(ans_clean.split()) < 3 or any(phrase in ans_clean for phrase in ["don't know", "dont know", "no idea", "skip", "idk", "haven't learned"]):
        return "insufficient"
    if score >= 75:
        return "correct"
    if score >= 50:
        return "partially_correct"
    return "incorrect"


def get_readiness_classification(overall_score: int) -> tuple:
    if overall_score >= 90:
        return "Excellent / Interview Ready", "Demonstrated exceptional domain mastery, architectural depth, and crisp communication."
    elif overall_score >= 75:
        return "Strong / Nearly Ready", "Solid conceptual and practical foundation. Ready for mid-level technical rounds with minor refinement."
    elif overall_score >= 60:
        return "Developing / Needs Practice", "Demonstrated foundational knowledge but requires focused practice in depth, trade-offs, and system resilience."
    elif overall_score >= 40:
        return "Significant Improvement Needed", "Partial conceptual awareness. Requires targeted revision on system mechanics and structured answering."
    else:
        return "Fundamentals Need Attention", "Early career stage. Recommend systematic drills on core domain fundamentals before retrying."


def calculate_deterministic_report(
    role: str,
    interview_type: str,
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculates ground-truth mathematical scores across questions and topics."""
    is_technical = interview_type.lower() != "hr"

    scores_list = []
    correct_count = 0
    partial_count = 0
    incorrect_count = 0
    insufficient_count = 0

    topic_tracker = {}
    tech_categories = {
        "Technical Correctness": [],
        "Completeness & Edge Cases": [],
        "Reasoning & Trade-offs": [],
        "Communication & Clarity": [],
        "Relevance & Conciseness": [],
    }
    hr_categories = {
        "Relevance to Question": [],
        "Communication & Clarity": [],
        "Answer Structure (STAR)": [],
        "Specific Examples": [],
        "Professional Confidence": [],
    }

    all_strengths = []
    all_missing = []
    question_reviews = []

    diff_weights = DIFFICULTY_WEIGHTS
    total_weighted_score = 0.0
    total_weight = 0.0

    for idx, q in enumerate(questions):
        fb = q.get("feedback", {})
        score = fb.get("score") if fb.get("score") is not None else q.get("score", 70)
        score = max(0, min(100, int(score)))
        scores_list.append(score)

        difficulty = str(q.get("difficulty", "medium")).lower()
        weight = diff_weights.get(difficulty, 1.0)
        total_weighted_score += (score * weight)
        total_weight += weight

        u_ans = str(q.get("userAnswer", "")).strip()
        result = fb.get("result") or classify_score_result(score, u_ans)

        if result == "correct":
            correct_count += 1
        elif result == "partially_correct":
            partial_count += 1
        elif result == "incorrect":
            incorrect_count += 1
        else:
            insufficient_count += 1

        topic = q.get("topic") or q.get("subcategory") or "General"
        q_text = q.get("question", f"Question {idx+1}")

        # Category scoring
        if is_technical:
            rubric = fb.get("technical_rubric") or {}
            c_score = rubric.get("correctness") if rubric.get("correctness") is not None else fb.get("correctness", score * 0.40)
            comp_score = rubric.get("completeness") if rubric.get("completeness") is not None else fb.get("detail", score * 0.20)
            reas_score = rubric.get("reasoning") if rubric.get("reasoning") is not None else fb.get("problemSolving", score * 0.15)
            comm_score = rubric.get("communication") if rubric.get("communication") is not None else fb.get("communication", score * 0.15)
            rel_score = rubric.get("relevance") if rubric.get("relevance") is not None else fb.get("relevance", score * 0.10)

            tech_categories["Technical Correctness"].append(min(100, round((c_score / 40.0) * 100 if c_score <= 40 else c_score)))
            tech_categories["Completeness & Edge Cases"].append(min(100, round((comp_score / 20.0) * 100 if comp_score <= 20 else comp_score)))
            tech_categories["Reasoning & Trade-offs"].append(min(100, round((reas_score / 15.0) * 100 if reas_score <= 15 else reas_score)))
            tech_categories["Communication & Clarity"].append(min(100, round((comm_score / 15.0) * 100 if comm_score <= 15 else comm_score)))
            tech_categories["Relevance & Conciseness"].append(min(100, round((rel_score / 10.0) * 100 if rel_score <= 10 else rel_score)))
        else:
            rubric = fb.get("hr_rubric") or {}
            rel_score = rubric.get("relevance") if rubric.get("relevance") is not None else fb.get("relevance", score * 0.25)
            comm_score = rubric.get("communication") if rubric.get("communication") is not None else fb.get("communication", score * 0.25)
            struct_score = rubric.get("structure") if rubric.get("structure") is not None else fb.get("clarity", score * 0.20)
            ex_score = rubric.get("examples") if rubric.get("examples") is not None else fb.get("detail", score * 0.15)
            conf_score = rubric.get("confidence") if rubric.get("confidence") is not None else fb.get("efficiency", score * 0.15)

            hr_categories["Relevance to Question"].append(min(100, round((rel_score / 25.0) * 100 if rel_score <= 25 else rel_score)))
            hr_categories["Communication & Clarity"].append(min(100, round((comm_score / 25.0) * 100 if comm_score <= 25 else comm_score)))
            hr_categories["Answer Structure (STAR)"].append(min(100, round((struct_score / 20.0) * 100 if struct_score <= 20 else struct_score)))
            hr_categories["Specific Examples"].append(min(100, round((ex_score / 15.0) * 100 if ex_score <= 15 else ex_score)))
            hr_categories["Professional Confidence"].append(min(100, round((conf_score / 15.0) * 100 if conf_score <= 15 else conf_score)))

        if topic not in topic_tracker:
            topic_tracker[topic] = {"total_score": 0, "count": 0, "correct": 0}
        topic_tracker[topic]["total_score"] += score
        topic_tracker[topic]["count"] += 1
        if result == "correct":
            topic_tracker[topic]["correct"] += 1

        q_strengths = fb.get("strengths") or fb.get("correct_points") or fb.get("keyPointsCovered") or []
        q_missing = fb.get("missing_points") or fb.get("keyPointsMissed") or []
        all_strengths.extend(q_strengths)
        all_missing.extend(q_missing)

        question_reviews.append({
            "questionIndex": idx + 1,
            "question": q_text,
            "userAnswer": u_ans or "No answer submitted.",
            "difficulty": difficulty.capitalize(),
            "topic": topic,
            "score": score,
            "result": result,
            "strengths": q_strengths,
            "missingPoints": q_missing,
            "incorrectPoints": fb.get("incorrect_points", []),
            "whatYouShouldUnderstand": fb.get("what_you_should_understand"),
            "approachGuidance": fb.get("approach_guidance") or fb.get("improvements") or [],
            "idealAnswer": fb.get("ideal_answer_summary") or fb.get("idealAnswer") or "",
            "source": q.get("source", "standard"),
            "resumeReference": q.get("resume_reference"),
        })

    overall_score = round(total_weighted_score / total_weight) if total_weight > 0 else 75
    overall_score = max(0, min(100, overall_score))
    avg_score = round(sum(scores_list) / len(scores_list)) if scores_list else overall_score
    readiness_lbl, readiness_desc = get_readiness_classification(overall_score)

    target_categories = tech_categories if is_technical else hr_categories
    aggregated_category_scores = {}
    for cat_name, val_list in target_categories.items():
        aggregated_category_scores[cat_name] = round(sum(val_list) / len(val_list)) if val_list else overall_score

    # Backward compatibility aliases for category score keys
    if is_technical:
        if "Completeness & Edge Cases" in aggregated_category_scores:
            aggregated_category_scores["Completeness"] = aggregated_category_scores["Completeness & Edge Cases"]
        if "Reasoning & Trade-offs" in aggregated_category_scores:
            aggregated_category_scores["Problem Solving"] = aggregated_category_scores["Reasoning & Trade-offs"]
        if "Communication & Clarity" in aggregated_category_scores:
            aggregated_category_scores["Communication"] = aggregated_category_scores["Communication & Clarity"]
        if "Relevance & Conciseness" in aggregated_category_scores:
            aggregated_category_scores["Relevance"] = aggregated_category_scores["Relevance & Conciseness"]

    topic_accuracy_list = []
    for top_name, t_data in topic_tracker.items():
        top_avg = round(t_data["total_score"] / t_data["count"]) if t_data["count"] > 0 else overall_score
        topic_accuracy_list.append({
            "topic": top_name,
            "score": top_avg,
            "questionsCount": t_data["count"],
            "correctCount": t_data["correct"],
        })

    return {
        "overallScore": overall_score,
        "readiness": readiness_lbl,
        "readinessDescription": readiness_desc,
        "questionsCount": len(questions),
        "correctCount": correct_count,
        "partialCount": partial_count,
        "incorrectCount": incorrect_count,
        "insufficientCount": insufficient_count,
        "averageScore": avg_score,
        "categoryScores": aggregated_category_scores,
        "topicAccuracy": topic_accuracy_list,
        "topStrengths": list(dict.fromkeys(all_strengths))[:5],
        "priorityImprovements": list(dict.fromkeys(all_missing))[:5],
        "questionReviews": question_reviews,
    }


# ==========================================
# 4. LANGGRAPH NODES
# ==========================================

async def build_interview_plan_node(state: AdaptiveInterviewState) -> Dict[str, Any]:
    """
    Builds a personalized, resume-grounded interview strategy.
    Extracts strictly verified resume evidence (no hallucinations) and selects Question 1.
    """
    role = state.get("role", "Software Engineer")
    itype = state.get("type", "technical")
    use_resume = state.get("useResume", False)
    resume = state.get("resume", {})

    evidence = extract_verified_resume_evidence(resume) if use_resume else {"projects": [], "skills": [], "claims": []}
    skill_gaps = identify_candidate_skill_gaps(role, evidence["skills"])

    plan = {
        "target_primary_questions": 6,
        "max_followups": 2,
        "strategic_weights": {
            "core_technical": 2,
            "resume_or_skill_gap": 2,
            "scenario_or_design": 1,
            "adaptive_slot": 1,
        },
        "verified_projects": [p["name"] for p in evidence["projects"]],
        "skill_gaps": skill_gaps,
    }

    initial_state_update = {
        "verified_resume_projects": evidence["projects"],
        "verified_resume_skills": evidence["skills"],
        "verified_resume_claims": evidence["claims"],
        "skill_gaps": skill_gaps,
        "interview_plan": plan,
        "target_primary_questions": 6,
        "primary_question_count": 0,
        "max_followups_total": 2,
        "followup_count": 0,
        "max_followups_per_question": 1,
        "followups_for_current_question": 0,
        "question_ids_asked": [],
        "concepts_covered": [],
        "asked_domains": [],
        "asked_subcategories": [],
        "questions": [],
        "answers": [],
        "evaluations": [],
    }

    # Select Question 1: If resume projects exist, start with verified project deep-dive or foundational role question
    next_q = await select_next_question(
        role=role,
        interview_type=itype,
        verified_projects=evidence["projects"],
        verified_skills=evidence["skills"],
        skill_gaps=skill_gaps,
        target_difficulty=state.get("target_difficulty", "medium"),
        question_action="resume_deep_dive" if evidence["projects"] else "technical_question",
        excluded_ids=[],
        excluded_concepts=[],
    )

    initial_state_update["current_question"] = next_q
    initial_state_update["current_question_id"] = next_q.get("question_id", "q_001")
    initial_state_update["primary_question_count"] = 1
    initial_state_update["question_ids_asked"] = [next_q.get("question_id", "q_001")]
    if next_q.get("key_concepts"):
        initial_state_update["concepts_covered"] = list(next_q.get("key_concepts"))
    initial_state_update["questions"] = [next_q]

    return initial_state_update


async def select_next_question(
    role: str,
    interview_type: str,
    verified_projects: List[Dict[str, Any]],
    verified_skills: List[str],
    skill_gaps: List[str],
    target_difficulty: str,
    question_action: str,
    excluded_ids: List[str],
    excluded_concepts: List[str],
    last_evaluation: Optional[Dict[str, Any]] = None,
    current_primary_q: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Selects or generates the next question:
    - RAG Core Technical (from 760-question pool)
    - Resume Deep-Dive (strictly verified evidence only, zero fabrication)
    - Adaptive Follow-up (targeting specific missing concepts)
    - Scenario / System Design
    """
    is_hr = interview_type.lower() == "hr"

    # ── 1. Adaptive Follow-Up Question ──
    if question_action == "follow_up" and last_evaluation and current_primary_q:
        missing = last_evaluation.get("missing_points", [])
        demonstrated = last_evaluation.get("correct_points", [])
        missing_focus = missing[0] if missing else "underlying trade-offs and mechanics"
        pri_q_text = current_primary_q.get("question", "")

        prompt = f"""
Candidate was asked: "{pri_q_text}"
Candidate demonstrated: {', '.join(demonstrated[:3]) if demonstrated else 'high-level understanding'}
Candidate missed: {missing_focus}

TASK: Generate a targeted, conversational follow-up question (1-2 sentences) asking the candidate to explain {missing_focus}.
Do NOT repeat the original question. Directly probe the missing concept.
Return JSON: {{"question": "...", "timer": 90}}
"""
        try:
            ai_res = await ai_router.execute(AIRequest(
                task_type=TaskType.REAL_TIME_FOLLOWUP,
                prompt=prompt,
                system_prompt="You are a professional hiring bar-raiser asking a constructive follow-up question.",
                json_mode=True,
                temperature=0.2,
            ))
            if ai_res.success and ai_res.parsed_json:
                q_text = ai_res.parsed_json.get("question")
                if q_text:
                    return {
                        "question_id": f"{current_primary_q.get('question_id', 'q')}_followup",
                        "question": q_text,
                        "difficulty": current_primary_q.get("difficulty", "medium"),
                        "timer": 90,
                        "topic": current_primary_q.get("topic", "Follow-up"),
                        "source": "follow_up",
                        "is_follow_up": True,
                        "parent_question_id": current_primary_q.get("question_id"),
                        "follow_up_reason": last_evaluation.get("follow_up_reason", f"Probe {missing_focus}"),
                        "key_concepts": [missing_focus],
                    }
        except Exception as e:
            logger.warning(f"Follow-up synthesis notice: {e}")

        # Fallback follow-up
        return {
            "question_id": f"{current_primary_q.get('question_id', 'q')}_followup",
            "question": f"You mentioned {demonstrated[0] if demonstrated else 'the core approach'}. Could you elaborate specifically on how you would handle {missing_focus}?",
            "difficulty": current_primary_q.get("difficulty", "medium"),
            "timer": 90,
            "topic": current_primary_q.get("topic", "Follow-up"),
            "source": "follow_up",
            "is_follow_up": True,
            "parent_question_id": current_primary_q.get("question_id"),
        }

    # ── 2. Resume Deep-Dive Question (Strictly Verified Evidence) ──
    if question_action == "resume_deep_dive" and verified_projects:
        # Pick the project with the most tech details
        proj = verified_projects[0]
        p_name = proj.get("name", "your project")
        p_tech = ", ".join(proj.get("technologies", [])) or "the stack you used"

        prompt = f"""
Candidate's Verified Resume Project:
- Project Name: {p_name}
- Verified Tech Stack: {p_tech}
- Description: {proj.get('description', '')}
- Target Role: {role}

CRITICAL RULE: You MUST NOT invent any unlisted technologies, metrics, or responsibilities. Only use what is listed above.
TASK: Formulate a realistic, deep-dive interview question asking the candidate to walk through an architectural decision or technical trade-off in {p_name}.
Return JSON: {{"question": "...", "topic": "{p_name} Architecture", "timer": 120}}
"""
        try:
            ai_res = await ai_router.execute(AIRequest(
                task_type=TaskType.FAST_INTERVIEW_QUESTION,
                prompt=prompt,
                system_prompt="You are an engineering interviewer conducting a deep dive on a candidate's verified project.",
                json_mode=True,
                temperature=0.2,
            ))
            if ai_res.success and ai_res.parsed_json:
                q_text = ai_res.parsed_json.get("question")
                if q_text:
                    return {
                        "question_id": f"resume_{re.sub(r'[^a-zA-Z0-9]', '_', p_name.lower())[:15]}",
                        "question": q_text,
                        "difficulty": target_difficulty,
                        "timer": 120,
                        "topic": f"{p_name} Deep-Dive",
                        "source": "resume_deep_dive",
                        "resume_reference": p_name,
                        "is_follow_up": False,
                        "key_concepts": proj.get("technologies", [])[:3],
                    }
        except Exception as e:
            logger.warning(f"Resume question synthesis notice: {e}")

        # Safe fallback
        return {
            "question_id": f"resume_{re.sub(r'[^a-zA-Z0-9]', '_', p_name.lower())[:15]}",
            "question": f"In your project '{p_name}', walk me through the overall technical architecture. What major engineering trade-offs did you consider?",
            "difficulty": target_difficulty,
            "timer": 120,
            "topic": f"{p_name} Architecture",
            "source": "resume_deep_dive",
            "resume_reference": p_name,
            "is_follow_up": False,
            "key_concepts": proj.get("technologies", []),
        }

    # ── 3. RAG Grounded Core Technical / HR Question ──
    domain_filter = "Behavioral/HR" if is_hr else None
    qtype_filter = "scenario" if question_action == "scenario_question" else None

    candidates = await retrieval_service.search_interview_topics(
        role=role,
        skill_gaps=skill_gaps,
        domain=domain_filter,
        difficulty=target_difficulty,
        question_type=qtype_filter,
        excluded_question_ids=excluded_ids,
        excluded_recent_concepts=excluded_concepts,
        top_k=8,
    )

    if candidates:
        chosen = candidates[0]
        return {
            "question_id": chosen.get("question_id"),
            "question": chosen.get("question"),
            "difficulty": chosen.get("difficulty", target_difficulty),
            "timer": 90 if chosen.get("difficulty") == "easy" else 120,
            "topic": chosen.get("subcategory") or chosen.get("domain", "Technical"),
            "source": "rag_grounded",
            "is_follow_up": False,
            "domain": chosen.get("domain"),
            "subcategory": chosen.get("subcategory"),
            "key_concepts": chosen.get("key_concepts", []),
            "ideal_answer": chosen.get("ideal_answer", ""),
            "key_concepts_to_look_for": chosen.get("key_concepts_to_look_for", ""),
            "strong_answer_indicators": chosen.get("strong_answer_indicators", []),
            "partial_answer_indicators": chosen.get("partial_answer_indicators", []),
            "weak_answer_indicators": chosen.get("weak_answer_indicators", []),
            "common_mistakes": chosen.get("common_mistakes", []),
            "evaluation_rubric": chosen.get("evaluation_rubric", {}),
            "follow_up_topics": chosen.get("follow_up_topics", []),
        }

    # Guaranteed fallback
    fallback_q = f"Explain the core architectural concepts and best practices required when designing scalable solutions for a {role}." if not is_hr else f"Tell me about a challenging technical or team obstacle you faced, and how you navigated it."
    return {
        "question_id": "fallback_core_001",
        "question": fallback_q,
        "difficulty": target_difficulty,
        "timer": 90,
        "topic": "Core Fundamentals",
        "source": "standard",
        "is_follow_up": False,
    }


async def evaluate_answer_node(state: AdaptiveInterviewState) -> Dict[str, Any]:
    """
    Evaluates candidate's answer with mandatory partial credit, concept recognition,
    and respectful handling of 'I don't know' responses.
    """
    curr_q = state.get("current_question", {})
    q_text = curr_q.get("question", "")
    ans_text = str(state.get("answer", "")).strip()
    ans_lower = ans_text.lower()
    difficulty = curr_q.get("difficulty", "medium")
    itype = state.get("type", "technical")
    is_technical = itype.lower() != "hr"

    # ── Detect "I Don't Know" / Not Sure ──
    ans_words = ans_text.split()
    word_count = len(ans_words)
    idk_phrases = ["don't know", "dont know", "no idea", "not sure", "haven't learned", "skip", "idk", "no answer", "pass"]
    has_idk = any(p in ans_lower for p in idk_phrases)

    # Genuine 'I don't know' refusal/unfamiliarity:
    # 1. Very short (< 4 words)
    # 2. Or short (< 14 words) with clear IDK phrase and no technical explanation
    # 3. Or begins directly with "i don't know" / "i have no idea" and is under 12 words
    has_tech_substance = any(kw in ans_lower for kw in ["streaming", "cache", "caching", "database", "vector", "index", "concurrency", "queue", "architecture", "latency", "tokens", "rag", "embeddings"])
    is_idontknow = (
        word_count < 4
        or (word_count < 14 and has_idk and not has_tech_substance)
        or (word_count < 12 and any(ans_lower.startswith(p) for p in ["i don't know", "i dont know", "no idea", "i'm not sure", "im not sure", "i have no idea", "haven't learned"]))
    )

    if is_idontknow:
        feedback = {
            "score": 30,
            "overall_score": 30,
            "result": "insufficient",
            "technical_rubric": {"correctness": 12, "completeness": 6, "reasoning": 5, "communication": 4, "relevance": 3},
            "hr_rubric": {"relevance": 8, "communication": 8, "structure": 5, "examples": 5, "confidence": 4},
            "correct_points": [],
            "partial_points": [],
            "missing_points": ["Candidate indicated unfamiliarity with this specific topic."],
            "incorrect_points": [],
            "concepts_demonstrated": [],
            "strengths": ["Clear and honest communication regarding unfamiliarity."],
            "what_you_should_understand": f"For '{q_text}', review foundational concepts in {curr_q.get('topic', 'this area')} and practice breaking down technical mechanics.",
            "ideal_answer_summary": curr_q.get("ideal_answer") or "A strong answer clearly defines the underlying principles, discusses trade-offs, and provides concrete real-world context.",
            "approach_guidance": ["1. State what you do know about related components.", "2. Reason from first principles.", "3. Be upfront if you haven't worked with it directly."],
            "feedback": "That's okay — let's move on to another area.",
            "improvements": ["Review foundational definitions and practice reasoning aloud even when uncertain."],
            "follow_up_recommended": False,
            "follow_up_reason": "Candidate explicitly indicated unfamiliarity.",
            "is_idontknow": True,
        }
        return {"last_evaluation": feedback}

    # ── Standardized Partial Credit Evaluation ──
    ideal_ans = curr_q.get("ideal_answer", "")
    key_concepts = ", ".join(curr_q.get("key_concepts", []))
    mistakes = ", ".join(curr_q.get("common_mistakes", []))

    eval_prompt = f"""
You are an Elite Principal Bar-Raiser evaluating a candidate's answer with MANDATORY PARTIAL CREDIT.

QUESTION: {q_text}
TOPIC: {curr_q.get('topic', 'General')}
DIFFICULTY: {difficulty}
CANDIDATE ANSWER: {ans_text}

GROUND-TRUTH BENCHMARK:
Ideal Concept Focus: {ideal_ans or 'Accurate mechanics, architectural trade-offs, scalability considerations.'}
Expected Key Concepts: {key_concepts or 'Foundational terminology and system workflow.'}
Common Mistakes to Watch For: {mistakes or 'Confusing terms, superficial definitions.'}

EVALUATION RULES:
1. PARTIAL CREDIT IS MANDATORY:
   - If candidate demonstrated valid concepts (e.g. latency, caching, embeddings, cost), YOU MUST explicitly list them under "correct_points" and acknowledge them in "strengths".
   - Do NOT mark an answer wrong merely because it lacks 100% completeness.
   - Distinguish WHAT IS CORRECT from WHAT IS MISSING from WHAT IS FACTUALLY WRONG.
2. SCORING SCALE (0-100):
   - 80-100 (correct): Strong conceptual grasp, articulates mechanics and trade-offs.
   - 50-79 (partially_correct): Valid technical concepts demonstrated, but omissions or missing depth.
   - 25-49 (incorrect): Serious misconceptions or off-topic.
   - 0-24 (insufficient): Empty or gibberish.
3. FOLLOW-UP RECOMMENDATION:
   - If score is 50-79 (partially correct) and a specific concept is missing, set "follow_up_recommended": true and provide "follow_up_reason" explaining what concept to probe.
   - If score >= 80 or < 45, set "follow_up_recommended": false.

Return valid JSON:
{{
  "overall_score": 75,
  "result": "partially_correct",
  "correct_points": ["Specific concepts candidate got right"],
  "partial_points": ["Points touched on but incomplete"],
  "missing_points": ["Key technical/architectural omissions"],
  "incorrect_points": ["Actual factual errors if any"],
  "concepts_demonstrated": ["List of proven concepts"],
  "strengths": ["What candidate did well with quotes/references"],
  "what_you_should_understand": "1-2 constructive sentences on correct technical mechanics",
  "ideal_answer_summary": "Concise high-caliber model answer",
  "approach_guidance": ["Step 1...", "Step 2..."],
  "feedback": "Balanced, encouraging feedback praising correct points first",
  "improvements": ["Concrete suggestions for improvement"],
  "follow_up_recommended": true,
  "follow_up_reason": "Candidate understands X but hasn't explained Y."
}}
"""

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FAST_EVALUATION,
            prompt=eval_prompt,
            system_prompt="You are an expert bar-raiser providing fair, encouraging, partial-credit evaluation.",
            json_mode=True,
            temperature=0.1,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            p = ai_res.parsed_json
            score = max(0, min(100, int(p.get("overall_score", 70))))
            res = p.get("result") or classify_score_result(score, ans_text)

            feedback = {
                "score": score,
                "overall_score": score,
                "result": res,
                "technical_rubric": {
                    "correctness": round(score * 0.40),
                    "completeness": round(score * 0.20),
                    "reasoning": round(score * 0.15),
                    "communication": round(score * 0.15),
                    "relevance": round(score * 0.10),
                } if is_technical else None,
                "hr_rubric": {
                    "relevance": round(score * 0.25),
                    "communication": round(score * 0.25),
                    "structure": round(score * 0.20),
                    "examples": round(score * 0.15),
                    "confidence": round(score * 0.15),
                } if not is_technical else None,
                "correct_points": p.get("correct_points", []),
                "partial_points": p.get("partial_points", []),
                "missing_points": p.get("missing_points", []),
                "incorrect_points": p.get("incorrect_points", []),
                "concepts_demonstrated": p.get("concepts_demonstrated", p.get("correct_points", [])),
                "strengths": p.get("strengths", p.get("correct_points", ["Addressed the core premises."])),
                "what_you_should_understand": p.get("what_you_should_understand"),
                "ideal_answer_summary": p.get("ideal_answer_summary", curr_q.get("ideal_answer", "")),
                "idealAnswer": p.get("ideal_answer_summary", curr_q.get("ideal_answer", "")),
                "approach_guidance": p.get("approach_guidance", []),
                "improvements": p.get("improvements", p.get("missing_points", [])),
                "feedback": str(p.get("feedback", "Answer evaluated.")),
                "follow_up_recommended": bool(p.get("follow_up_recommended", False)),
                "follow_up_reason": p.get("follow_up_reason"),
                "is_idontknow": False,
            }
            return {"last_evaluation": feedback}
    except Exception as e:
        logger.warning(f"Answer evaluation notice ({e}), applying heuristic fallback.")

    # Fallback heuristic
    tech_keywords = ["database", "cache", "redis", "scale", "api", "async", "index", "performance", "security", "token", "query", "vector", "rag", "embeddings", "latency"]
    matches = sum(1 for kw in tech_keywords if kw in ans_lower)
    word_count = len(ans_text.split())
    base_score = min(90, max(52, 60 + matches * 4 + min(12, word_count // 8)))

    res_cls = classify_score_result(base_score, ans_text)
    followup_rec = (res_cls == "partially_correct")

    return {
        "last_evaluation": {
            "score": base_score,
            "overall_score": base_score,
            "result": res_cls,
            "correct_points": [f"Addressed key concepts relevant to {curr_q.get('topic', 'the question')}"],
            "partial_points": [],
            "missing_points": ["Could expand on architectural trade-offs and edge cases."],
            "incorrect_points": [],
            "concepts_demonstrated": [kw for kw in tech_keywords if kw in ans_lower],
            "strengths": ["Demonstrated structured communication and relevant terminology."],
            "what_you_should_understand": "Connect foundational definitions directly with production scalability constraints.",
            "ideal_answer_summary": curr_q.get("ideal_answer") or "A strong answer details architectural workflow and trade-offs.",
            "approach_guidance": ["1. State definition.", "2. Detail mechanics.", "3. Discuss trade-offs."],
            "feedback": "Good fundamental understanding. Deepen the explanation of production edge cases.",
            "improvements": ["Include concrete performance and failure-recovery details."],
            "follow_up_recommended": followup_rec,
            "follow_up_reason": "Candidate gave a partial answer; probing edge-case considerations." if followup_rec else None,
            "is_idontknow": False,
        }
    }


async def decide_next_action_node(state: AdaptiveInterviewState) -> Dict[str, Any]:
    """
    Decides the next adaptive action in the interview state machine.
    Strictly enforces:
    - Target primary questions = 6
    - Max follow-ups total = 2
    - Max follow-ups per primary question = 1
    - Maximum total turns = 8
    """
    primary_count = state.get("primary_question_count", 0)
    target_primary = state.get("target_primary_questions", 6)
    followup_count = state.get("followup_count", 0)
    max_followups = state.get("max_followups_total", 2)
    followups_for_curr = state.get("followups_for_current_question", 0)

    last_eval = state.get("last_evaluation", {})
    score = last_eval.get("score", 70)
    is_idontknow = last_eval.get("is_idontknow", False)
    follow_up_rec = last_eval.get("follow_up_recommended", False)
    curr_q = state.get("current_question", {})
    curr_diff = curr_q.get("difficulty", "medium").lower()

    # ── 1. Termination Check ──
    # If we have reached 6 primary questions AND current question doesn't justify a follow-up
    # OR if we hit total question cap (8 turns)
    total_turns = len(state.get("questions", []))
    if total_turns >= 8 or (primary_count >= target_primary and not (follow_up_rec and followup_count < max_followups and followups_for_curr < 1)):
        return {
            "next_action": {
                "action": "finish",
                "reason": "Target primary question quota reached.",
            },
            "completed": True,
        }

    # ── 2. Handle 'I Don't Know' -> Switch Topic (Never Waste a Follow-Up) ──
    if is_idontknow:
        return {
            "next_action": {
                "action": "topic_switch",
                "reason": "Candidate indicated unfamiliarity. Pivoting to a different topic without penalty.",
                "target_difficulty": "medium",
            },
            "completed": False,
        }

    # ── 3. Adaptive Follow-Up (Conditional & Bounded) ──
    if (
        follow_up_rec
        and followup_count < max_followups
        and followups_for_curr < 1
        and not curr_q.get("is_follow_up", False)
    ):
        return {
            "next_action": {
                "action": "follow_up",
                "reason": last_eval.get("follow_up_reason", "Candidate gave a partial answer; probing missing concept."),
                "target_difficulty": curr_diff,
            },
            "completed": False,
        }

    # ── 4. Strategic Next Primary Question ──
    # Check what strategic slots have been filled
    verified_projects = state.get("verified_resume_projects", [])
    questions_asked = state.get("questions", [])
    resume_questions_asked = sum(1 for q in questions_asked if q.get("source") == "resume_deep_dive")

    # If score is very high (>= 80): Increase difficulty or introduce scenario
    if score >= 80:
        new_diff = "hard" if curr_diff != "hard" else "hard"
        if resume_questions_asked < 2 and verified_projects:
            action = "resume_deep_dive"
            reason = "High score; challenging verified resume project implementation."
        else:
            action = "scenario_question"
            reason = "High score; advancing to real-world scale or production failure scenario."
        return {
            "next_action": {
                "action": action,
                "reason": reason,
                "target_difficulty": new_diff,
            },
            "completed": False,
        }

    # If score is weak (< 45): Decrease difficulty or test foundational concept
    if score < 45:
        new_diff = "easy" if curr_diff != "easy" else "easy"
        return {
            "next_action": {
                "action": "technical_question",
                "reason": "Weak answer; pivoting to foundational concept at lower difficulty.",
                "target_difficulty": new_diff,
            },
            "completed": False,
        }

    # Normal progression: Alternate between Core Technical and Resume Deep-Dive
    if resume_questions_asked < 2 and verified_projects and primary_count in (2, 4):
        action = "resume_deep_dive"
        reason = "Engaging verified resume project."
    else:
        action = "technical_question"
        reason = "Covering core role competency."

    return {
        "next_action": {
            "action": action,
            "reason": reason,
            "target_difficulty": curr_diff,
        },
        "completed": False,
    }


async def generate_summary_node(state: AdaptiveInterviewState) -> Dict[str, Any]:
    """Generates deterministic mathematical report and enriches with executive summary."""
    role = state.get("role", "Software Engineer")
    itype = state.get("type", "technical")
    questions = state.get("questions", [])

    det_report = calculate_deterministic_report(role, itype, questions)

    # Enrich with learning recommendations from Fresher.AI KB
    recommendations = []
    for item in det_report.get("topicAccuracy", []):
        if item.get("score", 100) < 70:
            top_name = item.get("topic", "System Design")
            recommendations.append(f"Review the Fresher.AI Curated Roadmap for {top_name} to strengthen trade-off articulation.")

    if not recommendations:
        recommendations = [
            "Practice structuring complex architectural answers using trade-offs and edge-case mitigations.",
            "Incorporate quantifiable performance metrics and operational benchmarks into your explanations.",
            "Review caching invalidation strategies and database query profiling with EXPLAIN ANALYZE.",
            "Prepare detailed technical walkthroughs of your top projects using the STAR framework.",
            "Re-attempt mock interviews under timed conditions to build consistent confidence."
        ]

    ai_summary = f"The candidate completed the {role} interview with a verified score of {det_report['overallScore']}/100 ({det_report['readiness']}). {det_report['readinessDescription']}"

    # Feed to LLM for personalized synthesis
    prompt = f"""
Candidate: Role: {role} ({itype})
Overall Score: {det_report['overallScore']}/100 ({det_report['readiness']})
Correct: {det_report['correctCount']}, Partial: {det_report['partialCount']}, Insufficient: {det_report['insufficientCount']}
Top Strengths: {', '.join(det_report['topStrengths'])}
Priority Improvements: {', '.join(det_report['priorityImprovements'])}

TASK: Write a 100-130 word executive talent summary synthesizing candidate technical depth and hiring readiness.
Return JSON: {{"summary": "...", "recommendations": [...]}}
"""
    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FINAL_REPORT,
            prompt=prompt,
            system_prompt="You are an executive talent director writing an objective performance report.",
            json_mode=True,
            temperature=0.2,
        ))
        if ai_res.success and ai_res.parsed_json:
            s_text = ai_res.parsed_json.get("summary")
            if s_text:
                ai_summary = s_text
            recs = ai_res.parsed_json.get("recommendations")
            if recs and isinstance(recs, list) and len(recs) >= 3:
                recommendations = recs
    except Exception as e:
        logger.warning(f"Summary node AI notice: {e}")

    final_report = {
        **det_report,
        "summary": ai_summary,
        "recommendations": recommendations[:5],
        "hiringRecommendation": det_report["readiness"],
    }

    return {"report": final_report}


# ==========================================
# 5. STATEFUL GRAPH WORKFLOW & ADAPTER
# ==========================================

class AdaptiveInterviewGraph:
    """
    Production Adaptive Mock Interview Graph.
    Coordinates plan building, candidate selection, answer evaluation,
    next action decisions, and final summary generation.
    Supports both compiled LangGraph and robust fallback execution.
    """

    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        import time
        from app.core.telemetry import get_current_request_id
        g_start = time.perf_counter()
        req_id = get_current_request_id()

        action = state.get("action", "start")

        if action == "start":
            # Initializes session, extracts resume evidence, selects Question 1
            res = await build_interview_plan_node(state)
            res["request_id"] = req_id
            res["latency_ms"] = round((time.perf_counter() - g_start) * 1000.0, 2)
            return res

        elif action == "feedback" or action == "answer":
            # 1. Evaluate candidate's answer
            eval_res = await evaluate_answer_node(state)
            last_eval = eval_res.get("last_evaluation", {})

            # 2. Decide next action based on updated state
            eval_state = {**state, "last_evaluation": last_eval}
            decide_res = await decide_next_action_node(eval_state)
            next_act = decide_res.get("next_action", {})
            completed = decide_res.get("completed", False)

            # Update question counters
            curr_q = state.get("current_question", {})
            curr_q["userAnswer"] = state.get("answer", "")
            curr_q["feedback"] = last_eval
            curr_q["score"] = last_eval.get("score", 70)

            questions = list(state.get("questions", []))
            # update existing question at current index
            curr_idx = len(questions) - 1
            if curr_idx >= 0:
                questions[curr_idx] = curr_q

            answers = list(state.get("answers", []))
            answers.append({"question": curr_q.get("question"), "answer": state.get("answer")})

            evaluations = list(state.get("evaluations", []))
            evaluations.append(last_eval)

            pri_count = state.get("primary_question_count", 1)
            fu_count = state.get("followup_count", 0)
            fu_curr = state.get("followups_for_current_question", 0)

            excluded_ids = list(state.get("question_ids_asked", []))
            concepts_cov = list(state.get("concepts_covered", []))
            if curr_q.get("question_id"):
                excluded_ids.append(curr_q.get("question_id"))
            if curr_q.get("key_concepts"):
                concepts_cov.extend(curr_q.get("key_concepts"))

            # If interview is complete, trigger summary node
            if completed:
                sum_res = await generate_summary_node({
                    "role": state.get("role", "Software Engineer"),
                    "type": state.get("type", "technical"),
                    "questions": questions,
                })
                return {
                    "completed": True,
                    "feedback": last_eval,
                    "questions": questions,
                    "report": sum_res.get("report", {}),
                    "primary_question_count": pri_count,
                    "followup_count": fu_count,
                }

            # 3. Select / Generate Next Question
            act_type = next_act.get("action", "technical_question")
            is_fu = (act_type == "follow_up")
            if is_fu:
                fu_count += 1
                fu_curr += 1
            else:
                pri_count += 1
                fu_curr = 0

            next_q = await select_next_question(
                role=state.get("role", "Software Engineer"),
                interview_type=state.get("type", "technical"),
                verified_projects=state.get("verified_resume_projects", []),
                verified_skills=state.get("verified_resume_skills", []),
                skill_gaps=state.get("skill_gaps", []),
                target_difficulty=next_act.get("target_difficulty", "medium"),
                question_action=act_type,
                excluded_ids=excluded_ids,
                excluded_concepts=concepts_cov,
                last_evaluation=last_eval,
                current_primary_q=curr_q,
            )

            questions.append(next_q)
            if next_q.get("question_id"):
                excluded_ids.append(next_q.get("question_id"))

            return {
                "completed": False,
                "feedback": last_eval,
                "next_action": next_act,
                "current_question": next_q,
                "current_question_id": next_q.get("question_id"),
                "questions": questions,
                "primary_question_count": pri_count,
                "followup_count": fu_count,
                "followups_for_current_question": fu_curr,
                "question_ids_asked": excluded_ids,
                "concepts_covered": concepts_cov,
                "answers": answers,
                "evaluations": evaluations,
                "request_id": req_id,
                "latency_ms": round((time.perf_counter() - g_start) * 1000.0, 2),
            }

        elif action == "summary":
            res = await generate_summary_node(state)
            res["request_id"] = req_id
            res["latency_ms"] = round((time.perf_counter() - g_start) * 1000.0, 2)
            return res

        # Default fallback
        res = await build_interview_plan_node(state)
        res["request_id"] = req_id
        res["latency_ms"] = round((time.perf_counter() - g_start) * 1000.0, 2)
        return res

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safe synchronous compatibility wrapper for callers outside an active event loop.
        Uses asyncio.run() when no loop is running, or delegates safely if a loop is active.
        """
        import asyncio
        import concurrent.futures

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If called from within an active event loop, execute in a worker thread to prevent deadlock
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(self.ainvoke(state)))
                return future.result()
        else:
            return asyncio.run(self.ainvoke(state))


# Global singleton graph instance
interview_graph = AdaptiveInterviewGraph()
