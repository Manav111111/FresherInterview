import asyncio
import logging
import os
import sys
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.kb_loader import kb_loader
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fresherai.ingest_kb")


async def run_ingestion(batch_size: int = 50, recreate_collection: bool = False):
    print("=" * 70)
    print("FRESHER.AI -- KNOWLEDGE BASE INGESTION PIPELINE")
    print(f"Embedding Provider : {settings.EMBEDDING_PROVIDER}")
    print(f"Embedding Model    : {settings.EMBEDDING_MODEL}")
    print(f"Vector Dimension   : {settings.EMBEDDING_DIMENSION}")
    print(f"Qdrant Collection  : {settings.QDRANT_KB_COLLECTION}")
    print(f"Qdrant URL         : {settings.QDRANT_URL}")
    print("=" * 70)

    start_time = time.time()

    # 1. Load canonical KB records
    print("\n[1/5] Loading and validating fresher_ai_kb records...")
    records = kb_loader.load_ingestion_payloads()
    print(f"  ✓ Loaded {len(records)} canonical records from fresher_ai_kb.")

    # 2. Ensure Qdrant collection exists with verified dimension
    print("\n[2/5] Connecting to Qdrant and verifying collection schema...")
    qdrant_service.ensure_collection(recreate_if_dimension_mismatch=recreate_collection)
    print(f"  ✓ Qdrant collection '{settings.QDRANT_KB_COLLECTION}' ready.")

    # 3. Generate embeddings in batches
    print("\n[3/5] Generating semantic embeddings for KB records with Gemini API...")
    print("  [STRICT MODE] Fallback embeddings disabled (allow_fallback=False).")
    all_points = []
    stats = {
        "Roles": 0,
        "Skills": 0,
        "Resources": 0,
        "YouTube Channels / Playlists": 0,
        "Projects": 0,
        "Interview Questions": 0,
        "Roadmap Records": 0,
        "Tools": 0,
        "Other": 0,
    }

    # Extract all embedding texts
    texts = [r["embedding_text"] for r in records]
    print(f"  Computing live Gemini embeddings for {len(texts)} items (batch size: {batch_size})...")

    embeddings = await embedding_service.get_embeddings_batch(
        texts, batch_size=batch_size, allow_fallback=False
    )
    print(f"  ✓ Successfully computed {len(embeddings)} live Gemini vectors.")
    print(f"  ✓ Live API calls: {embedding_service.live_call_count} | Fallbacks: {embedding_service.fallback_count} | Failures: {embedding_service.failure_count}")

    # 4. Prepare points and calculate statistics
    print("\n[4/5] Preparing vectors and metadata payloads for Qdrant...")
    for record, vec in zip(records, embeddings):
        entity = record.get("entity_type", "Other")
        if entity == "Roles":
            stats["Roles"] += 1
        elif entity in ("Skills", "Foundation"):
            stats["Skills"] += 1
        elif entity in ("Resources", "resources"):
            stats["Resources"] += 1
        elif entity in ("YouTube_Channels", "Playlist", "playlists"):
            stats["YouTube Channels / Playlists"] += 1
        elif entity in ("Projects", "projects"):
            stats["Projects"] += 1
        elif entity in ("Interview_Questions", "interview_prep"):
            stats["Interview Questions"] += 1
        elif entity in ("Weekly_Roadmaps", "roadmaps"):
            stats["Roadmap Records"] += 1
        elif entity in ("Tools_Platforms", "tools"):
            stats["Tools"] += 1
        else:
            stats["Other"] += 1

        payload = dict(record.get("payload", {}))
        payload["entity_type"] = entity
        payload["id"] = record["id"]

        all_points.append({
            "id": record["id"],
            "vector": vec,
            "payload": payload,
        })

    # 5. Batch upsert into Qdrant
    print(f"\n[5/5] Upserting {len(all_points)} vectors into Qdrant collection '{settings.QDRANT_KB_COLLECTION}'...")
    total_upserted = qdrant_service.upsert_points(all_points, batch_size=batch_size)

    elapsed = round(time.time() - start_time, 2)

    # Print final summary
    print("\n" + "=" * 70)
    print("[SUCCESS] KB INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Roles                       : {stats['Roles']}")
    print(f"Skills                      : {stats['Skills']}")
    print(f"Resources                   : {stats['Resources']}")
    print(f"YouTube channels / Playlists: {stats['YouTube Channels / Playlists']}")
    print(f"Projects                    : {stats['Projects']}")
    print(f"Interview Questions         : {stats['Interview Questions']}")
    print(f"Roadmap records             : {stats['Roadmap Records']}")
    print(f"Tools & Platforms           : {stats['Tools']}")
    if stats['Other'] > 0:
        print(f"Other Entities              : {stats['Other']}")
    print(f"Total Vectors Ingested      : {total_upserted}")
    print(f"Live Gemini API Count       : {embedding_service.live_call_count}")
    print(f"Fallback Vectors Used       : {embedding_service.fallback_count}")
    print(f"Embedding Failures          : {embedding_service.failure_count}")
    print(f"Elapsed Time                : {elapsed}s")
    print("=" * 70 + "\n")

    return total_upserted, stats


if __name__ == "__main__":
    recreate = "--recreate" in sys.argv
    asyncio.run(run_ingestion(batch_size=50, recreate_collection=recreate))
