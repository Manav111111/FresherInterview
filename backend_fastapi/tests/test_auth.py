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


if __name__ == "__main__":
    test_auth_and_coins_flow()
