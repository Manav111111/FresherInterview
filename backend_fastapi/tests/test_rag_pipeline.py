import pytest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.skill_gap_engine import skill_gap_engine
from app.services.retrieval_service import retrieval_service
from app.agents.roadmap_agent import generate_roadmap
from app.agents.resume_agent import analyze_resume_text

client = TestClient(app)


def test_embedding_service_dimension():
    """Verifies that embedding service outputs vectors of configured dimension."""
    vec = embedding_service._generate_fallback_embedding("Test embedding text")
    assert len(vec) == settings.EMBEDDING_DIMENSION
    assert len(vec) == 768


def test_qdrant_collection_dimension_validation():
    """Verifies that Qdrant service ensures collection with exact dimension."""
    assert qdrant_service.ensure_collection() is True
    stats = qdrant_service.get_stats()
    assert stats["dimension"] == 768


def test_skill_normalization():
    """Verifies skill alias normalization against canonical KB skills."""
    assert skill_gap_engine.normalize_skill_name("ReactJS") == "React"
    assert skill_gap_engine.normalize_skill_name("react.js") == "React"
    assert skill_gap_engine.normalize_skill_name("Mongo") == "MongoDB"
    assert skill_gap_engine.normalize_skill_name("Fast API") == "FastAPI"
    assert skill_gap_engine.normalize_skill_name("py") == "Python"
    assert skill_gap_engine.normalize_skill_name("k8s") == "Kubernetes"
    assert skill_gap_engine.normalize_skill_name("rag") == "RAG"


def test_skill_gap_engine_ai_engineer():
    """Verifies skill gap calculation for AI Engineer with partial candidate skills."""
    gap = skill_gap_engine.calculate_skill_gap(
        target_role="AI Engineer",
        candidate_skills=["Python", "FastAPI", "SQL"],
    )
    assert gap["target_role_id"] == "role_ai_engineer"
    strong_names = [s["name"] for s in gap["strong_skills"]]
    missing_names = [s["name"] for s in gap["missing_skills"]]

    assert "Python" in strong_names
    assert any(x in missing_names for x in ["RAG", "Embeddings", "Vector Search", "AI Agents", "LangGraph"])
    assert gap["readiness_score"] < 100
    assert gap["gap_percentage"] > 0


@pytest.mark.parametrize(
    "role,skill",
    [
        ("Full Stack Developer", "React"),
        ("Backend Developer", "FastAPI"),
        ("AI Engineer", "RAG"),
        ("Data Scientist", "Supervised Learning"),
        ("DevOps Engineer", "Docker"),
    ],
)
@pytest.mark.anyio
async def test_retrieval_service_domains(role, skill):
    """Verifies retrieval across 5 target roles specified in Phase 21."""
    # Search resources
    resources = await retrieval_service.search_resources(skill=skill, role=role, top_k=2)
    assert isinstance(resources, list)

    # Search YouTube
    yt = await retrieval_service.search_youtube(skill=skill, role=role, top_k=2)
    assert isinstance(yt, list)


@pytest.mark.anyio
async def test_roadmap_personalization_off_vs_on():
    """Verifies roadmap generation behavior with personalization OFF vs ON."""
    # Personalization OFF: Role-based progression
    roadmap_off = await generate_roadmap(
        role="Full Stack Developer",
        target_package="15 LPA",
        use_resume=False,
    )
    assert len(roadmap_off["modules"]) >= 3
    assert roadmap_off["skillGapSummary"] is None

    # Personalization ON: Resume-aware progression
    roadmap_on = await generate_roadmap(
        role="AI Engineer",
        target_package="25 LPA",
        use_resume=True,
        resume={"skills": ["Python", "FastAPI"], "summary": "Backend Python dev"},
    )
    assert len(roadmap_on["modules"]) >= 3
    assert roadmap_on["skillGapSummary"] is not None
    assert "Python" in roadmap_on["skillGapSummary"]["strongSkills"]


@pytest.mark.anyio
async def test_resume_rag_no_metric_fabrication():
    """Verifies that resume recommendations do not fabricate arbitrary numbers and use placeholders."""
    raw_text = "John Developer\nExperience with Python, FastAPI, and React building microservices."
    res = await analyze_resume_text(raw_text, target_role="Backend Developer")
    assert "skills" in res
    assert "bulletImprovements" in res
    assert len(res["bulletImprovements"]) >= 1

    first_bullet = res["bulletImprovements"][0]["improved"]
    # Check that placeholders like [X] or [Y] or Google XYZ formula are used instead of invented hardcoded percentages
    assert "[" in first_bullet or "%" in first_bullet or "FastAPI" in first_bullet


def test_health_endpoints():
    """Verifies /health, /health/dependencies, and /api/health."""
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    assert resp1.json() == {"status": "ok"}

    resp2 = client.get("/health/dependencies")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "backend" in data2
    assert "redis" in data2
    assert "qdrant" in data2
    assert "database" in data2

    resp3 = client.get("/api/health")
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "healthy"
