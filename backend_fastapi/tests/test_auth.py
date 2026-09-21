import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_and_coins_flow():
    # 1. Login with a test token
    login_response = client.post("/api/auth/login", json={"token": "test_google_oauth_token"})
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_data = login_response.json()
    assert login_data["success"] is True
    assert "user" in login_data
    assert login_data["user"]["interviewCoin"] == 150
    user_id = login_data["user"]["userId"]
    print(f"Logged in user: {user_id}, Coins: {login_data['user']['interviewCoin']}")

    # Check that session cookie was set
    assert "session" in login_response.cookies or "session" in client.cookies

    # 2. Get current user profile (/api/me)
    me_response = client.get("/api/me")
    assert me_response.status_code == 200, f"/api/me failed: {me_response.text}"
    me_data = me_response.json()
    assert me_data["success"] is True
    assert me_data["user"]["userId"] == user_id
    assert me_data["user"]["interviewCoin"] == 150
    print(f"Retrieved user profile (/api/me): {me_data['user']['email']}")

    # 3. Deduct interview coins
    use_coins_resp = client.post("/api/auth/use-interview-coins", json={"coins": 50, "action": "start_mock_interview"})
    assert use_coins_resp.status_code == 200, f"use-interview-coins failed: {use_coins_resp.text}"
    use_coins_data = use_coins_resp.json()
    assert use_coins_data["success"] is True
    assert use_coins_data["interviewCoin"] == 100
    print(f"Used 50 coins. Remaining: {use_coins_data['interviewCoin']}")

    # 4. Add interview coins
    add_coins_resp = client.post("/api/auth/add-coins", json={"coins": 200})
    assert add_coins_resp.status_code == 200, f"add-coins failed: {add_coins_resp.text}"
    add_coins_data = add_coins_resp.json()
    assert add_coins_data["success"] is True
    assert add_coins_data["interviewCoin"] == 300
    print(f"Added 200 coins. New balance: {add_coins_data['interviewCoin']}")

    # 5. Logout
    logout_resp = client.get("/api/auth/logout")
    assert logout_resp.status_code == 200
    print("Logout successful.")

    # 6. Verify unauthenticated access fails
    unauth_resp = client.get("/api/me")
    assert unauth_resp.status_code == 401
    print("Verified: Unauthenticated request rejected with 401.")

    print("\nALL PHASE 2 AUTH & COINS TESTS PASSED!")


def test_dual_authentication_regression():
    from unittest.mock import patch

    # 1. Missing token -> 401
    # Create isolated client without cookies
    fresh_client = TestClient(app)
    res_missing = fresh_client.get("/api/me")
    assert res_missing.status_code == 401
    assert "Unauthorized" in res_missing.text or "Session Expired" in res_missing.text

    # 2. Malformed token -> 401
    res_malformed = fresh_client.get("/api/me", headers={"Authorization": "Bearer invalid_malformed_token_xyz"})
    assert res_malformed.status_code == 401
    assert res_malformed.json()["detail"] == "Session Expired or Invalid"

    # 3. Valid backend session token -> 200
    login_resp = fresh_client.post("/api/auth/login", json={"token": "test_google_oauth_token"})
    assert login_resp.status_code == 200
    session_token = login_resp.json()["token"]
    res_session = fresh_client.get("/api/me", headers={"Authorization": f"Bearer {session_token}"})
    assert res_session.status_code == 200
    assert res_session.json()["success"] is True

    # 4. Valid Firebase ID token without existing Redis session (stateless path)
    with patch("app.core.security.verify_firebase_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "verified_firebase_uid_99",
            "email": "candidate99@fresherai.com",
            "name": "Stateless Candidate",
        }
        res_firebase = fresh_client.get("/api/me", headers={"Authorization": "Bearer simulated_valid_firebase_jwt"})
        assert res_firebase.status_code == 200
        user_body = res_firebase.json()["user"]
        assert user_body["email"] == "candidate99@fresherai.com"
        assert user_body["name"] == "Stateless Candidate"

    # 5. Invalid / expired Firebase token -> 401
    with patch("app.core.security.verify_firebase_token") as mock_verify:
        mock_verify.side_effect = ValueError("Firebase ID token has expired")
        res_expired = fresh_client.get("/api/me", headers={"Authorization": "Bearer simulated_expired_jwt"})
        assert res_expired.status_code == 401
        assert res_expired.json()["detail"] == "Session Expired or Invalid"

    # 6. Redis session cache unavailable + valid Firebase ID token -> succeeds statelessly
    with patch("app.core.security.get_cache", return_value=None):
        with patch("app.core.security.verify_firebase_token") as mock_verify:
            mock_verify.return_value = {
                "uid": "redis_offline_uid_42",
                "email": "offline_candidate@fresherai.com",
                "name": "Offline Resilient User",
            }
            res_resilient = fresh_client.get("/api/me", headers={"Authorization": "Bearer resilient_jwt_token"})
            assert res_resilient.status_code == 200
            assert res_resilient.json()["user"]["email"] == "offline_candidate@fresherai.com"

    # 7. Invalid Firebase token does not activate demo user
    with patch("app.core.security.verify_firebase_token") as mock_verify:
        mock_verify.side_effect = ValueError("Token verification failed")
        res_fail = fresh_client.get("/api/me", headers={"Authorization": "Bearer completely_bogus_token"})
        assert res_fail.status_code == 401
        assert "Fresher Candidate" not in res_fail.text

    # 8. Valid Bearer token allows protected roadmap generation
    with patch("app.ai.provider_router.ai_router.execute") as mock_ai:
        class FakeSuccess:
            success = True
            parsed_json = {
                "role": "DevOps Engineer",
                "target_salary": "18 LPA",
                "summary": {"difficulty": "Intermediate", "duration_weeks": 6, "personalized": False},
                "skills": {"strong": [], "partial": [], "missing": ["Kubernetes"], "priority": ["Kubernetes"]},
                "tools": ["Docker"],
                "youtube_resources": [],
                "official_docs": [],
                "career_resources": [],
                "projects": [],
                "modules": [{"title": "Container Orchestration", "difficulty": "Intermediate", "topics": ["Kubernetes"]}],
            }
            error = None
        mock_ai.return_value = FakeSuccess()

        roadmap_resp = fresh_client.post(
            "/api/roadmap/generate",
            json={"role": "DevOps Engineer", "targetPackage": "18 LPA", "useResume": False},
            headers={"Authorization": f"Bearer {session_token}"},
        )
        assert roadmap_resp.status_code == 201
        assert roadmap_resp.json()["success"] is True


if __name__ == "__main__":
    test_auth_and_coins_flow()
    test_dual_authentication_regression()
