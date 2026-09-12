"""
Fresher.AI Knowledge Base — Interview Questions Data Module
Curated technical, system design, and behavioral interview questions mapped to roles and skills.
Exports the full 760-question production question bank v2.
"""

from typing import List, Dict, Any
from .interview_question_bank_v2 import (
    INTERVIEW_QUESTION_BANK_V2,
    get_interview_question_bank,
    get_question_by_id,
    get_questions_by_domain,
    get_questions_by_role,
    get_domains,
)

# Canonical export maintaining backward-compatibility with SHEETS_REGISTRY
INTERVIEW_QUESTIONS: List[Dict[str, Any]] = []

for q in INTERVIEW_QUESTION_BANK_V2:
    # Normalize for any legacy code expecting role_id or category
    role_id = q.get("roles", ["software_engineer"])[0] if q.get("roles") else "software_engineer"
    normalized = dict(q)
    normalized["role_id"] = role_id
    normalized["role_ids"] = ";".join(q.get("roles", []))
    normalized["category"] = q.get("domain", "Technical")
    normalized["skill_id"] = q.get("key_concepts", ["general"])[0] if q.get("key_concepts") else "general"
    normalized["skill_ids"] = ";".join(q.get("key_concepts", []))
    INTERVIEW_QUESTIONS.append(normalized)


def get_interview_questions() -> List[Dict[str, Any]]:
    """Returns the complete 760-question production bank."""
    return INTERVIEW_QUESTIONS


def get_interview_questions_headers() -> List[str]:
    return [
        "question_id", "domain", "subcategory", "question_type", "difficulty",
        "question", "roles", "key_concepts", "ideal_answer", "key_concepts_to_look_for",
        "strong_answer_indicators", "partial_answer_indicators", "weak_answer_indicators",
        "common_mistakes", "evaluation_rubric", "follow_up_topics", "related_question_ids",
        "embedding_text", "quality_status"
    ]
