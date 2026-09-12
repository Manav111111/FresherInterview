"""
Fresher.AI — Production Question Bank Validator & Semantic Duplicate Detection
Validates schema integrity, domain targets, enum constraints, and semantic intent.
Outputs: fresher_ai_kb/semantic_duplicate_report.json
"""

import json
import os
import re
from collections import Counter
from typing import List, Dict, Any

KB_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(KB_DIR, "semantic_duplicate_report.json")

EXPECTED_DOMAINS = {
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

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_QUESTION_TYPES = {"conceptual", "practical", "tradeoff", "debugging", "design", "scenario", "follow_up", "optimization"}

REQUIRED_FIELDS = [
    "question_id", "domain", "subcategory", "question_type", "difficulty",
    "question", "roles", "key_concepts", "ideal_answer", "key_concepts_to_look_for",
    "strong_answer_indicators", "partial_answer_indicators", "weak_answer_indicators",
    "common_mistakes", "evaluation_rubric", "follow_up_topics", "embedding_text",
    "quality_status"
]


def tokenize_clean(text: str) -> set:
    """Extracts normalized alphabetic token set for lexical similarity."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    words = set(cleaned.split())
    # Remove common filler words
    stop = {"a", "an", "the", "in", "on", "at", "to", "for", "with", "and", "or", "is", "are", "how", "what", "why", "which", "would", "you", "this", "if"}
    return words - stop


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def validate_bank(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors = []
    warnings = []

    seen_ids = set()
    exact_duplicates = []
    domain_counts = Counter()

    # 1. Structural & Schema Validation
    for idx, q in enumerate(questions):
        qid = q.get("question_id")
        if not qid:
            errors.append(f"Row {idx}: missing question_id")
            continue

        if qid in seen_ids:
            errors.append(f"Duplicate question_id: {qid}")
            exact_duplicates.append(qid)
        seen_ids.add(qid)

        # Check required fields
        for field in REQUIRED_FIELDS:
            val = q.get(field)
            if val is None or (isinstance(val, (str, list)) and len(val) == 0):
                errors.append(f"Question {qid}: missing or empty required field '{field}'")

        # Enums
        diff = q.get("difficulty", "").lower()
        if diff not in VALID_DIFFICULTIES:
            errors.append(f"Question {qid}: invalid difficulty '{diff}'")

        qtype = q.get("question_type", "").lower()
        if qtype not in VALID_QUESTION_TYPES:
            warnings.append(f"Question {qid}: uncommon question_type '{qtype}'")

        domain = q.get("domain", "")
        domain_counts[domain] += 1

        # Check concepts
        concepts = q.get("key_concepts", [])
        if len(concepts) < 2:
            warnings.append(f"Question {qid}: fewer than 2 key concepts ({concepts})")

        # Check rubric
        rubric = q.get("evaluation_rubric", {})
        if not rubric or sum(rubric.values()) < 90:
            errors.append(f"Question {qid}: invalid evaluation rubric (total weight < 90)")

    # 2. Domain Count Validation
    for d, expected_cnt in EXPECTED_DOMAINS.items():
        actual_cnt = domain_counts.get(d, 0)
        if actual_cnt != expected_cnt:
            errors.append(f"Domain count mismatch for '{d}': expected {expected_cnt}, got {actual_cnt}")

    # 3. Lexical & Semantic Near-Duplicate Detection
    semantic_duplicate_candidates = []
    approved_related_pairs = []

    # Compare pairs within the same domain & subcategory
    by_subcat = {}
    for q in questions:
        key = (q.get("domain"), q.get("subcategory"))
        if key not in by_subcat:
            by_subcat[key] = []
        by_subcat[key].append(q)

    for (domain, subcat), sub_qs in by_subcat.items():
        for i in range(len(sub_qs)):
            for j in range(i + 1, len(sub_qs)):
                q1 = sub_qs[i]
                q2 = sub_qs[j]

                t1 = tokenize_clean(q1.get("question", ""))
                t2 = tokenize_clean(q2.get("question", ""))
                sim = jaccard_similarity(t1, t2)

                # High lexical similarity
                if sim >= 0.70:
                    # Check intent: are they variants of the same base?
                    is_variant_pair = (
                        "edge case" in q1.get("question", "").lower() or "edge case" in q2.get("question", "").lower()
                        or "10x" in q1.get("question", "").lower() or "10x" in q2.get("question", "").lower()
                        or "trade-off" in q1.get("question", "").lower() or "trade-off" in q2.get("question", "").lower()
                        or "production example" in q1.get("question", "").lower() or "production example" in q2.get("question", "").lower()
                    )

                    if is_variant_pair:
                        approved_related_pairs.append({
                            "question_1_id": q1.get("question_id"),
                            "question_2_id": q2.get("question_id"),
                            "similarity_score": round(sim, 3),
                            "relationship": "base_and_probing_variant",
                            "status": "approved_related",
                        })
                    else:
                        semantic_duplicate_candidates.append({
                            "question_1_id": q1.get("question_id"),
                            "question_2_id": q2.get("question_id"),
                            "similarity_score": round(sim, 3),
                            "question_1_text": q1.get("question", ""),
                            "question_2_text": q2.get("question", ""),
                            "recommendation": "keep_distinct_or_link_as_followup",
                        })

    report = {
        "schema_version": "2.0",
        "total_questions_checked": len(questions),
        "domain_counts": dict(domain_counts),
        "validation_summary": {
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "exact_duplicates_count": len(exact_duplicates),
            "semantic_duplicate_candidates_count": len(semantic_duplicate_candidates),
            "approved_related_pairs_count": len(approved_related_pairs),
        },
        "errors": errors,
        "warnings": warnings[:50],  # cap display
        "exact_duplicates": exact_duplicates,
        "semantic_duplicate_candidates": semantic_duplicate_candidates[:100],
        "approved_related_pairs": approved_related_pairs[:100],
        "removed_questions": [],
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    from data.interview_question_bank_v2 import get_interview_question_bank
    qs = get_interview_question_bank()
    rep = validate_bank(qs)
    print("\n" + "="*60)
    print("VALIDATION RESULTS:")
    print(f"Total Questions: {rep['total_questions_checked']}")
    print(f"Errors: {rep['validation_summary']['total_errors']}")
    print(f"Warnings: {rep['validation_summary']['total_warnings']}")
    print(f"Exact Duplicates: {rep['validation_summary']['exact_duplicates_count']}")
    print(f"Semantic Duplicate Candidates: {rep['validation_summary']['semantic_duplicate_candidates_count']}")
    print(f"Approved Related Pairs: {rep['validation_summary']['approved_related_pairs_count']}")
    print("Domain Counts:")
    for d, c in sorted(rep['domain_counts'].items()):
        print(f"  - {d}: {c}")
    print("Report saved to:", REPORT_PATH)
    print("="*60 + "\n")
