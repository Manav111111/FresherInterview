"""
Root launcher for Fresher.AI Master System Validation Suite.
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend_fastapi")
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import asyncio
    from validate_rag import run_validation
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)
