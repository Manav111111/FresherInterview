"""
Fresher.AI — Deterministic RAG Retrieval Evaluation Suite
Calculates industry-standard retrieval metrics:
- Recall@K
- Precision@K
- Mean Reciprocal Rank (MRR@K)
- Normalized Discounted Cumulative Gain (NDCG@K)

Compares baseline Stage 1 vector retrieval vs Stage 2 reranked retrieval across the curated evaluation dataset.
"""

import math
from typing import Dict, List, Set, Tuple, Any


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Computes Recall@K: fraction of relevant documents retrieved in top-K.
    Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|
    """
    if not relevant_ids:
        return 0.0
    top_k_retrieved = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    return hits / float(len(relevant_ids))


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Computes Precision@K: fraction of top-K retrieved documents that are relevant.
    Precision@K = |Retrieved@K ∩ Relevant| / K
    """
    if k <= 0:
        return 0.0
    top_k_retrieved = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    return hits / float(k)


def reciprocal_rank_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Computes Reciprocal Rank (RR@K): 1 / (rank of first relevant document) if within top-K, else 0.
    """
    top_k_retrieved = retrieved_ids[:k]
    for rank, doc_id in enumerate(top_k_retrieved, start=1):
        if doc_id in relevant_ids:
            return 1.0 / float(rank)
    return 0.0


def dcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Computes Discounted Cumulative Gain (DCG@K) using binary relevance (1 or 0).
    DCG@K = sum_{i=1}^K (rel_i / log2(i + 1))
    """
    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        dcg += rel / math.log2(rank + 1)
    return dcg


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Computes Normalized Discounted Cumulative Gain (NDCG@K).
    NDCG@K = DCG@K / IDCG@K
    """
    if not relevant_ids:
        return 0.0
    dcg = dcg_at_k(retrieved_ids, relevant_ids, k)
    # Ideal DCG: all relevant documents appear at the very top
    ideal_k = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_k + 1))
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


class RetrievalEvaluator:
    """
    Evaluates retrieval systems across a dataset of query-relevance pairs.
    Produces comprehensive aggregate metrics across multiple K cutoffs.
    """

    def __init__(self, k_values: List[int] = None):
        self.k_values = k_values or [1, 3, 5, 10]

    def evaluate_dataset(
        self,
        dataset: List[Dict[str, Any]],
        retriever_func: Any,
    ) -> Dict[str, float]:
        """
        Executes evaluation for each query in the dataset using the provided retriever function.
        retriever_func(query: str, max_k: int) -> List[str] (list of retrieved document/question IDs).
        """
        max_k = max(self.k_values)
        totals: Dict[str, float] = {}
        for k in self.k_values:
            totals[f"recall@{k}"] = 0.0
            totals[f"precision@{k}"] = 0.0
            totals[f"mrr@{k}"] = 0.0
            totals[f"ndcg@{k}"] = 0.0

        n = len(dataset)
        if n == 0:
            return totals

        for item in dataset:
            query = item["query"]
            relevant_ids = set(item.get("relevant_ids", []))
            retrieved_ids = retriever_func(query, max_k)

            for k in self.k_values:
                totals[f"recall@{k}"] += recall_at_k(retrieved_ids, relevant_ids, k)
                totals[f"precision@{k}"] += precision_at_k(retrieved_ids, relevant_ids, k)
                totals[f"mrr@{k}"] += reciprocal_rank_at_k(retrieved_ids, relevant_ids, k)
                totals[f"ndcg@{k}"] += ndcg_at_k(retrieved_ids, relevant_ids, k)

        # Average across dataset
        results = {metric: round(val / float(n), 4) for metric, val in totals.items()}
        return results
