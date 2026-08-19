import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_video_solution_endpoint_validation():
    """Test empty question validation."""
    response = client.post("/api/video/generate-solution", json={"question": ""})
    assert response.status_code == 422 or response.status_code == 400


def test_video_solution_math_generation():
    """Test generating a structured video solution for a math question."""
    response = client.post("/api/video/generate-solution", json={"question": "Solve 2x + 5 = 15"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    sol = data["data"]
    assert "question" in sol
    assert "scenes" in sol
    assert len(sol["scenes"]) >= 3
    assert "finalAnswer" in sol
    assert sol["totalDuration"] >= 10.0

    # Verify each scene structure
    for scene in sol["scenes"]:
        assert "id" in scene
        assert "content" in scene
        assert "narration" in scene
        assert "duration" in scene
        assert scene["duration"] > 0


def test_video_solution_programming_generation():
    """Test generating a structured video solution for a programming question."""
    response = client.post("/api/video/generate-solution", json={"question": "How does Binary Search work?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["scenes"]) >= 3
