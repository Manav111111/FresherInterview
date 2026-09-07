import pytest
import asyncio
from app.services.retrieval_service import retrieval_service


@pytest.mark.asyncio
async def test_ai_engineer_youtube_creators():
    """Verify AI Engineer returns CampusX, Krish Naik, Codebasics and no unverified creators."""
    creators = await retrieval_service.search_youtube_creators(role="AI Engineer", top_k_creators=5)
    assert len(creators) >= 3
    creator_ids = [c["channel"]["id"] for c in creators]
    assert "campusx" in creator_ids
    assert "krish_naik" in creator_ids
    assert "codebasics" in creator_ids

    # Verify all returned playlists are verified
    for c in creators:
        assert len(c["playlists"]) <= 3
        for p in c["playlists"]:
            assert p["verified"] is True
            assert "list=" in p["url"]

    # Verify no unverified creators leak
    assert "shreyansh_ai" not in creator_ids
    assert "coding_with_sagar" not in creator_ids
    assert "think_with_models" not in creator_ids


@pytest.mark.asyncio
async def test_ai_engineer_personalization():
    """If Python is strong and RAG/LangGraph are missing, prioritize Agentic AI and RAG over Python crash course."""
    creators = await retrieval_service.search_youtube_creators(
        role="AI Engineer",
        missing_skills=["rag", "langgraph"],
        strong_skills=["python"],
        top_k_creators=5,
    )
    # CampusX playlists should prioritize Agentic AI or RAG or LangChain over 100 Days of ML / Python
    campusx = next(c for c in creators if c["channel"]["id"] == "campusx")
    titles = [p["title"] for p in campusx["playlists"]]
    assert any("LangGraph" in t or "RAG" in t or "LangChain" in t for t in titles)


@pytest.mark.asyncio
async def test_full_stack_youtube_creators():
    """Verify Full Stack returns verified creators (Apna College, CodeWithHarry, Chai aur Code, Sheryians, Thapa)."""
    creators = await retrieval_service.search_youtube_creators(role="Full Stack Developer", top_k_creators=5)
    creator_ids = [c["channel"]["id"] for c in creators]
    assert "apna_college" in creator_ids or "codewithharry" in creator_ids or "chai_aur_code" in creator_ids
    for c in creators:
        for p in c["playlists"]:
            assert p["verified"] is True


@pytest.mark.asyncio
async def test_devops_youtube_creators():
    """Verify DevOps prioritizes Abhishek Veeramalla and Gate Smashers."""
    creators = await retrieval_service.search_youtube_creators(role="DevOps Engineer", top_k_creators=5)
    creator_ids = [c["channel"]["id"] for c in creators]
    assert "abhishek_veeramalla" in creator_ids


@pytest.mark.asyncio
async def test_dsa_youtube_creators():
    """Verify DSA prioritizes Take U Forward, CodeHelp, Kunal Kushwaha, Apna College."""
    creators = await retrieval_service.search_youtube_creators(role="DSA / Placement", top_k_creators=5)
    creator_ids = [c["channel"]["id"] for c in creators]
    assert any(x in creator_ids for x in ["take_u_forward", "codehelp", "kunal_kushwaha", "apna_college"])


@pytest.mark.asyncio
async def test_system_design_youtube_creators():
    """Verify System Design returns Gaurav Sen with verified playlist."""
    creators = await retrieval_service.search_youtube_creators(role="System Design", top_k_creators=5)
    creator_ids = [c["channel"]["id"] for c in creators]
    assert "gaurav_sen" in creator_ids
    gaurav = next(c for c in creators if c["channel"]["id"] == "gaurav_sen")
    assert any("PLMCXHnjXnTnvo6alSjVkgxV-VH6EPyvoX" in p["url"] for p in gaurav["playlists"])
