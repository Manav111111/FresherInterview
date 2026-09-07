import asyncio
import os
import sys
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.config import settings
from app.core.redis import get_cache, set_cache, get_redis
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.kb_loader import kb_loader
from app.services.skill_gap_engine import skill_gap_engine
from app.services.retrieval_service import retrieval_service
from app.agents.roadmap_agent import generate_roadmap
from app.agents.resume_agent import analyze_resume_text


async def run_validation():
    print("=" * 70)
    print("🔍 FRESHER.AI MASTER SYSTEM VALIDATION SUITE")
    print("=" * 70)

    results = []

    def report(num: int, name: str, passed: bool, detail: str = ""):
        status_text = "PASS" if passed else "FAIL"
        dots = "." * (30 - len(name))
        print(f"[{num:02d}/12] {name} {dots} {status_text}  {detail}")
        results.append((name, passed, detail))

    # [1] Environment Configuration
    try:
        has_models = bool(settings.EMBEDDING_MODEL and settings.LLM_MODEL)
        has_dim = settings.EMBEDDING_DIMENSION == 768
        report(1, "Environment Config", has_models and has_dim, f"Model: {settings.EMBEDDING_MODEL}, Dim: {settings.EMBEDDING_DIMENSION}")
    except Exception as e:
        report(1, "Environment Config", False, str(e))

    # [2] Embedding Service
    try:
        sample_vec = await embedding_service.get_embedding("Full Stack Developer React FastAPI")
        valid_vec = len(sample_vec) == settings.EMBEDDING_DIMENSION
        report(2, "Embedding Generation", valid_vec, f"Vector size: {len(sample_vec)}")
    except Exception as e:
        report(2, "Embedding Generation", False, str(e))

    # [3] Qdrant Connection
    try:
        client = qdrant_service.get_client()
        report(3, "Qdrant Connection", client is not None, f"Collection: {settings.QDRANT_KB_COLLECTION}")
    except Exception as e:
        report(3, "Qdrant Connection", False, str(e))

    # [4] Collection & Vector Dimension
    try:
        q_stats = qdrant_service.get_stats()
        correct_dim = q_stats.get("dimension") == settings.EMBEDDING_DIMENSION
        pts = q_stats.get("points_count", 0)
        report(4, "Vector Dimension & Count", correct_dim and pts > 0, f"Points: {pts}, Dim: {q_stats.get('dimension')}")
    except Exception as e:
        report(4, "Vector Dimension & Count", False, str(e))

    # [5] Semantic Search
    try:
        res = await retrieval_service.search_resources(skill="React", role="Full Stack Developer", top_k=2)
        has_res = len(res) > 0 and bool(res[0].get("url"))
        report(5, "Semantic Search", has_res, f"Retrieved {len(res)} resources (Top: {res[0].get('title') if res else 'None'})")
    except Exception as e:
        report(5, "Semantic Search", False, str(e))

    # [6] Metadata Filtering (YouTube Channels & Playlists)
    try:
        yt = await retrieval_service.search_youtube(skill="Python", top_k=2)
        has_yt = len(yt) > 0 and bool(yt[0].get("url"))
        report(6, "Metadata Filtering (YouTube)", has_yt, f"Found {len(yt)} playlists (Channel: {yt[0].get('channel_name') if yt else 'None'})")
    except Exception as e:
        report(6, "Metadata Filtering (YouTube)", False, str(e))

    # [7] Skill Normalization
    try:
        norm_react = skill_gap_engine.normalize_skill_name("ReactJS") == "React"
        norm_mongo = skill_gap_engine.normalize_skill_name("Mongo") == "MongoDB"
        norm_fastapi = skill_gap_engine.normalize_skill_name("Fast API") == "FastAPI"
        all_norm = norm_react and norm_mongo and norm_fastapi
        report(7, "Skill Normalization", all_norm, "Mapped ReactJS->React, Mongo->MongoDB, Fast API->FastAPI")
    except Exception as e:
        report(7, "Skill Normalization", False, str(e))

    # [8] Skill Gap Engine
    try:
        gap = skill_gap_engine.calculate_skill_gap(
            target_role="AI Engineer",
            candidate_skills=["Python", "FastAPI", "SQL"],
        )
        strong = [s["name"] for s in gap.get("strong_skills", [])]
        missing = [s["name"] for s in gap.get("missing_skills", [])]
        has_strong = "Python" in strong
        has_missing = any(x in missing for x in ["RAG", "Embeddings", "Vector Search", "AI Agents", "LangGraph"])
        report(8, "Skill Gap Engine", has_strong and has_missing, f"Strong: {len(strong)}, Missing: {len(missing)}, Score: {gap.get('readiness_score')}%")
    except Exception as e:
        report(8, "Skill Gap Engine", False, str(e))

    # [9] Roadmap RAG Generation (Off vs On)
    try:
        # Off: role-based
        rm_off = await generate_roadmap(role="Backend Developer", target_package="12 LPA", use_resume=False)
        # On: resume-aware
        rm_on = await generate_roadmap(
            role="AI Engineer",
            target_package="20 LPA",
            use_resume=True,
            resume={"skills": ["Python", "FastAPI"], "summary": "Python Developer"},
        )
        has_modules = len(rm_off.get("modules", [])) >= 3 and len(rm_on.get("modules", [])) >= 3
        has_urls = bool(rm_on["modules"][0].get("videoUrl") or rm_on["modules"][0].get("youtube"))
        report(9, "Roadmap RAG Generation", has_modules and has_urls, f"Modules generated: {len(rm_on.get('modules', []))}, Grounded: {has_urls}")
    except Exception as e:
        report(9, "Roadmap RAG Generation", False, str(e))

    # [10] Resume RAG Analysis
    try:
        resume_sample = "Jane Doe\nPython Developer with experience in FastAPI, React, SQL, and Docker.\nBuilt web APIs."
        parsed_resume = await analyze_resume_text(resume_sample, target_role="Full Stack Developer")
        has_skills = len(parsed_resume.get("skills", [])) >= 2
        has_bullets = len(parsed_resume.get("bulletImprovements", [])) >= 1
        report(10, "Resume RAG Analysis", has_skills and has_bullets, f"Skills: {len(parsed_resume.get('skills', []))}, Score: {parsed_resume.get('score')}")
    except Exception as e:
        report(10, "Resume RAG Analysis", False, str(e))

    # [11] Redis Cache Read/Write
    try:
        test_key = "test_val_validation_rag"
        await set_cache(test_key, "fresherai_cached_ok", ex=10)
        val = await get_cache(test_key)
        report(11, "Redis Caching", val == "fresherai_cached_ok", "Cache write & read verified (or in-memory session)")
    except Exception as e:
        report(11, "Redis Caching", False, str(e))

    # [12] API Health Endpoints
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        h_resp = client.get("/health")
        d_resp = client.get("/health/dependencies")
        api_h_resp = client.get("/api/health")
        all_ok = h_resp.status_code == 200 and d_resp.status_code == 200 and api_h_resp.status_code == 200
        report(12, "API Health Endpoints", all_ok, f"/health: {h_resp.status_code}, /health/dependencies: {d_resp.status_code}")
    except Exception as e:
        report(12, "API Health Endpoints", False, str(e))

    # Final Summary
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print("\n" + "=" * 70)
    print(f"VALIDATION SUMMARY: {passed_count}/{total_count} CHECKS PASSED")
    print("=" * 70 + "\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)
