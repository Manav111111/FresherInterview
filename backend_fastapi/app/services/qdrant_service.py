import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Union
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config import settings

logger = logging.getLogger("fresherai.qdrant")


class QdrantService:
    """
    Dedicated Qdrant Vector Database service for Fresher.AI knowledge base.
    Manages client connection, collection lifecycle, schema dimension validation,
    payload indexing, batch upserts, and filtered semantic vector search.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.url = url or settings.QDRANT_URL or "http://localhost:6333"
        self.api_key = api_key or (settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None)
        self.collection_name = collection_name or settings.QDRANT_KB_COLLECTION or "fresher_ai_knowledge"
        self.dimension = dimension or settings.EMBEDDING_DIMENSION or 768
        self._client: Optional[QdrantClient] = None
        self._is_in_memory: bool = False

    def get_client(self) -> QdrantClient:
        """
        Lazily initializes and returns the Qdrant client.
        Supports remote HTTP(S), Qdrant Cloud, local embedded storage, or in-memory fallback.
        """
        if self._client is not None:
            return self._client

        # Check for in-memory or local path specification
        if self.url == ":memory:":
            logger.info("Initializing Qdrant in-memory client.")
            self._client = QdrantClient(location=":memory:")
            self._is_in_memory = True
            return self._client

        try:
            # Attempt connection to configured QDRANT_URL
            client = QdrantClient(url=self.url, api_key=self.api_key, timeout=5.0)
            # Ping by listing collections to verify live network connectivity
            client.get_collections()
            self._client = client
            self._is_in_memory = False
            logger.info(f"Connected to Qdrant at {self.url}")
            return self._client
        except Exception as e:
            logger.warning(
                f"Could not connect to Qdrant at {self.url} ({e}). "
                "Falling back to local persistent Qdrant storage."
            )
            local_storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "qdrant_local")
            os.makedirs(local_storage_path, exist_ok=True)
            try:
                self._client = QdrantClient(path=local_storage_path)
                self._is_in_memory = True
                return self._client
            except Exception as lock_err:
                logger.warning(f"Local Qdrant storage lock notice ({lock_err}). Using in-memory client.")
                self._client = QdrantClient(location=":memory:")
                self._is_in_memory = True
                return self._client

    def ensure_collection(self, recreate_if_dimension_mismatch: bool = False) -> bool:
        """
        Ensures the collection exists with the exact configured embedding dimension.
        Raises ValueError if existing collection dimension conflicts with configured dimension.
        """
        client = self.get_client()

        try:
            collections = client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking Qdrant collections: {e}")
            return False

        if exists:
            # Validate collection dimension
            try:
                info = client.get_collection(collection_name=self.collection_name)
                # Vectors config can be VectorParams or a dict of VectorParams
                vectors_cfg = info.config.params.vectors
                existing_dim: Optional[int] = None

                if isinstance(vectors_cfg, models.VectorParams):
                    existing_dim = vectors_cfg.size
                elif isinstance(vectors_cfg, dict):
                    # Multi-vector config
                    first_val = next(iter(vectors_cfg.values()), None)
                    if first_val and hasattr(first_val, "size"):
                        existing_dim = first_val.size

                if existing_dim and existing_dim != self.dimension:
                    msg = (
                        f"Qdrant collection '{self.collection_name}' has vector dimension {existing_dim}, "
                        f"but configured EMBEDDING_DIMENSION is {self.dimension}!"
                    )
                    if recreate_if_dimension_mismatch:
                        logger.warning(f"{msg} Recreating collection as requested.")
                        client.delete_collection(self.collection_name)
                    else:
                        logger.error(msg)
                        raise ValueError(msg)
                else:
                    logger.info(f"Collection '{self.collection_name}' verified with dimension {self.dimension}.")
                    return True
            except ValueError:
                raise
            except Exception as e:
                logger.warning(f"Notice while inspecting collection info: {e}")

        # Create collection
        logger.info(f"Creating collection '{self.collection_name}' with dimension {self.dimension}...")
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.dimension,
                distance=models.Distance.COSINE,
            ),
        )

        # Create payload indexes for frequent filtering fields
        index_fields = [
            ("entity_type", models.PayloadSchemaType.KEYWORD),
            ("role_ids", models.PayloadSchemaType.KEYWORD),
            ("skill_ids", models.PayloadSchemaType.KEYWORD),
            ("difficulty", models.PayloadSchemaType.KEYWORD),
            ("category", models.PayloadSchemaType.KEYWORD),
        ]
        for field_name, field_type in index_fields:
            try:
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception as idx_err:
                logger.debug(f"Payload index for '{field_name}' notice: {idx_err}")

        return True

    def upsert_points(
        self,
        points: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """
        Upserts vector points into Qdrant.
        Each point dict should have:
        - "id": UUID string or integer
        - "vector": List[float]
        - "payload": Dict[str, Any]
        """
        if not points:
            return 0

        client = self.get_client()
        self.ensure_collection()

        qdrant_points: List[models.PointStruct] = []
        for p in points:
            pid = p.get("id")
            # Ensure valid Qdrant ID (UUID string or positive int)
            if isinstance(pid, str):
                try:
                    uuid_obj = uuid.UUID(pid)
                    valid_id = str(uuid_obj)
                except ValueError:
                    # Generate deterministic UUID from custom string ID
                    valid_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, pid))
            elif isinstance(pid, int) and pid > 0:
                valid_id = pid
            else:
                valid_id = str(uuid.uuid4())

            qdrant_points.append(
                models.PointStruct(
                    id=valid_id,
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
            )

        total_upserted = 0
        for i in range(0, len(qdrant_points), batch_size):
            chunk = qdrant_points[i : i + batch_size]
            client.upsert(
                collection_name=self.collection_name,
                points=chunk,
                wait=True,
            )
            total_upserted += len(chunk)

        logger.info(f"Upserted {total_upserted} vectors into '{self.collection_name}'.")
        return total_upserted

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        entity_type: Optional[Union[str, List[str]]] = None,
        role_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Executes filtered semantic similarity search in Qdrant.
        """
        client = self.get_client()

        must_conditions = []

        if entity_type:
            if isinstance(entity_type, list):
                must_conditions.append(
                    models.FieldCondition(
                        key="entity_type",
                        match=models.MatchAny(any=entity_type),
                    )
                )
            else:
                must_conditions.append(
                    models.FieldCondition(
                        key="entity_type",
                        match=models.MatchValue(value=entity_type),
                    )
                )

        if role_id:
            must_conditions.append(
                models.FieldCondition(
                    key="role_ids",
                    match=models.MatchValue(value=role_id),
                )
            )

        if skill_id:
            must_conditions.append(
                models.FieldCondition(
                    key="skill_ids",
                    match=models.MatchValue(value=skill_id),
                )
            )

        if difficulty:
            must_conditions.append(
                models.FieldCondition(
                    key="difficulty",
                    match=models.MatchValue(value=difficulty),
                )
            )

        query_filter = models.Filter(must=must_conditions) if must_conditions else None

        try:
            # Query Qdrant
            hits = client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold if score_threshold > 0 else None,
            ).points

            results = []
            for hit in hits:
                results.append({
                    "id": str(hit.id),
                    "score": round(float(hit.score), 4),
                    "payload": hit.payload or {},
                })
            return results
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []

    def seed_collection_if_empty(self) -> int:
        """Seeds collection with canonical KB points if empty."""
        try:
            client = self.get_client()
            try:
                info = client.get_collection(self.collection_name)
                if info.points_count and info.points_count > 0:
                    return info.points_count
            except Exception:
                pass

            from app.services.kb_loader import kb_loader
            from app.services.embedding_service import embedding_service
            records = kb_loader.load_ingestion_payloads()
            points = []
            for r in records:
                vec = embedding_service._generate_fallback_embedding(r.get("embedding_text", ""))
                points.append({
                    "id": r["id"],
                    "vector": vec,
                    "payload": r["payload"],
                })
            upserted = self.upsert_points(points, batch_size=100)
            logger.info(f"Auto-seeded {upserted} canonical KB points into Qdrant collection '{self.collection_name}'.")
            return upserted
        except Exception as e:
            logger.warning(f"Notice auto-seeding Qdrant collection: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection points count, status, and configuration."""
        client = self.get_client()
        self.ensure_collection()
        try:
            info = client.get_collection(self.collection_name)
            pts = info.points_count or 0
            if pts == 0:
                pts = self.seed_collection_if_empty()
            return {
                "collection": self.collection_name,
                "status": str(info.status),
                "points_count": pts,
                "dimension": self.dimension,
                "in_memory": self._is_in_memory,
            }
        except Exception as e:
            return {
                "collection": self.collection_name,
                "status": "error",
                "points_count": 0,
                "dimension": self.dimension,
                "error": str(e),
            }


# Global singleton instance
qdrant_service = QdrantService()
