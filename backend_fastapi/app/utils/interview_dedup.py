"""
Fresher.AI — Canonical Interview Question Deduplication & Tracking Engine
Provides:
- Stable canonical question ID resolution (strictly payload.question_id, never point UUID)
- Normalized text tokenization & fingerprinting
- Variant detection via question-bank related_question_ids & semantic token similarity
- Safe session history extraction from restored JSONB questions
- Diverse, non-repeating fallback pools
"""

import re
import sys
import os
import logging
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger("fresherai.interview_dedup")

# Stop words for semantic question tokenization
QUESTION_STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "of", "to", "for", "with", "on", "at",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
    "will", "shall", "may", "might", "must", "how", "what", "why", "when", "where",
    "which", "who", "whom", "this", "that", "these", "those", "you", "your", "we",
    "our", "they", "their", "explain", "describe", "tell", "walk", "through", "about",
    "please", "interview", "interviewer", "candidate", "answer", "asked", "question"
}

_CACHED_BANK_MAP: Optional[Dict[str, Dict[str, Any]]] = None


def get_canonical_bank_map() -> Dict[str, Dict[str, Any]]:
    """Loads and caches the 760-question bank mapped by canonical question_id."""
    global _CACHED_BANK_MAP
    if _CACHED_BANK_MAP is not None:
        return _CACHED_BANK_MAP

    try:
        from data.interview_question_bank_v2 import get_interview_question_bank
    except ImportError:
        try:
            # Ensure workspace path resolution
            p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "fresher_ai_kb", "data"))
            p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            if p1 not in sys.path:
                sys.path.insert(0, p1)
            if p2 not in sys.path:
                sys.path.insert(0, p2)
            from interview_question_bank_v2 import get_interview_question_bank
        except ImportError:
            try:
                from fresher_ai_kb.data.interview_question_bank_v2 import get_interview_question_bank
            except ImportError:
                logger.warning("Could not load interview_question_bank_v2; using empty bank map.")
                _CACHED_BANK_MAP = {}
                return _CACHED_BANK_MAP

    bank = get_interview_question_bank()
    _CACHED_BANK_MAP = {str(q.get("question_id", "")).strip().lower(): q for q in bank if q.get("question_id")}
    return _CACHED_BANK_MAP


def stem_token(word: str) -> str:
    """Lightweight suffix normalizer without external dependencies."""
    w = word.lower()
    for suffix in ["tion", "ing", "ies", "es", "ed", "s"]:
        if len(w) > len(suffix) + 2 and w.endswith(suffix):
            if suffix == "ies":
                return w[:-3] + "y"
            return w[:-len(suffix)]
    return w


def normalize_question_tokens(text: str) -> Set[str]:
    """Extracts stemmed semantic keyword tokens for high-precision duplicate detection."""
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = cleaned.split()
    return {stem_token(w) for w in words if len(w) > 2 and w not in QUESTION_STOP_WORDS}


def normalize_question_fingerprint(text: str) -> str:
    """Canonical text fingerprint string from sorted tokens."""
    tokens = sorted(list(normalize_question_tokens(text)))
    return " ".join(tokens)


def calculate_question_similarity(text1: str, text2: str) -> float:
    """Computes Jaccard token similarity between two questions."""
    t1 = normalize_question_tokens(text1)
    t2 = normalize_question_tokens(text2)
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0


def extract_session_excluded_history(interview_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts the complete canonical exclusion history for an interview session.
    Works seamlessly whether session is fresh or restored from Supabase JSONB questions.
    """
    asked_canonical_ids: Set[str] = set()
    asked_related_ids: Set[str] = set()
    asked_fingerprints: Set[str] = set()
    asked_token_sets: List[Set[str]] = []
    asked_projects: Set[str] = set()

    # 1. From state question_ids_asked
    for qid in interview_state.get("question_ids_asked", []):
        if qid:
            asked_canonical_ids.add(str(qid).strip().lower())

    # 2. From questions array (guaranteed persisted in DB)
    questions = interview_state.get("questions", [])
    for q in questions:
        if not isinstance(q, dict):
            continue
        qid = q.get("question_id")
        if qid:
            clean_qid = str(qid).strip().lower()
            asked_canonical_ids.add(clean_qid)

            for rel_id in q.get("related_question_ids", []):
                if rel_id:
                    asked_related_ids.add(str(rel_id).strip().lower())

        qtext = q.get("question", "")
        if qtext:
            fp = normalize_question_fingerprint(qtext)
            if fp:
                asked_fingerprints.add(fp)
            toks = normalize_question_tokens(qtext)
            if toks:
                asked_token_sets.append(toks)

        pref = q.get("resume_reference")
        if pref:
            asked_projects.add(str(pref).strip().lower())

    # 3. Add bank-level related_question_ids for all asked questions
    bank_map = get_canonical_bank_map()
    for qid in list(asked_canonical_ids):
        if qid in bank_map:
            bank_item = bank_map[qid]
            for rel_id in bank_item.get("related_question_ids", []):
                if rel_id:
                    asked_related_ids.add(str(rel_id).strip().lower())

    combined_excluded_ids = asked_canonical_ids | asked_related_ids

    return {
        "excluded_ids": combined_excluded_ids,
        "asked_canonical_ids": asked_canonical_ids,
        "asked_related_ids": asked_related_ids,
        "asked_fingerprints": asked_fingerprints,
        "asked_token_sets": asked_token_sets,
        "asked_projects": asked_projects,
    }


def is_candidate_duplicate(
    candidate: Dict[str, Any],
    excluded_history: Dict[str, Any],
    similarity_threshold: float = 0.65,
) -> bool:
    """
    Checks if candidate is an exact ID duplicate, bank-variant duplicate,
    fingerprint match, or semantic near-duplicate of an already-asked question.
    """
    qid = str(candidate.get("question_id", "")).strip().lower()
    excluded_ids = excluded_history.get("excluded_ids", set())

    # 1. Exact canonical ID check
    if qid and qid in excluded_ids:
        return True

    # 2. Check candidate's own related_question_ids
    for rel_id in candidate.get("related_question_ids", []):
        if str(rel_id).strip().lower() in excluded_ids:
            return True

    # 3. Normalized fingerprint match
    qtext = candidate.get("question", "")
    if not qtext:
        return False

    q_fp = normalize_question_fingerprint(qtext)
    if q_fp and q_fp in excluded_history.get("asked_fingerprints", set()):
        return True

    # 4. Token overlap similarity check against all asked questions
    c_tokens = normalize_question_tokens(qtext)
    if not c_tokens:
        return False

    for asked_t in excluded_history.get("asked_token_sets", []):
        if not asked_t:
            continue
        union_len = len(c_tokens | asked_t)
        if union_len > 0:
            sim = len(c_tokens & asked_t) / union_len
            if sim >= similarity_threshold:
                return True

    return False


# Diverse fallback pools to avoid repeating hardcoded questions
DIVERSE_FALLBACK_POOL = {
    "technical": [
        {
            "question_id": "fallback_tech_001",
            "question": "Walk me through how you would architect a resilient, high-throughput service for this role. What database indexing and caching strategies would you select?",
            "topic": "System Architecture & Caching",
            "difficulty": "medium",
        },
        {
            "question_id": "fallback_tech_002",
            "question": "Describe an engineering trade-off you encountered when optimizing for latency versus data consistency. How did you validate your decision?",
            "topic": "Engineering Trade-offs",
            "difficulty": "medium",
        },
        {
            "question_id": "fallback_tech_003",
            "question": "How do you detect, isolate, and debug intermittent race conditions or memory leaks in a distributed backend or web application?",
            "topic": "Debugging & Concurrency",
            "difficulty": "hard",
        },
        {
            "question_id": "fallback_tech_004",
            "question": "Explain the core principles of designing idempotent REST or asynchronous APIs. How do you prevent duplicate side effects under network retries?",
            "topic": "API Design & Idempotency",
            "difficulty": "medium",
        },
        {
            "question_id": "fallback_tech_005",
            "question": "When refactoring a legacy codebase, what testing methodology and CI/CD safeguards do you implement to ensure zero downtime and no regressions?",
            "topic": "Code Quality & Deployment",
            "difficulty": "medium",
        },
    ],
    "hr": [
        {
            "question_id": "fallback_hr_001",
            "question": "Tell me about a challenging technical roadblock or conflicting priority you navigated with a teammate. How did you reach a consensus?",
            "topic": "Collaboration & Conflict",
            "difficulty": "medium",
        },
        {
            "question_id": "fallback_hr_002",
            "question": "Describe a scenario where a deployment or feature you shipped did not go as planned. What was the impact, and how did you resolve it?",
            "topic": "Ownership & Failure Recovery",
            "difficulty": "medium",
        },
        {
            "question_id": "fallback_hr_003",
            "question": "How do you stay continuously updated with rapidly shifting AI and software engineering stacks while meeting tight project deadlines?",
            "topic": "Continuous Learning",
            "difficulty": "easy",
        },
    ],
}


def get_diverse_fallback_question(
    interview_type: str,
    target_difficulty: str,
    excluded_history: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Selects an unused fallback question from the diverse pool."""
    pool_key = "hr" if interview_type.lower() == "hr" else "technical"
    pool = DIVERSE_FALLBACK_POOL.get(pool_key, DIVERSE_FALLBACK_POOL["technical"])

    for item in pool:
        if not is_candidate_duplicate(item, excluded_history, similarity_threshold=0.60):
            return {
                "question_id": item["question_id"],
                "question": item["question"],
                "difficulty": item.get("difficulty", target_difficulty),
                "timer": 90,
                "topic": item.get("topic", "Core Fundamentals"),
                "source": "fallback_pool",
                "is_follow_up": False,
            }

    return None
