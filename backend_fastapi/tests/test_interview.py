import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.agents.interview_graph import (
    calculate_deterministic_report,
    classify_score_result,
    get_readiness_classification,
    DIFFICULTY_WEIGHTS,
)

client = TestClient(app)


def test_deterministic_score_aggregation_and_weights():
    """Validates mathematical score calculation with difficulty weights (easy=0.8, medium=1.0, hard=1.2)."""
    questions = [
        {
            "question": "Explain REST API principles",
            "difficulty": "easy",
            "topic": "Backend Fundamentals",
            "userAnswer": "Stateless client-server architecture with standard HTTP methods.",
            "feedback": {
                "score": 80,
                "result": "correct",
                "technical_rubric": {"correctness": 32, "completeness": 16, "reasoning": 12, "communication": 12, "relevance": 8}
            }
        },
        {
            "question": "How do database indexes work internally?",
            "difficulty": "medium",
            "topic": "Databases",
            "userAnswer": "B-trees allow logarithmic search times.",
            "feedback": {
                "score": 60,
                "result": "partially_correct",
                "technical_rubric": {"correctness": 24, "completeness": 12, "reasoning": 9, "communication": 9, "relevance": 6}
            }
        },
        {
            "question": "Design a distributed rate limiter for high-throughput microservices.",
            "difficulty": "hard",
            "topic": "System Design",
            "userAnswer": "Use Redis token bucket algorithm with sliding window log and atomic Lua scripts.",
            "feedback": {
                "score": 90,
                "result": "correct",
                "technical_rubric": {"correctness": 38, "completeness": 18, "reasoning": 14, "communication": 13, "relevance": 7}
            }
        }
    ]

    report = calculate_deterministic_report("Backend Developer", "technical", questions)

    # Expected calculation:
    # Q1: 80 * 0.8 = 64
    # Q2: 60 * 1.0 = 60
    # Q3: 90 * 1.2 = 108
    # Weighted sum = 232, Total weight = 0.8 + 1.0 + 1.2 = 3.0
    # Expected overall = round(232 / 3.0) = 77
    assert report["overallScore"] == 77
    assert report["questionsCount"] == 3
    assert report["correctCount"] == 2
    assert report["partialCount"] == 1
    assert report["incorrectCount"] == 0
    assert report["averageScore"] == 77  # (80 + 60 + 90) / 3 = 76.66 -> 77
    assert report["readiness"] == "Strong / Nearly Ready"

    # Verify topic accuracy grouping
    topics = {t["topic"]: t["score"] for t in report["topicAccuracy"]}
    assert topics["Backend Fundamentals"] == 80
    assert topics["Databases"] == 60
    assert topics["System Design"] == 90

    # Verify category breakdown presence
    assert "Technical Correctness" in report["categoryScores"]
    assert "Completeness" in report["categoryScores"]
    assert "Problem Solving" in report["categoryScores"]


def test_classification_thresholds():
    """Validates answer classification rules."""
    # Correct: >= 75
    assert classify_score_result(85, "Comprehensive technical answer with depth.") == "correct"
    assert classify_score_result(75, "Satisfactory answer with core concepts.") == "correct"

    # Partially Correct: 50 <= score < 75
    assert classify_score_result(74, "Good understanding with some details missing.") == "partially_correct"
    assert classify_score_result(50, "Basic outline but incomplete.") == "partially_correct"

    # Incorrect: < 50
    assert classify_score_result(40, "Confused horizontal scaling with vertical scaling.") == "incorrect"

    # Insufficient: empty, < 5 words, or 'don't know'
    assert classify_score_result(70, "") == "insufficient"
    assert classify_score_result(70, "idk") == "insufficient"
    assert classify_score_result(70, "I don't know") == "insufficient"
    assert classify_score_result(70, "skip this question") == "insufficient"


def test_readiness_tiers():
    """Validates deterministic hiring readiness tiers."""
    assert get_readiness_classification(95)[0] == "Excellent / Interview Ready"
    assert get_readiness_classification(80)[0] == "Strong / Nearly Ready"
    assert get_readiness_classification(65)[0] == "Developing / Needs Practice"
    assert get_readiness_classification(45)[0] == "Significant Improvement Needed"
    assert get_readiness_classification(30)[0] == "Fundamentals Need Attention"


def test_complete_interview_lifecycle():
    """End-to-end test starting an interview, answering questions, and generating a verified report."""
    # 1. Login
    login_resp = client.post("/api/auth/login", json={"token": "candidate_interview_tester"})
    assert login_resp.status_code == 200

    # 2. Start Interview
    start_payload = {
        "type": "technical",
        "role": "Full Stack Developer",
        "useResume": True,
        "resume": {
            "skills": ["Python", "FastAPI", "React", "Docker"],
            "projects": ["Campus Management System"],
            "summary": "Full Stack Engineer"
        }
    }
    start_resp = client.post("/api/interview/start", json=start_payload)
    assert start_resp.status_code == 201
    start_data = start_resp.json()

    assert start_data["success"] is True
    interview_id = start_data["interviewId"]
    total_questions = start_data["totalQuestions"]
    assert total_questions >= 1

    # 3. Answer questions sequentially
    for q_idx in range(total_questions):
        answer_payload = {
            "interviewId": interview_id,
            "answer": "For this technical problem, I use modular architecture with clear separation of concerns, comprehensive indexing in PostgreSQL, and async execution in FastAPI to maximize throughput and responsiveness."
        }
        ans_resp = client.post("/api/interview/answer", json=answer_payload)
        assert ans_resp.status_code == 200
        ans_data = ans_resp.json()
        assert ans_data["success"] is True

        if ans_data["completed"]:
            report = ans_data["interview"]
            assert report["status"] == "completed"
            assert "overallScore" in report
            assert report["overallScore"] >= 0 and report["overallScore"] <= 100
            assert "summary" in report
            assert "categoryScores" in report
            assert len(report["strengths"]) > 0
            assert len(report["recommendations"]) > 0

    # 4. Fetch past interviews
    all_resp = client.get("/api/interview/all")
    assert all_resp.status_code == 200
    assert len(all_resp.json()["interviews"]) >= 1

    # 5. Fetch single interview report
    single_resp = client.get(f"/api/interview/{interview_id}")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["interview"]["_id"] == interview_id
