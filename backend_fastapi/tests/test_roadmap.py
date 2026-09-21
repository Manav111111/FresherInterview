import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_roadmap_flow():
    # 1. Login
    login_resp = client.post("/api/auth/login", json={"token": "roadmap_tester_token"})
    assert login_resp.status_code == 200
    user_id = login_resp.json()["user"]["userId"]
    print(f"Authenticated as user {user_id}")

    # 2. Generate Roadmap
    generate_payload = {
        "role": "DevOps Engineer",
        "targetPackage": "18 LPA",
        "useResume": True,
        "resume": {
            "skills": ["Linux", "Docker", "Python", "CI/CD"],
            "missingSkills": ["Kubernetes", "Terraform", "Prometheus"],
            "summary": "Junior DevOps Engineer"
        }
    }
    create_resp = client.post("/api/roadmap/generate", json=generate_payload)
    assert create_resp.status_code == 201, f"Generate roadmap failed: {create_resp.text}"
    create_data = create_resp.json()

    assert create_data["success"] is True
    assert "data" in create_data
    roadmap = create_data["data"]
    roadmap_id = roadmap["_id"]
    assert len(roadmap["modules"]) >= 1
    assert "title" in roadmap
    assert "targetPackage" in roadmap

    first_mod = roadmap["modules"][0]
    assert "title" in first_mod
    assert "description" in first_mod
    assert "youtube" in first_mod
    assert "article" in first_mod
    print(f"Generated Roadmap: '{roadmap['title']}', Level: {roadmap['level']}, Duration: {roadmap['duration']}")
    print(f"Total Modules: {len(roadmap['modules'])}")
    print(f"Module 1: {first_mod['title']} ({first_mod['difficulty']})")
    print(f"Resource: {first_mod['youtube']}")

    # 3. Test GET /api/roadmap
    get_all_resp = client.get("/api/roadmap")
    assert get_all_resp.status_code == 200
    get_all_data = get_all_resp.json()
    assert get_all_data["success"] is True
    assert len(get_all_data["data"]) >= 1
    print(f"Verified GET /api/roadmap: {len(get_all_data['data'])} roadmap(s) found")

    # 4. Test GET /api/roadmap/{id}
    get_one_resp = client.get(f"/api/roadmap/{roadmap_id}")
    assert get_one_resp.status_code == 200
    get_one_data = get_one_resp.json()
    assert get_one_data["success"] is True
    assert get_one_data["data"]["_id"] == roadmap_id
    print(f"Verified GET /api/roadmap/{roadmap_id}: Retrieved successfully")

    print("\nALL PHASE 5 ROADMAP TESTS PASSED!")


def test_roadmap_list_and_string_skill_regression():
    """
    Regression test verifying that:
    1. resume.skills as a list of strings works without type errors.
    2. resume.missingSkills as a list of strings works without type errors.
    3. resume.skills as a comma-separated string remains compatible.
    4. Deterministic fallback with list topics_covered does not raise 'list' object has no attribute 'split'.
    """
    from unittest.mock import patch

    # 1. Test list inputs under simulated AI provider failure (deterministic fallback)
    with patch("app.ai.provider_router.ai_router.execute") as mock_ai:
        class ProviderFailure:
            success = False
            parsed_json = None
            error = "Simulated CI missing keys"

        mock_ai.return_value = ProviderFailure()

        list_payload = {
            "role": "DevOps Engineer",
            "targetPackage": "18 LPA",
            "useResume": True,
            "resume": {
                "skills": ["Linux", "Docker", "Python", "CI/CD"],
                "missingSkills": ["Kubernetes", "Terraform", "Prometheus"],
                "summary": "Junior DevOps Engineer"
            }
        }
        res_list = client.post("/api/roadmap/generate", json=list_payload)
        assert res_list.status_code == 201, f"List payload failed: {res_list.text}"
        data_list = res_list.json()["data"]
        assert len(data_list["modules"]) >= 3
        assert "skills" in data_list
        assert any("Kubernetes" in str(m.get("title", "")) or "Kubernetes" in str(m.get("topics", "")) for m in data_list["modules"])

        # 2. Test comma-separated string input compatibility
        str_payload = {
            "role": "DevOps Engineer",
            "targetPackage": "18 LPA",
            "useResume": True,
            "resume": {
                "skills": "Linux, Docker, Python, CI/CD",
                "missingSkills": "Kubernetes, Terraform, Prometheus",
                "summary": "Junior DevOps Engineer"
            }
        }
        res_str = client.post("/api/roadmap/generate", json=str_payload)
        assert res_str.status_code == 201, f"String payload failed: {res_str.text}"
        data_str = res_str.json()["data"]
        assert len(data_str["modules"]) >= 3


if __name__ == "__main__":
    test_roadmap_flow()
    test_roadmap_list_and_string_skill_regression()
