import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.agents.chatbot_agent import detect_query_intent, QueryIntent, generate_chatbot_response

client = TestClient(app)


def test_intent_detection():
    """Validates lightweight intent classification across query categories."""
    # 1. LinkedIn Post Intents
    assert detect_query_intent("Write a LinkedIn post about my new job at Amazon as SDE 1") == QueryIntent.LINKEDIN_POST
    assert detect_query_intent("I got selected at Microsoft, make a LinkedIn post") == QueryIntent.LINKEDIN_POST
    assert detect_query_intent("Write a post for my internship at Google") == QueryIntent.LINKEDIN_POST
    assert detect_query_intent("Make a LinkedIn post about completing my portfolio project") == QueryIntent.LINKEDIN_POST

    # 2. Theory / Conceptual Intents
    assert detect_query_intent("What is Docker?") == QueryIntent.THEORY_CONCEPTUAL
    assert detect_query_intent("Explain REST API principles") == QueryIntent.THEORY_CONCEPTUAL
    assert detect_query_intent("What are ACID properties in database systems?") == QueryIntent.THEORY_CONCEPTUAL
    assert detect_query_intent("How does garbage collection work in Java?") == QueryIntent.THEORY_CONCEPTUAL

    # 3. Mathematical / Numerical Intents
    assert detect_query_intent("Solve 2x + 5 = 15") == QueryIntent.MATHEMATICAL_NUMERICAL
    assert detect_query_intent("Find the derivative of f(x) = x^3 + 4x - 7") == QueryIntent.MATHEMATICAL_NUMERICAL
    assert detect_query_intent("Calculate the determinant of a 2x2 matrix") == QueryIntent.MATHEMATICAL_NUMERICAL

    # 4. Coding & DSA Intents
    assert detect_query_intent("Write a python function to reverse a string") == QueryIntent.CODING_PROGRAMMING
    assert detect_query_intent("Explain Binary Search algorithm and its complexity") == QueryIntent.DSA_ALGORITHM

    # 5. Interview Question Intent
    assert detect_query_intent("How to answer tell me about yourself in an interview?") == QueryIntent.INTERVIEW_QUESTION


def test_chatbot_linkedin_post_generation():
    """Validates that LinkedIn post generation returns a clean, ready-to-copy post with hashtags and no meta filler."""
    res = asyncio.run(generate_chatbot_response("Write a LinkedIn post about starting my internship at Google as a Software Engineer"))
    assert res["success"] is True
    assert res["intent"] == QueryIntent.LINKEDIN_POST
    reply = res["reply"]
    
    # Must contain relevant content and hashtags
    assert "#" in reply
    # Must not contain conversational meta filler
    assert not reply.lower().startswith("here is your linkedin post")
    assert not reply.lower().startswith("here's a post")


def test_chatbot_theory_response():
    """Validates that theory questions are answered conceptually without forced math steps."""
    res = asyncio.run(generate_chatbot_response("What is Docker and why is it used?"))
    assert res["success"] is True
    assert res["intent"] == QueryIntent.THEORY_CONCEPTUAL
    reply = res["reply"]

    # Must explain naturally without forced calculation steps
    assert "calculate" not in reply.lower()
    assert len(reply) > 40


def test_chat_message_endpoint():
    """Validates the POST /api/chat/message API endpoint."""
    response = client.post("/api/chat/message", json={
        "message": "Write a LinkedIn post about completing my full-stack web development project",
        "history": [],
        "context": {"name": "Alex", "target_role": "Full Stack Developer"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["intent"] == QueryIntent.LINKEDIN_POST
    assert len(data["reply"]) > 30
