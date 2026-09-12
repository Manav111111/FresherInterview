"""
Builds the canonical Python module fresher_ai_kb/data/interview_question_bank_v2.py
from interview_question_bank_v2.csv with complete structured metadata.
"""

import csv
import json
import os
import re

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DATA_DIR, "data", "interview_question_bank_v2.csv")
TARGET_PY = os.path.join(DATA_DIR, "data", "interview_question_bank_v2.py")
TARGET_JSON = os.path.join(DATA_DIR, "json_export", "interview_questions_v2.json")

# Hand-crafted rich knowledge anchors for the 10 domains
DOMAIN_KNOWLEDGE = {
    "AI Engineering": {
        "ideal_focus": "Address latency (TTFT/TPOT), vector similarity search, chunking boundaries, hybrid search (dense + BM25 with RRF), prompt caching, cross-encoder rerankers, and automated RAGAS evaluation.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Focusing solely on prompt wording without architectural latency or retrieval mitigations", "Assuming vector search alone handles exact acronyms and SKUs"],
    },
    "DSA": {
        "ideal_focus": "Analyze time and space complexity with Big-O notation, explain data structure trade-offs (e.g., hash map O(1) avg vs space overhead), identify two-pointer/sliding window patterns, and verify boundary conditions (empty input, duplicates, overflow).",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Providing brute force without complexity analysis", "Failing to handle null/empty arrays, single-element collections, or integer overflow"],
    },
    "Core CS": {
        "ideal_focus": "Differentiate processes and threads with virtual memory address spaces, explain synchronization primitives (mutex vs semaphore vs lock-free), detail OS scheduling, and explain TCP handshake / TLS 1.3 flow.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Confusing process memory isolation with shared thread heap", "Assuming TCP guarantees order without sequence numbers and sliding windows"],
    },
    "Backend": {
        "ideal_focus": "Design idempotent RESTful endpoints, compare async event-loop concurrency with worker thread pools, structure relational schemas with foreign keys and indexes, and implement distributed Redis caching and rate-limiting.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Running CPU-bound blocking code inside async event loops", "Omitting database transaction boundaries during multi-step write operations"],
    },
    "Frontend": {
        "ideal_focus": "Explain React Fiber reconciliation, Virtual DOM diffing, reference stability (useCallback/useMemo), Core Web Vitals (LCP, CLS, INP), browser rendering critical path, and state management encapsulation.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Believing Virtual DOM is always faster than direct DOM manipulation", "Overusing memoization hooks on primitive or cheap computations"],
    },
    "DevOps/Cloud": {
        "ideal_focus": "Troubleshoot Kubernetes CrashLoopBackOff via kubectl describe and logs --previous, optimize multi-stage Docker builds, secure remote Terraform state with DynamoDB locking, and implement blue/green rollouts.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Deleting state files to resolve drift instead of terraform refresh/import", "Ignoring exit codes (e.g. exit code 137 indicating OOMKilled)"],
    },
    "Databases/SQL": {
        "ideal_focus": "Analyze query execution plans with EXPLAIN ANALYZE, compare B-Tree index sequential page sweeps vs random heap tuple lookups, enforce ACID isolation levels, and use window functions and cursor pagination.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Using OFFSET pagination on multi-million row tables causing full table scans", "Assuming an index is always chosen regardless of query selectivity"],
    },
    "ML/Data Science": {
        "ideal_focus": "Handle missing values and data leakage, select appropriate evaluation metrics (Precision/Recall/F1/ROC-AUC for imbalanced classes), prevent overfitting via regularization and cross-validation, and monitor production drift.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Using raw Accuracy metric on severely imbalanced datasets", "Fitting preprocessing scalers on the entire dataset before train-test split (data leakage)"],
    },
    "System Design": {
        "ideal_focus": "Gather functional and non-functional requirements, calculate back-of-the-envelope scale/storage estimates, design high-level API contracts, partition data (sharding/replication), and ensure fault-tolerant caching and failover.",
        "rubric": {"correctness": 40, "completeness": 20, "reasoning": 15, "communication": 15, "relevance": 10},
        "mistakes": ["Jumping straight into drawing boxes without clarifying read/write ratios and scale", "Assuming single database instances can handle 100k+ writes/second without partitioning"],
    },
    "Behavioral/HR": {
        "ideal_focus": "Structure answers using the STAR methodology (Situation, Task, Action, Result), emphasize personal accountability and data-driven conflict resolution, demonstrate growth mindset, and align with company values.",
        "rubric": {"relevance": 25, "communication": 25, "structure": 20, "examples": 15, "confidence": 15},
        "mistakes": ["Speaking vaguely without specific Situation and quantifiable Results", "Blaming coworkers or managers for project roadblocks instead of showing constructive action"],
    },
}


def build_questions():
    questions = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row["question_id"].strip()
            domain = row["domain"].strip()
            subcat = row["subcategory"].strip()
            qtype = row["question_type"].strip()
            diff = row["difficulty"].strip().lower()
            qtext = row["question"].strip()
            raw_concepts = [c.strip() for c in row["key_concepts"].split(";") if c.strip()]
            raw_roles = [r.strip() for r in row["roles"].split(";") if r.strip()]
            status = row.get("content_status", "curated").strip()

            dk = DOMAIN_KNOWLEDGE.get(domain, DOMAIN_KNOWLEDGE["Core CS"])

            # Determine if this is a variant or base question
            is_variant = "How would you answer this if" in qtext or "What edge case or failure mode" in qtext or "10x larger" in qtext or "What trade-off would you explain" in qtext or "How would you debug this if it worked locally" in qtext

            # Base question relation
            base_id = qid
            # Clean base text
            base_qtext = re.sub(r"\s*(How would you answer this if|What edge case or failure mode|How would your approach change|What trade-off would you explain|How would you debug this if).*$", "", qtext).strip()

            ideal_answer = f"A high-caliber answer addresses {subcat} principles: {dk['ideal_focus']} In the context of '{base_qtext}', articulate the core mechanism, explain concrete technical trade-offs, and detail edge-case resilience."

            key_concepts_to_look_for = ", ".join(raw_concepts)

            strong_indicators = [
                f"Demonstrates deep, accurate understanding of {subcat} and its underlying architecture.",
                f"Accurately articulates technical trade-offs and explains real-world constraints.",
                "Provides concrete, well-structured examples with professional terminology."
            ]

            partial_indicators = [
                f"Mentions core concepts like {raw_concepts[0] if raw_concepts else subcat} but omits architectural nuance or edge cases.",
                "Explains the definition accurately but lacks depth in production trade-offs.",
                "States the correct high-level approach but misses critical failure modes."
            ]

            weak_indicators = [
                "Provides vague, non-technical or superficial descriptions.",
                "Confuses foundational terminology or principles.",
                "States 'I don't know' or provides off-topic answers."
            ]

            embedding_text = (
                f"Question ID: {qid}\n"
                f"Domain: {domain}\n"
                f"Subcategory: {subcat}\n"
                f"Type: {qtype}\n"
                f"Difficulty: {diff.capitalize()}\n"
                f"Question: {qtext}\n"
                f"Target Roles: {', '.join(raw_roles)}\n"
                f"Key Concepts: {', '.join(raw_concepts)}"
            )

            # Quality state:
            # Curated questions are production_approved.
            # Expanded questions are semantic_reviewed.
            quality_status = "production_approved" if status == "curated" and not is_variant else "semantic_reviewed"

            # Determine related questions (sibling variants or parent)
            related_ids = []

            question_obj = {
                "question_id": qid,
                "domain": domain,
                "subcategory": subcat,
                "question_type": qtype,
                "difficulty": diff,
                "question": qtext,
                "roles": raw_roles,
                "key_concepts": raw_concepts,
                "ideal_answer": ideal_answer,
                "key_concepts_to_look_for": key_concepts_to_look_for,
                "strong_answer_indicators": strong_indicators,
                "partial_answer_indicators": partial_indicators,
                "weak_answer_indicators": weak_indicators,
                "common_mistakes": dk["mistakes"],
                "evaluation_rubric": dk["rubric"],
                "follow_up_topics": [f"Advanced {subcat}", f"{subcat} at Scale", f"{subcat} Failure Recovery"],
                "related_question_ids": related_ids,
                "embedding_text": embedding_text,
                "quality_status": quality_status,
                "content_status": status,
            }
            questions.append(question_obj)

    # Link related question IDs
    base_map = {}
    for q in questions:
        base_match = re.match(r"^([a-z\-]+-\d{3})", q["question_id"])
        prefix = base_match.group(1) if base_match else q["question_id"]
        # Match by base question text
        clean_text = re.sub(r"\s*(How would you answer this if|What edge case or failure mode|How would your approach change|What trade-off would you explain|How would you debug this if).*$", "", q["question"]).strip()
        if clean_text not in base_map:
            base_map[clean_text] = []
        base_map[clean_text].append(q["question_id"])

    for q in questions:
        clean_text = re.sub(r"\s*(How would you answer this if|What edge case or failure mode|How would your approach change|What trade-off would you explain|How would you debug this if).*$", "", q["question"]).strip()
        siblings = base_map.get(clean_text, [])
        q["related_question_ids"] = [s for s in siblings if s != q["question_id"]][:5]

    return questions


def main():
    questions = build_questions()
    print(f"Loaded {len(questions)} questions.")

    # Write Python module
    py_content = f'''"""
Fresher.AI Knowledge Base — Production Interview Question Bank v2
Contains {len(questions)} curated & reviewed questions across all 10 technical & career domains.
Metadata includes rubrics, strong/partial/weak indicators, follow-ups, and dense embedding text.
"""

from typing import List, Dict, Any, Optional

INTERVIEW_QUESTION_BANK_V2: List[Dict[str, Any]] = {json.dumps(questions, indent=2)}

def get_interview_question_bank() -> List[Dict[str, Any]]:
    """Returns all questions in the v2 question bank."""
    return INTERVIEW_QUESTION_BANK_V2

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific question by stable identifier."""
    for q in INTERVIEW_QUESTION_BANK_V2:
        if q.get("question_id") == question_id:
            return q
    return None

def get_questions_by_domain(domain: str) -> List[Dict[str, Any]]:
    """Filters questions by domain (e.g. 'AI Engineering', 'DSA', 'Databases/SQL')."""
    d_lower = domain.lower()
    return [q for q in INTERVIEW_QUESTION_BANK_V2 if q.get("domain", "").lower() == d_lower]

def get_questions_by_role(role_id: str) -> List[Dict[str, Any]]:
    """Filters questions relevant to a target role ID (e.g. 'ai_engineer', 'backend_engineer')."""
    r_lower = role_id.lower().replace(" ", "_")
    return [q for q in INTERVIEW_QUESTION_BANK_V2 if any(r_lower in r.lower() for r in q.get("roles", []))]

def get_domains() -> List[str]:
    """Returns sorted list of distinct domains in the bank."""
    return sorted(list(set(q.get("domain", "") for q in INTERVIEW_QUESTION_BANK_V2)))
'''

    with open(TARGET_PY, "w", encoding="utf-8") as f:
        f.write(py_content)
    print(f"Generated Python module: {TARGET_PY}")

    # Write JSON export
    os.makedirs(os.path.dirname(TARGET_JSON), exist_ok=True)
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)
    print(f"Exported JSON: {TARGET_JSON}")


if __name__ == "__main__":
    main()
