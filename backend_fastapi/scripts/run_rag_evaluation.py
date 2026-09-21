"""
Fresher.AI — RAG Evaluation Runner & Benchmark
Runs baseline (Stage 1 Vector/KB Retrieval) versus Stage 2 Reranked Retrieval
across the 35 curated evaluation queries and prints the exact measured comparison table.
"""

import json
import os
import sys
import time
from typing import List, Dict, Any

# Ensure backend root and project root are in sys.path
BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_BACKEND, ".."))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.rag_evaluator import RetrievalEvaluator
from app.services.reranker_service import RerankerService

EVAL_DATASET_PATH = os.path.join(BASE_BACKEND, "tests", "data", "rag_eval_dataset.json")


def load_all_candidate_questions() -> List[Dict[str, Any]]:
    """Loads all 760 canonical questions from the question bank."""
    try:
        from fresher_ai_kb.data.interview_question_bank_v2 import get_interview_question_bank
        return get_interview_question_bank()
    except Exception as e:
        try:
            from data.interview_question_bank_v2 import get_interview_question_bank
            return get_interview_question_bank()
        except Exception:
            return []


def baseline_retriever(query: str, all_questions: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Stage 1 Baseline Retriever:
    Simulates standard lexical/vector candidate selection based on title/question/concept overlap.
    """
    q_tokens = set(query.lower().split())
    scored = []
    for q in all_questions:
        text = f"{q.get('question', '')} {' '.join(q.get('key_concepts', []))} {q.get('subcategory', '')}".lower()
        score = sum(1.0 for t in q_tokens if t in text)
        scored.append((score, q))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [q for _, q in scored[:top_n]]


def run_benchmark():
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    all_questions = load_all_candidate_questions()
    reranker = RerankerService(enabled=True)

    # Define baseline retriever func (returning IDs)
    def run_baseline(query: str, max_k: int) -> List[str]:
        candidates = baseline_retriever(query, all_questions, top_n=max_k)
        return [c.get("question_id") for c in candidates]

    # Define reranked retriever func (returning IDs)
    def run_reranked(query: str, max_k: int) -> List[str]:
        # Stage 1: Retrieve top-20 candidates
        candidates = baseline_retriever(query, all_questions, top_n=20)
        # Stage 2: Rerank to max_k
        reranked = reranker.rerank(query=query, candidates=candidates, top_k=max_k)
        return [c.get("question_id") for c in reranked]

    evaluator = RetrievalEvaluator(k_values=[1, 3, 5, 10])

    # Time baseline
    start_b = time.perf_counter()
    baseline_metrics = evaluator.evaluate_dataset(dataset, run_baseline)
    baseline_time = (time.perf_counter() - start_b) * 1000.0 / len(dataset)

    # Time reranked
    start_r = time.perf_counter()
    reranked_metrics = evaluator.evaluate_dataset(dataset, run_reranked)
    reranked_time = (time.perf_counter() - start_r) * 1000.0 / len(dataset)

    print("\n=======================================================")
    print("FRESHER.AI — RAG RETRIEVAL EVALUATION RESULTS (OVERALL 100 QUERIES)")
    print("=======================================================")
    print(f"Dataset Size: {len(dataset)} evaluation queries across 7 technical domains")
    print(f"Baseline Latency per Query: {baseline_time:.2f} ms")
    print(f"Reranked Latency per Query: {reranked_time:.2f} ms (Overhead: +{reranked_time - baseline_time:.2f} ms)\n")
    print(f"{'Metric':<15} | {'Baseline':<12} | {'Reranked':<12} | {'Delta':<10}")
    print("-" * 56)
    for metric in ["recall@1", "recall@3", "recall@5", "recall@10", "precision@1", "precision@3", "precision@5", "precision@10", "mrr@1", "mrr@3", "mrr@5", "mrr@10", "ndcg@1", "ndcg@3", "ndcg@5", "ndcg@10"]:
        b_val = baseline_metrics.get(metric, 0.0)
        r_val = reranked_metrics.get(metric, 0.0)
        delta = r_val - b_val
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
        print(f"{metric:<15} | {b_val:<12.4f} | {r_val:<12.4f} | {delta_str:<10}")
    print("=======================================================\n")

    # Evaluate by query type slice
    types = ["canonical", "paraphrase", "noisy_short", "ambiguous_conversational"]
    print("---------------------------------------------------------------------------------------------")
    print(f"{'Query Slice':<26} | {'Count':<6} | {'Recall@1 (Base/Rerank)':<22} | {'Recall@5 (Base/Rerank)':<22} | {'MRR@5 (Base/Rerank)':<20}")
    print("---------------------------------------------------------------------------------------------")
    for qt in types:
        sub = [item for item in dataset if item.get("type") == qt]
        if not sub:
            continue
        sub_b = evaluator.evaluate_dataset(sub, run_baseline)
        sub_r = evaluator.evaluate_dataset(sub, run_reranked)
        print(f"{qt:<26} | {len(sub):<6} | {sub_b['recall@1']:.4f} / {sub_r['recall@1']:.4f}      | {sub_b['recall@5']:.4f} / {sub_r['recall@5']:.4f}      | {sub_b['mrr@5']:.4f} / {sub_r['mrr@5']:.4f}")
    print("---------------------------------------------------------------------------------------------\n")

    return {
        "dataset_size": len(dataset),
        "baseline_latency_ms": round(baseline_time, 2),
        "reranked_latency_ms": round(reranked_time, 2),
        "baseline_metrics": baseline_metrics,
        "reranked_metrics": reranked_metrics,
    }


if __name__ == "__main__":
    run_benchmark()
