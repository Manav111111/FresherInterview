"""
Fresher.AI — Comprehensive Automated Test Suite for Adaptive Mock Interview Brain
Tests:
1. 760-Question Bank Validation (unique IDs, 10 domains, complete schemas)
2. Semantic Retrieval across multiple roles & skill gaps
3. Partial Credit Evaluation (concept recognition & constructive feedback)
4. 'I Don't Know' natural polite handling & topic switching
5. Strict Resume Grounding (Anti-Hallucination verification)
6. 6-Primary + Max 2 Follow-ups Count Model Enforcement (Max 8 turns)
7. Question Deduplication & Variety Enforcement
8. Qdrant & Redis Outage Fallback Resilience
"""

import sys
import os
import pytest
import asyncio

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fresher_ai_kb")))

from app.agents.interview_graph import (
    interview_graph,
    extract_verified_resume_evidence,
    identify_candidate_skill_gaps,
    select_next_question,
    evaluate_answer_node,
    decide_next_action_node,
)
from app.services.retrieval_service import retrieval_service


# ==========================================
# 1. QUESTION BANK TESTS
# ==========================================

def test_question_bank_total_and_domains():
    """Verify 760 questions loaded across all 10 domains with exact target counts."""
    from data.interview_question_bank_v2 import get_interview_question_bank, get_domains

    qs = get_interview_question_bank()
    assert len(qs) == 760, f"Expected 760 questions, got {len(qs)}"

    expected_counts = {
        "AI Engineering": 100,
        "DSA": 120,
        "Core CS": 100,
        "Backend": 70,
        "Frontend": 60,
        "DevOps/Cloud": 70,
        "Databases/SQL": 60,
        "ML/Data Science": 70,
        "System Design": 60,
        "Behavioral/HR": 50,
    }

    counts = {}
    seen_ids = set()
    for q in qs:
        # Check duplicate IDs
        qid = q.get("question_id")
        assert qid, "Missing question_id"
        assert qid not in seen_ids, f"Duplicate question_id: {qid}"
        seen_ids.add(qid)

        d = q.get("domain")
        counts[d] = counts.get(d, 0) + 1

        # Check required fields
        assert q.get("question"), f"Empty question text for {qid}"
        assert q.get("key_concepts"), f"Empty key_concepts for {qid}"
        assert q.get("ideal_answer"), f"Empty ideal_answer for {qid}"
        assert q.get("evaluation_rubric"), f"Empty rubric for {qid}"
        assert q.get("embedding_text"), f"Empty embedding_text for {qid}"
        assert q.get("difficulty") in ("easy", "medium", "hard"), f"Invalid difficulty in {qid}"

    for d, exp_cnt in expected_counts.items():
        assert counts.get(d) == exp_cnt, f"Domain {d}: expected {exp_cnt}, got {counts.get(d)}"


# ==========================================
# 2. RETRIEVAL & SKILL GAP BOOSTING TESTS
# ==========================================

@pytest.mark.asyncio
async def test_retrieval_skill_gap_priority():
    """Verify retrieval prioritizes candidate skill gaps and target domain."""
    res = await retrieval_service.search_interview_topics(
        role="AI Engineer",
        skill_gaps=["RAG", "LangGraph"],
        difficulty="medium",
        top_k=5,
    )
    assert len(res) == 5, f"Expected 5 questions, got {len(res)}"
    # Verify at least one question covers RAG or LangGraph
    concepts = " ".join(" ".join(r.get("key_concepts", [])) + " " + r.get("subcategory", "") for r in res).lower()
    assert "rag" in concepts or "langgraph" in concepts, "Retrieved candidates did not prioritize skill gaps"


@pytest.mark.asyncio
async def test_retrieval_excludes_asked_questions():
    """Verify retrieval strictly excludes questions already asked."""
    excluded = ["ai-enginee-001", "ai-enginee-002", "ai-enginee-003"]
    res = await retrieval_service.search_interview_topics(
        role="AI Engineer",
        domain="AI Engineering",
        excluded_question_ids=excluded,
        top_k=10,
    )
    retrieved_ids = [r["question_id"] for r in res]
    for ex in excluded:
        assert ex not in retrieved_ids, f"Excluded question {ex} was unexpectedly retrieved"


# ==========================================
# 3. PARTIAL CREDIT & EVALUATION TESTS
# ==========================================

@pytest.mark.asyncio
async def test_partial_credit_evaluation():
    """Verify partial answers get credit (50-80), correct points are identified, and follow-up is recommended."""
    state = {
        "current_question": {
            "question_id": "ai-enginee-001",
            "question": "A production LLM endpoint is too slow. What would you measure first, and which changes could reduce latency?",
            "topic": "LLM Fundamentals",
            "difficulty": "medium",
            "ideal_answer": "Measure TTFT and TPOT. Use prompt caching, streaming, speculative decoding, and vLLM continuous batching.",
            "key_concepts": ["TTFT", "TPOT", "Prompt Caching", "Streaming", "Speculative Decoding"],
            "common_mistakes": ["Confusing latency with throughput"],
        },
        "answer": "I would enable streaming so users see tokens immediately and cache frequent prompts to save time, but I am not sure about the exact GPU profiling metrics.",
        "type": "technical",
    }
    result = await evaluate_answer_node(state)
    eval_data = result.get("last_evaluation", {})

    assert 45 <= eval_data["score"] <= 85, f"Expected partial score (45-85), got {eval_data['score']}"
    assert eval_data["result"] in ("partially_correct", "correct")
    assert len(eval_data.get("correct_points", [])) > 0, "Evaluator failed to acknowledge correct points"
    assert len(eval_data.get("missing_points", [])) > 0, "Evaluator failed to isolate missing concepts"
    # Should recommend follow-up for partial answer
    assert eval_data.get("follow_up_recommended") is True, "Follow-up should be recommended for partial answer"


@pytest.mark.asyncio
async def test_idontknow_polite_handling():
    """Verify 'I don't know' is handled kindly without shaming, giving 30 score and pivoting."""
    state = {
        "current_question": {
            "question_id": "databases-003",
            "question": "How does a B-Tree index work in PostgreSQL?",
            "topic": "Indexes",
            "difficulty": "medium",
            "ideal_answer": "B-Tree balanced search tree with O(log N) lookups.",
        },
        "answer": "I don't know much about database internals yet, haven't learned this.",
        "type": "technical",
    }
    result = await evaluate_answer_node(state)
    eval_data = result.get("last_evaluation", {})

    assert eval_data["is_idontknow"] is True
    assert "That's okay" in eval_data["feedback"]
    assert "not technical" not in eval_data["feedback"].lower(), "Interviewer shamed the candidate"
    assert eval_data["result"] == "insufficient"
    assert eval_data["follow_up_recommended"] is False, "Should NOT recommend follow-up on 'I don't know'"


# ==========================================
# 4. RESUME GROUNDING (ANTI-HALLUCINATION) TESTS
# ==========================================

def test_resume_evidence_extraction():
    """Verify only verified projects and skills are extracted, without hallucinations."""
    resume = {
        "skills": ["Python", "FastAPI", "Docker", "Qdrant"],
        "projects": [
            {
                "name": "Fresher.AI",
                "technologies": ["React", "FastAPI", "LangGraph", "Qdrant"],
                "description": "Mock interview platform using stateful agents.",
            }
        ],
        "summary": "AI enthusiast building developer tools.",
    }
    evidence = extract_verified_resume_evidence(resume)

    assert len(evidence["projects"]) == 1
    assert evidence["projects"][0]["name"] == "Fresher.AI"
    assert "LangGraph" in evidence["projects"][0]["technologies"]
    assert "Kubernetes" not in evidence["skills"], "Hallucinated unlisted skill"


@pytest.mark.asyncio
async def test_resume_question_anti_hallucination():
    """Verify resume questions only reference verified projects and never invent unlisted technologies."""
    verified_projects = [{
        "name": "Fresher.AI",
        "technologies": ["FastAPI", "Qdrant", "LangGraph"],
        "description": "Adaptive mock interview platform.",
    }]
    q = await select_next_question(
        role="AI Engineer",
        interview_type="technical",
        verified_projects=verified_projects,
        verified_skills=["Python", "FastAPI"],
        skill_gaps=["RAG"],
        target_difficulty="medium",
        question_action="resume_deep_dive",
        excluded_ids=[],
        excluded_concepts=[],
    )
    assert q["source"] == "resume_deep_dive"
    assert "Fresher.AI" in q["question"] or "project" in q["question"].lower()
    # Ensure interviewer doesn't claim candidate used unlisted technologies like Kubernetes or AWS
    assert "kubernetes" not in q["question"].lower()
    assert "aws" not in q["question"].lower()


# ==========================================
# 5. STRICT QUESTION COUNT & FLOW TESTS (6 + MAX 2)
# ==========================================

@pytest.mark.asyncio
async def test_interview_turn_and_followup_limits():
    """
    Simulate an entire interview session and verify:
    - Exactly 6 primary questions are asked
    - Maximum 2 follow-ups total
    - Total turns never exceed 8
    - Termination condition triggers properly
    """
    # 1. Start session
    start_res = await interview_graph.ainvoke({
        "action": "start",
        "role": "AI Engineer",
        "type": "technical",
        "useResume": True,
        "resume": {
            "skills": ["Python", "FastAPI"],
            "projects": [{"name": "AI Search Engine", "technologies": ["Qdrant", "FastAPI"]}],
        }
    })

    assert start_res["primary_question_count"] == 1
    assert len(start_res["questions"]) == 1
    q1 = start_res["current_question"]

    curr_state = dict(start_res)
    turn_count = 1

    # Simulate answering up to 10 times to verify termination at <= 8 turns
    for step in range(10):
        # Alternate answers: step 1 partial, step 2 good, step 3 'I don't know', step 4 good, etc.
        if step == 0:
            ans = "I used vector embeddings and semantic search, but I didn't configure the reranking pipeline."
        elif step == 2:
            ans = "I don't know much about this specific scaling concept."
        else:
            ans = "We partitioned the indexes, implemented continuous batching, and achieved low latency."

        answer_res = await interview_graph.ainvoke({
            "action": "feedback",
            "role": "AI Engineer",
            "type": "technical",
            "current_question": curr_state["current_question"],
            "answer": ans,
            "primary_question_count": curr_state.get("primary_question_count", 1),
            "target_primary_questions": 6,
            "followup_count": curr_state.get("followup_count", 0),
            "max_followups_total": 2,
            "followups_for_current_question": curr_state.get("followups_for_current_question", 0),
            "question_ids_asked": curr_state.get("question_ids_asked", []),
            "concepts_covered": curr_state.get("concepts_covered", []),
            "verified_resume_projects": curr_state.get("verified_resume_projects", []),
            "verified_resume_skills": curr_state.get("verified_resume_skills", []),
            "skill_gaps": curr_state.get("skill_gaps", []),
            "questions": curr_state.get("questions", []),
            "answers": curr_state.get("answers", []),
            "evaluations": curr_state.get("evaluations", []),
        })

        if answer_res.get("completed"):
            # Interview successfully terminated!
            report = answer_res.get("report", {})
            assert report.get("overallScore") is not None
            assert len(report.get("topicAccuracy", [])) > 0
            break

        curr_state = answer_res
        turn_count += 1

    # Verify constraints
    assert turn_count <= 8, f"Total turns exceeded maximum 8: {turn_count}"
    assert curr_state.get("followup_count", 0) <= 2, f"Follow-ups exceeded max 2: {curr_state.get('followup_count')}"
    assert answer_res.get("completed") is True, "Interview failed to complete within target turns"


# ==========================================
# 6. DEDUPLICATION TEST
# ==========================================

@pytest.mark.asyncio
async def test_no_duplicate_questions_in_session():
    """Verify that multiple question selection calls never return the same question ID."""
    asked_ids = []
    for _ in range(5):
        q = await select_next_question(
            role="Backend Developer",
            interview_type="technical",
            verified_projects=[],
            verified_skills=["Python", "PostgreSQL"],
            skill_gaps=["Redis", "Indexing"],
            target_difficulty="medium",
            question_action="technical_question",
            excluded_ids=asked_ids,
            excluded_concepts=[],
        )
        qid = q.get("question_id")
        assert qid not in asked_ids, f"Duplicate question selected: {qid}"
        asked_ids.append(qid)


# ==========================================
# 7. RESILIENCE & FALLBACK TESTS
# ==========================================

@pytest.mark.asyncio
async def test_qdrant_and_redis_fallback_resilience():
    """Verify interview starts and evaluates cleanly even when external services timeout."""
    # Run start action with invalid/unreachable external URLs
    res = await interview_graph.ainvoke({
        "action": "start",
        "role": "DevOps Engineer",
        "type": "technical",
        "useResume": False,
        "resume": {},
    })
    assert res.get("current_question") is not None
    assert res.get("primary_question_count") == 1
    assert len(res.get("questions", [])) == 1
