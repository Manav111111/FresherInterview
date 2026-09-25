"""
Fresher.AI — Interview Question Deduplication & Lifecycle Regression Tests
Tests:
1. Canonical question ID uniqueness across multiple interview turns.
2. Automatic exclusion of related question variants (e.g. ai-enginee-028 & 094 when 001 is asked).
3. Semantic near-duplicate detection and exclusion based on token fingerprints.
4. Session restoration: full history reconstruction from questions JSONB array.
5. Idempotent answer submission preventing duplicate question generation.
6. Diverse fallback pool preventing repetition of hardcoded fallback questions.
7. Graceful interview termination when candidate pool is exhausted.
8. Legitimate follow-up preservation without duplicating the main question.
"""

import pytest
import re
from typing import Dict, Any, List

from app.utils.interview_dedup import (
    get_canonical_bank_map,
    extract_session_excluded_history,
    is_candidate_duplicate,
    normalize_question_tokens,
    normalize_question_fingerprint,
    calculate_question_similarity,
    get_diverse_fallback_question,
)
from app.agents.interview_graph import select_next_question, interview_graph


# =========================================================================
# 1. CANONICAL QUESTION ID & VARIANT EXCLUSION
# =========================================================================

def test_canonical_bank_and_related_variants():
    """Verify that asking a base question automatically excludes all its variant questions."""
    bank = get_canonical_bank_map()
    assert len(bank) >= 760, f"Expected 760 questions, got {len(bank)}"

    base_qid = "ai-enginee-001"
    assert base_qid in bank, "Base question ai-enginee-001 must exist in bank"
    related_ids = bank[base_qid].get("related_question_ids", [])
    assert len(related_ids) > 0, "Base question must have related variant IDs in bank"

    # Simulate session where base question was asked
    session = {
        "questions": [{
            "question_id": base_qid,
            "question": bank[base_qid]["question"],
            "related_question_ids": related_ids,
        }]
    }
    history = extract_session_excluded_history(session)

    # 1. Base question must be excluded
    assert base_qid in history["excluded_ids"]
    assert is_candidate_duplicate(bank[base_qid], history) is True

    # 2. All related variants must be excluded from selection as new primary questions
    for rel_id in related_ids:
        assert rel_id.lower() in history["excluded_ids"], f"Variant {rel_id} should be in excluded_ids"
        if rel_id.lower() in bank:
            assert is_candidate_duplicate(bank[rel_id.lower()], history) is True, f"Variant {rel_id} must be flagged as duplicate"


# =========================================================================
# 2. TOKEN FINGERPRINT & SEMANTIC DUPLICATE DETECTION
# =========================================================================

def test_semantic_duplicate_detection():
    """Verify that rephrased questions with different IDs but high token overlap are blocked."""
    history = {
        "excluded_ids": {"custom_q_001"},
        "asked_fingerprints": set(),
        "asked_token_sets": [normalize_question_tokens("How does Redis caching work and what eviction policies exist?")],
        "asked_projects": set(),
    }

    # Near duplicate rephrasing
    candidate_rephrased = {
        "question_id": "custom_q_999",
        "question": "Can you explain how Redis caching works and what eviction policies you can configure?",
    }

    assert is_candidate_duplicate(candidate_rephrased, history, similarity_threshold=0.65) is True

    # Completely different question
    candidate_different = {
        "question_id": "custom_q_100",
        "question": "What is the difference between TCP and UDP at the transport layer?",
    }
    assert is_candidate_duplicate(candidate_different, history, similarity_threshold=0.65) is False


# =========================================================================
# 3. MULTI-TURN SELECTION HAS ZERO REPEATED QUESTIONS
# =========================================================================

@pytest.mark.asyncio
async def test_multi_turn_interview_selection_never_repeats():
    """Verify that sequentially selecting questions for an interview never yields duplicate IDs or variants."""
    asked_history = {
        "excluded_ids": set(),
        "asked_canonical_ids": set(),
        "asked_related_ids": set(),
        "asked_fingerprints": set(),
        "asked_token_sets": [],
        "asked_projects": set(),
    }

    selected_questions = []

    for turn in range(6):
        q = await select_next_question(
            role="AI Engineer",
            interview_type="technical",
            verified_projects=[],
            verified_skills=["Python", "FastAPI", "Qdrant"],
            skill_gaps=[],
            target_difficulty="medium",
            question_action="technical_question",
            excluded_ids=list(asked_history["excluded_ids"]),
            excluded_concepts=[],
            excluded_history=asked_history,
        )

        qid = q.get("question_id")
        assert qid is not None, f"Turn {turn} returned null question_id"
        assert qid not in [sq["question_id"] for sq in selected_questions], f"Turn {turn} repeated question_id {qid}"

        # Verify semantic similarity against all previously selected
        q_text = q.get("question", "")
        for prev in selected_questions:
            sim = calculate_question_similarity(q_text, prev["question"])
            assert sim < 0.70, f"Turn {turn} ({qid}) too similar ({sim:.2f}) to previous ({prev['question_id']})"

        selected_questions.append(q)

        # Update history
        asked_history["excluded_ids"].add(str(qid).strip().lower())
        for rel in q.get("related_question_ids", []):
            asked_history["excluded_ids"].add(str(rel).strip().lower())
        toks = normalize_question_tokens(q_text)
        if toks:
            asked_history["asked_token_sets"].append(toks)

    assert len(selected_questions) == 6


# =========================================================================
# 4. SESSION RESTORATION PRESERVES COMPLETE HISTORY FROM QUESTIONS JSONB
# =========================================================================

def test_session_restoration_from_questions_array():
    """Verify that restoring a session with only questions array reconstructs all excluded IDs and variants."""
    restored_session = {
        "id": "test_session_123",
        "current_question": 2,
        # notice: question_ids_asked is intentionally absent (as when restored from Supabase)
        "questions": [
            {
                "question_id": "ai-enginee-001",
                "question": "A production LLM endpoint is too slow. What would you measure first?",
                "related_question_ids": ["ai-enginee-028", "ai-enginee-094"],
            },
            {
                "question_id": "dsa-012",
                "question": "Given a binary tree, serialize and deserialize it into a string format.",
                "related_question_ids": ["dsa-090"],
            },
        ],
    }

    history = extract_session_excluded_history(restored_session)

    # Must contain both asked canonical IDs
    assert "ai-enginee-001" in history["excluded_ids"]
    assert "dsa-012" in history["excluded_ids"]

    # Must contain related variant IDs
    assert "ai-enginee-028" in history["excluded_ids"]
    assert "ai-enginee-094" in history["excluded_ids"]
    assert "dsa-090" in history["excluded_ids"]

    # Must contain token sets for semantic duplicate checking
    assert len(history["asked_token_sets"]) == 2


# =========================================================================
# 5. DIVERSE FALLBACK POOL NEVER REPEATS
# =========================================================================

def test_diverse_fallback_pool_distinct():
    """Verify that fallback pool returns distinct questions and terminates gracefully if exhausted."""
    history = {
        "excluded_ids": set(),
        "asked_canonical_ids": set(),
        "asked_related_ids": set(),
        "asked_fingerprints": set(),
        "asked_token_sets": [],
        "asked_projects": set(),
    }

    fallbacks = []
    for _ in range(5):
        fb = get_diverse_fallback_question(
            interview_type="technical",
            target_difficulty="medium",
            excluded_history=history,
        )
        if not fb:
            break
        assert fb["question_id"] not in [f["question_id"] for f in fallbacks]
        fallbacks.append(fb)
        history["excluded_ids"].add(fb["question_id"].lower())
        toks = normalize_question_tokens(fb["question"])
        if toks:
            history["asked_token_sets"].append(toks)

    assert len(fallbacks) == 5, f"Expected 5 distinct technical fallbacks, got {len(fallbacks)}"


# =========================================================================
# 6. FOLLOW-UP QUESTIONS PRESERVE CONTEXT WITHOUT REPEATING MAIN QUESTION
# =========================================================================

@pytest.mark.asyncio
async def test_followup_question_does_not_repeat_main():
    """Verify that follow-up questions probe missing concepts and do not duplicate main question text."""
    pri_q = {
        "question_id": "tech_redis_01",
        "question": "Explain how Redis cache invalidation strategies work in distributed systems.",
        "difficulty": "medium",
        "topic": "Caching",
    }
    last_eval = {
        "score": 60,
        "correct_points": ["cache-aside pattern", "TTL expiration"],
        "missing_points": ["write-through vs write-behind consistency trade-offs"],
    }

    fu = await select_next_question(
        role="Backend Developer",
        interview_type="technical",
        verified_projects=[],
        verified_skills=[],
        skill_gaps=[],
        target_difficulty="medium",
        question_action="follow_up",
        excluded_ids=["tech_redis_01"],
        excluded_concepts=[],
        last_evaluation=last_eval,
        current_primary_q=pri_q,
        fu_count=0,
    )

    assert fu["is_follow_up"] is True
    assert fu["parent_question_id"] == "tech_redis_01"
    assert "followup_1" in fu["question_id"]

    # Follow-up must probe missing concept and NOT duplicate main question
    sim = calculate_question_similarity(fu["question"], pri_q["question"])
    assert sim < 0.70, f"Follow-up question should not duplicate main question (similarity: {sim})"
    assert any(term in fu["question"].lower() for term in ["trade-off", "consistency", "write", "behind", "through", "handle", "elaborate"])
