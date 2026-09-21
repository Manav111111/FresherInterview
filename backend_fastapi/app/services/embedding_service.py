import asyncio
import hashlib
import json
import logging
import math
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger("fresherai.embedding")


class EmbeddingService:
    """
    Production embedding service supporting Gemini Embedding 2 with configurable
    model and dimensions (default 768). Handles batching, transient retries,
    and a deterministic fallback vector generator for offline/test environments.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL or "gemini-embedding-2"
        self.dimension = dimension or settings.EMBEDDING_DIMENSION or 768
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._api_disabled: bool = False
        self.live_call_count: int = 0
        self.fallback_count: int = 0
        self.failure_count: int = 0

    def _is_api_key_valid(self) -> bool:
        if self._api_disabled:
            return False
        if not self.api_key or len(self.api_key) < 15:
            return False
        if "placeholder" in self.api_key.lower() or "your_" in self.api_key.lower():
            return False
        return True

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, pseudo-semantic normalized unit vector of configured dimension
        using cryptographic hashing of token n-grams. Used when Gemini API is unreachable or in tests.
        """
        self.fallback_count += 1
        dim = self.dimension
        vector = [0.0] * dim

        # Extract words/tokens
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            tokens = ["empty"]

        for idx, token in enumerate(tokens):
            h = int(hashlib.sha256(f"{token}:{idx % 10}".encode("utf-8")).hexdigest()[:8], 16)
            slot = h % dim
            vector[slot] += 1.0 + (1.0 / (idx + 1))

        # Also hash full string for global context
        full_hash = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
        vector[full_hash % dim] += 2.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    async def get_embedding(
        self,
        text: str,
        max_retries: int = 3,
        allow_fallback: bool = True,
    ) -> List[float]:
        """
        Generates a single embedding vector for the provided text.
        If allow_fallback is False, raises RuntimeError on failure instead of generating hash vectors.
        """
        import time
        from app.core.telemetry import telemetry

        start_time = time.perf_counter()
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned_text = text.strip()

        if not self._is_api_key_valid():
            if not allow_fallback:
                self.failure_count += 1
                raise RuntimeError(
                    f"Gemini API key is invalid or API is disabled (disabled={self._api_disabled}), "
                    "and fallback embeddings are disallowed."
                )
            logger.debug("Gemini API key not configured/invalid. Using deterministic fallback embedding.")
            vec = self._generate_fallback_embedding(cleaned_text)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            telemetry.log_embedding_event(self.model, self.dimension, duration_ms, item_count=1, is_fallback=True)
            return vec

        url = f"{self.base_url}/{self.model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": cleaned_text}]
            },
            "outputDimensionality": self.dimension,
        }

        last_err: Optional[str] = None
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        values = data.get("embedding", {}).get("values", [])
                        duration_ms = (time.perf_counter() - start_time) * 1000.0
                        telemetry.log_embedding_event(self.model, self.dimension, duration_ms, item_count=1, is_fallback=False)
                        self.live_call_count += 1
                        if len(values) == self.dimension:
                            return values
                        elif len(values) > self.dimension:
                            return values[: self.dimension]
                        elif len(values) > 0:
                            return values + [0.0] * (self.dimension - len(values))
                    elif resp.status_code in (400, 401, 403):
                        self._api_disabled = True
                        last_err = f"Status {resp.status_code}: {resp.text[:200]}"
                        logger.warning(
                            f"Gemini embedding API returned status {resp.status_code} (Auth/Invalid Key): {last_err}"
                        )
                        if not allow_fallback:
                            self.failure_count += 1
                            raise RuntimeError(f"Gemini embedding failed with {last_err} and allow_fallback=False.")
                        break
                    else:
                        last_err = f"Status {resp.status_code}"
                        logger.warning(f"Gemini embedding transient error ({last_err}, attempt {attempt}/{max_retries})")
            except Exception as exc:
                last_err = str(exc)
                logger.warning(f"Gemini embedding network exception on attempt {attempt}: {exc}")

            if attempt < max_retries:
                await asyncio.sleep(0.5 * attempt)

        # Retries exhausted
        if not allow_fallback:
            self.failure_count += 1
            raise RuntimeError(f"Gemini embedding failed after {max_retries} attempts: {last_err}")

        vec = self._generate_fallback_embedding(cleaned_text)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        telemetry.log_embedding_event(self.model, self.dimension, duration_ms, item_count=1, is_fallback=True)
        return vec

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 50,
        allow_fallback: bool = True,
    ) -> List[List[float]]:
        """
        Generates embeddings for a list of texts in controlled batches using batchEmbedContents.
        If allow_fallback is False, raises RuntimeError on failure and does not produce hash vectors.
        """
        if not texts:
            return []

        if not self._is_api_key_valid():
            if not allow_fallback:
                self.failure_count += len(texts)
                raise RuntimeError(
                    f"Gemini API key is invalid/disabled and fallback is disallowed (allow_fallback=False)."
                )
            return [self._generate_fallback_embedding(t) for t in texts]

    def _get_cache_path(self) -> Path:
        p = Path(__file__).resolve().parent.parent / "data" / "gemini_embedding_cache.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _load_cache(self) -> Dict[str, List[float]]:
        p = self._get_cache_path()
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache: Dict[str, List[float]]):
        p = self._get_cache_path()
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception as e:
            logger.warning(f"Could not save embedding cache: {e}")

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 50,
        allow_fallback: bool = True,
    ) -> List[List[float]]:
        """
        Generates embeddings for a list of texts in controlled batches using batchEmbedContents.
        Utilizes persistent local disk caching, 429 rate limit backoff, and pacing.
        If allow_fallback is False, raises RuntimeError on failure and does not produce hash vectors.
        """
        if not texts:
            return []

        if not self._is_api_key_valid():
            if not allow_fallback:
                self.failure_count += len(texts)
                raise RuntimeError(
                    f"Gemini API key is invalid/disabled and fallback is disallowed (allow_fallback=False)."
                )
            return [self._generate_fallback_embedding(t) for t in texts]

        # Check persistent cache first
        cache = self._load_cache()
        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []

        for idx, t in enumerate(texts):
            clean = t.strip() if t and t.strip() else "empty"
            cache_key = hashlib.sha256(f"{self.model}:{self.dimension}:{clean}".encode("utf-8")).hexdigest()
            if cache_key in cache:
                results[idx] = cache[cache_key]
            else:
                uncached_indices.append(idx)

        cached_count = len(texts) - len(uncached_indices)
        if cached_count > 0:
            logger.info(f"Embedding cache hit: {cached_count}/{len(texts)} already cached.")
            print(f"  ✓ Reused {cached_count}/{len(texts)} vectors from persistent local cache.")

        if not uncached_indices:
            return [vec for vec in results if vec is not None]

        url = f"{self.base_url}/{self.model}:batchEmbedContents?key={self.api_key}"

        # Process uncached items in batches
        for i in range(0, len(uncached_indices), batch_size):
            chunk_indices = uncached_indices[i : i + batch_size]
            chunk_texts = [texts[idx] for idx in chunk_indices]

            requests_payload = []
            for t in chunk_texts:
                clean = t.strip() if t and t.strip() else "empty"
                requests_payload.append({
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": clean}]},
                    "outputDimensionality": self.dimension,
                })

            chunk_embedded = False
            last_err: Optional[str] = None
            max_attempts = 10
            for attempt in range(1, max_attempts + 1):
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(url, json={"requests": requests_payload})
                        if resp.status_code == 200:
                            data = resp.json()
                            embeddings_data = data.get("embeddings", [])
                            for emb_idx, emb in enumerate(embeddings_data):
                                vals = emb.get("values", [])
                                if len(vals) == self.dimension:
                                    final_vec = vals
                                elif len(vals) > self.dimension:
                                    final_vec = vals[: self.dimension]
                                else:
                                    final_vec = vals + [0.0] * (self.dimension - len(vals))

                                orig_idx = chunk_indices[emb_idx]
                                results[orig_idx] = final_vec

                                # Store in persistent cache
                                clean = texts[orig_idx].strip() if texts[orig_idx] and texts[orig_idx].strip() else "empty"
                                cache_key = hashlib.sha256(f"{self.model}:{self.dimension}:{clean}".encode("utf-8")).hexdigest()
                                cache[cache_key] = final_vec

                            self._save_cache(cache)
                            chunk_embedded = True
                            self.live_call_count += len(chunk_indices)
                            print(f"  ✓ Live batch ({i + len(chunk_indices)}/{len(uncached_indices)}) embedded successfully.")
                            break
                        elif resp.status_code == 429:
                            # Rate limit hit — exponential backoff
                            retry_header = resp.headers.get("retry-after")
                            wait_time = float(retry_header) if retry_header and retry_header.isdigit() else max(20.0, 10.0 * attempt)
                            last_err = f"Status 429 Rate Limit (waited {wait_time:.1f}s)"
                            logger.warning(
                                f"Gemini 429 Rate Limit on batch. Backing off for {wait_time:.1f}s (attempt {attempt}/{max_attempts})..."
                            )
                            print(f"  ⏳ Rate limit backoff: sleeping {wait_time:.1f}s (attempt {attempt}/{max_attempts})...")
                            await asyncio.sleep(wait_time)
                        elif resp.status_code in (400, 401, 403):
                            self._api_disabled = True
                            last_err = f"Status {resp.status_code}: {resp.text[:200]}"
                            logger.warning(
                                f"Gemini batchEmbedContents returned {last_err}. Switching to fallback if allowed."
                            )
                            break
                        else:
                            last_err = f"Status {resp.status_code}"
                            logger.warning(f"Batch embed retry status {resp.status_code} (attempt {attempt}/{max_attempts})")
                            await asyncio.sleep(2.0 * attempt)
                except Exception as exc:
                    last_err = str(exc)
                    logger.warning(f"Batch embed exception on attempt {attempt}: {exc}")
                    await asyncio.sleep(2.0 * attempt)

            if not chunk_embedded:
                if not allow_fallback:
                    self.failure_count += len(chunk_indices)
                    raise RuntimeError(
                        f"Failed to generate live Gemini embeddings for batch chunk of {len(chunk_indices)} items "
                        f"({last_err}) and allow_fallback=False."
                    )
                for idx in chunk_indices:
                    results[idx] = self._generate_fallback_embedding(texts[idx])

            # Pacing delay between live API batches to respect 15 RPM
            if i + batch_size < len(uncached_indices):
                await asyncio.sleep(5.0)

        return [vec for vec in results if vec is not None]

    @staticmethod
    def build_semantic_text(
        entity_type: str,
        title: str,
        role: Optional[str] = None,
        skill: Optional[str] = None,
        level: Optional[str] = None,
        description: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Builds standardized, rich semantic context for embeddings rather than only embedding a title.
        """
        parts = [f"Entity: {entity_type}"]
        if title:
            parts.append(f"Title: {title}")
        if role:
            parts.append(f"Role: {role}")
        if skill:
            parts.append(f"Skill: {skill}")
        if level:
            parts.append(f"Level: {level}")
        if description:
            parts.append(f"Description: {description}")
        if extra_context:
            parts.append(f"Context: {extra_context}")
        return "\n".join(parts)


# Global singleton instance
embedding_service = EmbeddingService()
