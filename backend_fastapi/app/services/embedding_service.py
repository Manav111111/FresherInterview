import hashlib
import logging
import math
import re
import time
from typing import List, Optional
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

    async def get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generates a single embedding vector for the provided text.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned_text = text.strip()

        if not self._is_api_key_valid():
            logger.debug("Gemini API key not configured/invalid. Using deterministic fallback embedding.")
            return self._generate_fallback_embedding(cleaned_text)

        url = f"{self.base_url}/{self.model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": cleaned_text}]
            },
            "outputDimensionality": self.dimension,
        }

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        values = data.get("embedding", {}).get("values", [])
                        if len(values) == self.dimension:
                            return values
                        elif len(values) > self.dimension:
                            return values[: self.dimension]
                        elif len(values) > 0:
                            # Pad if necessary
                            return values + [0.0] * (self.dimension - len(values))
                    elif resp.status_code in (400, 401, 403):
                        # Client / key error - disable live API calls and switch to deterministic fallback
                        self._api_disabled = True
                        logger.warning(
                            f"Gemini embedding API returned status {resp.status_code} (Auth/Invalid Key). "
                            "Switching to deterministic vector fallback for remaining items."
                        )
                        return self._generate_fallback_embedding(cleaned_text)
                    else:
                        logger.warning(
                            f"Gemini embedding transient error (status {resp.status_code}, attempt {attempt}/{max_retries})"
                        )
            except Exception as exc:
                logger.warning(f"Gemini embedding network exception on attempt {attempt}: {exc}")

            if attempt < max_retries:
                time.sleep(0.5 * attempt)

        # If all retries exhausted, safely fall back
        return self._generate_fallback_embedding(cleaned_text)

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 20,
    ) -> List[List[float]]:
        """
        Generates embeddings for a list of texts in controlled batches.
        """
        if not texts:
            return []

        results: List[List[float]] = []

        # If API key is not valid, compute fallbacks immediately
        if not self._is_api_key_valid():
            return [self._generate_fallback_embedding(t) for t in texts]

        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            # Process chunk
            chunk_vectors = []
            for item_text in chunk:
                vec = await self.get_embedding(item_text)
                chunk_vectors.append(vec)
            results.extend(chunk_vectors)

        return results

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
