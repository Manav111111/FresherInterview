import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_billing_and_payment_flow():
    # 1. Login
    login_resp = client.post("/api/auth/login", json={"token": "billing_test_candidate"})
    assert login_resp.status_code == 200
    user_id = login_resp.json()["user"]["userId"]
    initial_coins = login_resp.json()["user"]["interviewCoin"]
    print(f"Authenticated user {user_id}, Current coins: {initial_coins}")

    # 2. Create Razorpay order for 'starter' plan (199 INR -> 300 Coins)
    create_resp = client.post("/api/billing/create", json={"planId": "starter"})
    assert create_resp.status_code == 201, f"Create order failed: {create_resp.text}"
    create_data = create_resp.json()
    assert create_data["success"] is True
    assert "order" in create_data
    order = create_data["order"]
    order_id = order["id"]
    assert order["amount"] == 19900  # in paise
    print(f"Razorpay order created: {order_id}, Amount: INR {order['amount']//100}")

    # 3. Verify Payment
    verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": f"pay_{order_id[6:]}",
        "razorpay_signature": "mock_valid_signature_for_test",
    }
    verify_resp = client.post("/api/billing/verify", json=verify_payload)
    assert verify_resp.status_code == 200, f"Verify payment failed: {verify_resp.text}"
    verify_data = verify_resp.json()
    assert verify_data["success"] is True
    print(f"Payment verified successfully: {verify_data['message']}")

    # 4. Credit Coins to Account
    add_coins_resp = client.post("/api/auth/add-coins", json={"coins": 300})
    assert add_coins_resp.status_code == 200
    new_coin_balance = add_coins_resp.json()["interviewCoin"]
    assert new_coin_balance == initial_coins + 300
    print(f"Credited 300 coins! New user coin balance: {new_coin_balance}")

    # 5. Check Payment History
    history_resp = client.get("/api/billing/history")
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert history_data["success"] is True
    assert len(history_data["history"]) >= 1
    print(f"Payment History verified: Found {len(history_data['history'])} transaction(s)")

    print("\nALL PHASE 6 BILLING & PAYMENTS TESTS PASSED!")


if __name__ == "__main__":
    test_billing_and_payment_flow()
