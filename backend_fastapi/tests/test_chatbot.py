"""
Fresher.AI — Chatbot Assistant Compatibility Tests
Validates the /api/chat/message endpoint and assistant agent.
For the complete 15-scenario acceptance test suite, see test_assistant.py.
"""

import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.agents.chatbot_agent import generate_chatbot_response
from app.services.intent_router import route_user_query, AssistantIntent

client = TestClient(app)


def test_intent_routing_compatibility():
    """Validates that queries are routed to appropriate categories."""
    assert route_user_query("What is Fresher.AI?").intent == AssistantIntent.WEBSITE_INFORMATION
    assert route_user_query("Where can I take a mock interview?").intent == AssistantIntent.NAVIGATION
    assert route_user_query("What is Docker?").intent == AssistantIntent.TECHNICAL_QUESTION
    assert route_user_query("How do I contact support?").intent == AssistantIntent.SUPPORT


def test_chat_message_endpoint():
    """Validates the POST /api/chat/message API endpoint returns valid response and links."""
    response = client.post("/api/chat/message", json={
        "message": "Where can I practice mock interviews?",
        "history": [],
        "context": {"name": "Alex", "target_role": "Full Stack Developer"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reply" in data
    assert "links" in data
    assert len(data["reply"]) > 20
