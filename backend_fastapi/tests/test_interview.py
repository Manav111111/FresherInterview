import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_interview_lifecycle():
    # 1. Login
    login_resp = client.post("/api/auth/login", json={"token": "candidate_interview_tester"})
    assert login_resp.status_code == 200
    user_id = login_resp.json()["user"]["userId"]
    print(f"Logged in user {user_id}")

    # 2. Start Interview
    start_payload = {
        "type": "technical",
        "role": "Full Stack Developer",
        "useResume": True,
        "resume": {
            "skills": ["Python", "FastAPI", "React", "Docker"],
            "projects": ["FresherAI Platform"],
            "summary": "Full Stack Engineer"
        }
    }
    start_resp = client.post("/api/interview/start", json=start_payload)
    assert start_resp.status_code == 201, f"Start interview failed: {start_resp.text}"
    start_data = start_resp.json()

    assert start_data["success"] is True
    interview_id = start_data["interviewId"]
    total_questions = start_data["totalQuestions"]
    assert total_questions >= 1
    assert "question" in start_data
    print(f"Started Interview ID: {interview_id}, Total Questions: {total_questions}")
    print(f"Q1: {start_data['question']['question']}")

    # 3. Answer questions sequentially
    for q_idx in range(total_questions):
        answer_payload = {
            "interviewId": interview_id,
            "answer": f"For this technical problem, I use modular architecture with clear separation of concerns, comprehensive indexing in PostgreSQL, and async execution in FastAPI to maximize throughput and responsiveness."
        }
        ans_resp = client.post("/api/interview/answer", json=answer_payload)
        assert ans_resp.status_code == 200, f"Submit answer {q_idx} failed: {ans_resp.text}"
        ans_data = ans_resp.json()
        assert ans_data["success"] is True

        if not ans_data["completed"]:
            print(f"Answered Q{q_idx+1}. Received Feedback (Score: {ans_data['feedback']['score']}). Next Q: {ans_data['question']['question']}")
        else:
            print("\nFinal question answered! Interview Completed!")
            report = ans_data["interview"]
            assert report["status"] == "completed"
            assert "overallScore" in report
            assert "summary" in report
            assert len(report["strengths"]) > 0
            assert len(report["recommendations"]) > 0
            print(f"Overall Interview Score: {report['overallScore']}/100")
            print(f"Summary: {report['summary']}")
            print(f"Strengths: {report['strengths']}")
            print(f"Recommendations: {report['recommendations']}")

    # 4. Test GET /api/interview/all
    all_resp = client.get("/api/interview/all")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert all_data["success"] is True
    assert len(all_data["interviews"]) >= 1
    print(f"Verified /api/interview/all: Found {len(all_data['interviews'])} interviews")

    # 5. Test GET /api/interview/{id}
    single_resp = client.get(f"/api/interview/{interview_id}")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["success"] is True
    assert single_data["interview"]["_id"] == interview_id
    print(f"Verified /api/interview/{interview_id}: Status is '{single_data['interview']['status']}'")

    print("\nALL PHASE 4 MOCK INTERVIEW TESTS PASSED!")


if __name__ == "__main__":
    test_complete_interview_lifecycle()
