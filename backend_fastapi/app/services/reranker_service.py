"""
Fresher.AI — Two-Stage RAG Reranking Service
Implements a dedicated, independent second-stage relevance reranker for retrieved candidates.
Supports:
1. Lexical Cross-Encoder (BM25 + Bi-gram Exact Phrase + Key Concept Intersection with normalized logits)
2. Optional Transformer Cross-Encoder (sentence-transformers CrossEncoder with lazy loading & CPU-safe fallback)
3. Graceful degradation: If reranker encounters any failure, falls back transparently to first-stage Qdrant ranking.
4. Full Phase 2 telemetry integration (latency, candidate counts, model, status, correlation IDs).
"""

import logging
import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.core.telemetry import get_current_request_id, telemetry

logger = logging.getLogger("fresherai.reranker")


class RerankerService:
    """
    Dedicated RAG candidate reranker.
    Takes top-N retrieved candidate documents/questions from Stage 1 (Qdrant semantic vector search)
    and computes an independent cross-attention / relevance score against the query to return final top-K.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        top_n: Optional[int] = None,
        final_k: Optional[int] = None,
    ):
        self.enabled = enabled if enabled is not None else settings.RERANKING_ENABLED
        self.provider = provider or settings.RERANKER_PROVIDER
        self.model_name = model_name or settings.RERANKER_MODEL
        self.top_n = top_n or settings.RERANK_TOP_N
        self.final_k = final_k or settings.RERANK_FINAL_K
        self._cross_encoder_model = None

    def _tokenize(self, text: str) -> List[str]:
        """Simple lowercase tokenization for lexical cross-scoring."""
        return [w for w in re.findall(r"\w+", (text or "").lower()) if len(w) > 1]

    def _extract_document_text(self, doc: Dict[str, Any]) -> str:
        """Extracts the rich evaluable text from candidate documents or questions."""
        payload = doc.get("payload") or doc
        parts = []

        # Question / Interview Bank format
        if "question" in payload:
            parts.append(str(payload.get("question", "")))
        if "ideal_answer" in payload:
            parts.append(str(payload.get("ideal_answer", ""))[:300])
        if "key_concepts" in payload:
            concepts = payload.get("key_concepts", [])
            if isinstance(concepts, list):
                parts.append(" ".join(str(c) for c in concepts))
            else:
                parts.append(str(concepts))
        if "subcategory" in payload:
            parts.append(str(payload.get("subcategory", "")))
        if "domain" in payload:
            parts.append(str(payload.get("domain", "")))

        # Resource / Doc / Tool / Project format
        if "title" in payload:
            parts.append(str(payload.get("title", "")))
        if "description" in payload:
            parts.append(str(payload.get("description", "")))
        if "summary" in payload:
            parts.append(str(payload.get("summary", "")))
        if "topics" in payload:
            topics = payload.get("topics", [])
            parts.append(" ".join(str(t) for t in topics) if isinstance(topics, list) else str(topics))
        if "embedding_text" in payload:
            parts.append(str(payload.get("embedding_text", ""))[:400])

        return " ".join(parts).strip()

    def _compute_lexical_cross_score(self, query: str, doc_text: str, doc: Dict[str, Any]) -> float:
        """
        Computes a fine-grained cross-relevance score between query and document.
        Combines:
        1. BM25-style term saturation (TF / (TF + k1))
        2. Exact phrase and n-gram overlap bonus
        3. Key concept coverage ratio
        4. Normalized cross-relevance logit
        """
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return 0.5

        d_tokens = self._tokenize(doc_text)
        if not d_tokens:
            return 0.0

        d_token_counts: Dict[str, int] = {}
        for t in d_tokens:
            d_token_counts[t] = d_token_counts.get(t, 0) + 1

        # 1. Term Saturation Score (k1 = 1.2)
        k1 = 1.2
        matched_terms = 0
        term_score = 0.0
        for qt in q_tokens:
            tf = d_token_counts.get(qt, 0)
            if tf > 0:
                matched_terms += 1
                term_score += (tf * (k1 + 1)) / (tf + k1)

        token_coverage = matched_terms / len(q_tokens)

        # 2. Bigram / phrase matching bonus
        phrase_bonus = 0.0
        q_clean = query.lower()
        d_clean = doc_text.lower()
        if len(q_tokens) >= 2:
            for i in range(len(q_tokens) - 1):
                bigram = f"{q_tokens[i]} {q_tokens[i+1]}"
                if bigram in d_clean:
                    phrase_bonus += 0.75

        # 3. Exact Substring Match bonus
        if q_clean in d_clean and len(q_clean) > 5:
            phrase_bonus += 1.5

        # 4. Key concepts precision
        payload = doc.get("payload") or doc
        concepts = payload.get("key_concepts", []) or payload.get("skills", [])
        concept_overlap = 0
        if isinstance(concepts, list):
            for c in concepts:
                c_clean = str(c).lower()
                if any(c_clean in qt or qt in c_clean for qt in q_tokens):
                    concept_overlap += 1
        elif isinstance(concepts, str) and concepts:
            if any(qt in concepts.lower() for qt in q_tokens):
                concept_overlap += 1

        # Normalized Composite Relevance Logit
        raw_score = (term_score * 1.5) + (token_coverage * 3.0) + phrase_bonus + (concept_overlap * 1.2)
        # Sigmoid squash to [0.0, 1.0] range
        cross_relevance = 1.0 / (1.0 + math.exp(-raw_score / 3.0))
        return round(cross_relevance, 4)

    def _score_with_cross_encoder_model(
        self,
        query: str,
        pairs: List[Tuple[str, str]],
    ) -> Optional[List[float]]:
        """
        Attempts to score using sentence-transformers CrossEncoder if installed.
        Returns None if model is unavailable.
        """
        try:
            if self._cross_encoder_model is None:
                from sentence_transformers import CrossEncoder
                self._cross_encoder_model = CrossEncoder(self.model_name, max_length=256)
            scores = self._cross_encoder_model.predict(pairs)
            return [float(s) for s in scores]
        except Exception as e:
            logger.debug(f"CrossEncoder model unavailable or failed ({e}), using lexical cross-scoring.")
            return None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        operation: str = "rag_reranking",
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate documents against the query.
        Returns the top-K highest-ranked documents with an updated 'rerank_score'.
        If reranker is disabled or candidates are empty, returns the original slice gracefully.
        """
        k = top_k or self.final_k
        if not candidates:
            return []

        if not self.enabled or self.provider == "none":
            return candidates[:k]

        start_time = time.perf_counter()
        req_id = get_current_request_id()
        candidate_count = len(candidates)

        try:
            doc_texts = [self._extract_document_text(c) for c in candidates]
            scores: Optional[List[float]] = None

            # Attempt neural cross-encoder if configured
            if self.provider == "cross_encoder":
                pairs = [(query, dt) for dt in doc_texts]
                scores = self._score_with_cross_encoder_model(query, pairs)

            # Fall back to lexical cross-encoder
            if scores is None:
                scores = [
                    self._compute_lexical_cross_score(query, doc_texts[i], candidates[i])
                    for i in range(candidate_count)
                ]

            # Attach scores and rank
            scored_candidates = []
            for i, cand in enumerate(candidates):
                item = dict(cand)
                item["rerank_score"] = scores[i]
                scored_candidates.append(item)

            # Sort descending by rerank_score, using original rank as tiebreaker
            scored_candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            final_results = scored_candidates[:k]

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            telemetry.log_reranker_event(
                operation=operation,
                latency_ms=duration_ms,
                candidate_count_before=candidate_count,
                candidate_count_after=len(final_results),
                model=self.model_name if self.provider == "cross_encoder" else "lexical-cross-encoder-v1",
                status="success",
                request_id=req_id,
            )
            return final_results

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Reranker failed ({e}). Gracefully falling back to baseline vector ranking.")
            telemetry.log_reranker_event(
                operation=operation,
                latency_ms=duration_ms,
                candidate_count_before=candidate_count,
                candidate_count_after=len(candidates[:k]),
                model=self.model_name,
                status="fallback",
                error_type=type(e).__name__,
                request_id=req_id,
            )
            # Safe fallback: return baseline top-K
            return candidates[:k]


# Global singleton instance
reranker_service = RerankerService()
