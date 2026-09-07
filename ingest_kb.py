"""
Root launcher for Fresher.AI Knowledge Base Ingestion Pipeline.
"""
import os
import sys

# Ensure backend_fastapi is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend_fastapi")
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import asyncio
    from ingest_kb import run_ingestion
    recreate = "--recreate" in sys.argv
    asyncio.run(run_ingestion(batch_size=50, recreate_collection=recreate))
