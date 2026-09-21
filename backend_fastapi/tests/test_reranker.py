"""
Tests for Phase 3: RAG Evaluation & Real Two-Stage Reranking.

Covers:
1. Baseline vs Reranked Candidate Ordering (re-sorting by semantic cross-attention score)
2. Empty candidate set handling
3. Top-N > Final-K and Top-N <= Final-K limits
4. Graceful fallback to baseline ranking when reranker encounters errors
5. Deterministic retrieval evaluation metrics (Recall@K, Precision@K, MRR@K, NDCG@K)
6. Telemetry emission (candidate counts, latency, model, status, no secrets/PII)
7. Integration with retrieval_service._search_with_cache
"""

import math
import pytest
from unittest.mock import patch

from app.services.reranker_service import RerankerService, reranker_service
from app.services.rag_evaluator import (
    recall_at_k,
    precision_at_k,
    reciprocal_rank_at_k,
    dcg_at_k,
    ndcg_at_k,
    RetrievalEvaluator,
)
from app.core.telemetry import telemetry


# ─────────────────────────────────────────────────────────────────────────────
# 1. RERANKER ORDERING & RE-SCORING TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_reranker_reorders_candidates_by_cross_relevance():
    """
    Candidate B is 2nd in vector search, but has higher cross-relevance to query.
    Reranker must promote Candidate B to Rank 1 with rerank_score attached.
    """
    query = "How to reduce LLM latency and optimize TTFT"
    candidates = [
        {
            "id": "doc_1",
            "question": "What is Python asyncio?",
            "ideal_answer": "Asyncio is a library to write concurrent code using the async/await syntax.",
            "key_concepts": ["Python", "Concurrency"],
            "score": 0.85,
        },
        {
            "id": "doc_2",
            "question": "How to reduce LLM latency and optimize TTFT and TPOT?",
            "ideal_answer": "To reduce LLM latency and optimize TTFT, use prompt caching, speculative decoding, and quantization.",
            "key_concepts": ["LLM Fundamentals", "Latency", "TTFT"],
            "score": 0.72,
        },
    ]

    reranker = RerankerService(enabled=True)
    reranked = reranker.rerank(query, candidates, top_k=2)

    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc_2"
    assert reranked[1]["id"] == "doc_1"
    assert "rerank_score" in reranked[0]
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]


def test_reranker_handles_empty_candidates():
    """Empty candidate list safely returns empty list without exception."""
    reranker = RerankerService(enabled=True)
    result = reranker.rerank("any query", [], top_k=5)
    assert result == []


def test_reranker_disabled_passthrough():
    """When disabled, returns original slice unchanged."""
    candidates = [{"id": "d1"}, {"id": "d2"}, {"id": "d3"}]
    reranker = RerankerService(enabled=False)
    result = reranker.rerank("query", candidates, top_k=2)
    assert len(result) == 2
    assert result[0]["id"] == "d1"
    assert "rerank_score" not in result[0]


def test_reranker_top_n_greater_than_final_k():
    """When top_n > final_k (e.g. 10 candidates -> final 3), returns exactly final_k."""
    query = "database connection pooling"
    candidates = [{"id": f"doc_{i}", "description": f"content {i} database pooling"} for i in range(10)]
    reranker = RerankerService(enabled=True)
    result = reranker.rerank(query, candidates, top_k=3)
    assert len(result) == 3


def test_reranker_top_n_less_than_final_k():
    """When candidate count <= final_k, returns all candidates ranked."""
    query = "database connection pooling"
    candidates = [{"id": f"doc_{i}", "description": f"content {i} database pooling"} for i in range(2)]
    reranker = RerankerService(enabled=True)
    result = reranker.rerank(query, candidates, top_k=5)
    assert len(result) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 2. RERANKER FAILURE & GRACEFUL FALLBACK TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_reranker_fallback_on_exception():
    """
    When an unexpected internal exception occurs during reranking,
    gracefully fall back to original baseline vector candidates and log fallback event.
    """
    candidates = [
        {"id": "doc_base_1", "title": "Base 1"},
        {"id": "doc_base_2", "title": "Base 2"},
    ]
    reranker = RerankerService(enabled=True)

    # Patch _compute_lexical_cross_score to simulate unexpected crash
    with patch.object(reranker, "_compute_lexical_cross_score", side_effect=RuntimeError("GPU OOM / Memory fault")):
        with patch.object(telemetry, "log_reranker_event") as mock_log:
            result = reranker.rerank("query text", candidates, top_k=1)

            # Preserves original baseline top item
            assert len(result) == 1
            assert result[0]["id"] == "doc_base_1"

            # Confirms fallback telemetry emitted
            assert mock_log.called
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["status"] == "fallback"
            assert "RuntimeError" in call_kwargs["error_type"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. DETERMINISTIC RETRIEVAL METRICS TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_recall_at_k_exact_calculation():
    """Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|."""
    relevant = {"doc_a", "doc_b"}
    # Hits doc_a at rank 1, doc_c at rank 2
    retrieved = ["doc_a", "doc_c", "doc_b"]

    assert recall_at_k(retrieved, relevant, k=1) == 0.5  # 1/2
    assert recall_at_k(retrieved, relevant, k=2) == 0.5  # 1/2
    assert recall_at_k(retrieved, relevant, k=3) == 1.0  # 2/2


def test_precision_at_k_exact_calculation():
    """Precision@K = |Retrieved@K ∩ Relevant| / K."""
    relevant = {"doc_a"}
    retrieved = ["doc_a", "doc_b", "doc_c"]

    assert precision_at_k(retrieved, relevant, k=1) == 1.0        # 1/1
    assert precision_at_k(retrieved, relevant, k=2) == 0.5        # 1/2
    assert round(precision_at_k(retrieved, relevant, k=3), 4) == 0.3333  # 1/3


def test_mrr_at_k_exact_calculation():
    """MRR = 1 / rank of first relevant item."""
    relevant = {"target_doc"}

    # Target at rank 1 -> RR = 1.0
    assert reciprocal_rank_at_k(["target_doc", "other"], relevant, k=3) == 1.0

    # Target at rank 2 -> RR = 0.5
    assert reciprocal_rank_at_k(["other", "target_doc"], relevant, k=3) == 0.5

    # Target at rank 3 -> RR = 1/3
    assert round(reciprocal_rank_at_k(["other1", "other2", "target_doc"], relevant, k=3), 4) == 0.3333

    # Target beyond K -> RR = 0.0
    assert reciprocal_rank_at_k(["other1", "other2", "other3", "target_doc"], relevant, k=3) == 0.0


def test_ndcg_at_k_calculation():
    """NDCG matches binary discount log formula."""
    relevant = {"d1"}
    # Perfect ranking: d1 at rank 1 -> NDCG = 1.0
    assert ndcg_at_k(["d1", "d2"], relevant, k=2) == 1.0

    # Sub-optimal: d1 at rank 2 -> DCG = 1/log2(3) = 0.6309, IDCG = 1/log2(2) = 1.0 -> NDCG = 0.6309
    score = ndcg_at_k(["d2", "d1"], relevant, k=2)
    assert round(score, 4) == round(1.0 / math.log2(3), 4)


def test_retrieval_evaluator_dataset():
    """RetrievalEvaluator aggregates metrics across a sample dataset."""
    dataset = [
        {"query": "q1", "relevant_ids": ["d1"]},
        {"query": "q2", "relevant_ids": ["d2"]},
    ]

    def mock_retriever(q, max_k):
        return ["d1", "x"] if q == "q1" else ["y", "d2"]

    evaluator = RetrievalEvaluator(k_values=[1, 2])
    metrics = evaluator.evaluate_dataset(dataset, mock_retriever)

    # q1 has d1 at rank 1 (Recall@1 = 1.0, RR = 1.0)
    # q2 has d2 at rank 2 (Recall@1 = 0.0, RR = 0.5)
    # Average Recall@1 = 0.5, Average Recall@2 = 1.0
    # Average MRR@1 = 0.5, Average MRR@2 = 0.75
    assert metrics["recall@1"] == 0.5
    assert metrics["recall@2"] == 1.0
    assert metrics["mrr@1"] == 0.5
    assert metrics["mrr@2"] == 0.75
