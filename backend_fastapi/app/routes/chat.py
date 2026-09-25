import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from app.agents.chatbot_agent import generate_chatbot_response, detect_query_intent
from app.core.security import get_current_user

logger = logging.getLogger("fresherai.chat_router")

chat_router = APIRouter(tags=["Chatbot Assistant"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User message or question")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Recent message history")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User contextual data")


class ChatMessageResponse(BaseModel):
    success: bool = True
    reply: str
    intent: str
    links: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Verified application navigation links")
    suggested_actions: Optional[List[str]] = Field(default_factory=list, description="Contextual action suggestions")
    provider: Optional[str] = "groq"
    model: Optional[str] = "llama-3.3-70b-versatile"
    request_id: Optional[str] = None
    latency_ms: Optional[float] = None


@chat_router.post("/message", response_model=ChatMessageResponse)
async def handle_chat_message(
    body: ChatMessageRequest,
    request: Request,
):
    """
    Intelligent Fresher.AI Website Assistant endpoint.
    Provides verified platform facts, feature guidance, safe navigation links,
    career roadmaps, interview prep, and general technical explanations.
    """
    message = (body.message or "").strip()
    if not message:
        return ChatMessageResponse(
            success=True,
            reply="Hello! I am the Fresher.AI Assistant. How can I assist you with your career preparation, mock interviews, or platform features today?",
            intent="general",
            links=[],
            suggested_actions=["Start an AI Interview", "Analyze My Resume", "Build Learning Roadmap"],
            provider="local",
            model="default",
        )

    # Extract user info if authenticated
    user_context = dict(body.context or {})
    try:
        auth_cookie = request.cookies.get("session") or request.cookies.get("accessToken")
        auth_header = request.headers.get("Authorization")
        if auth_cookie or auth_header:
            user = await get_current_user(request)
            if user:
                user_context.setdefault("name", user.get("name"))
                user_context.setdefault("email", user.get("email"))
                user_context.setdefault("target_role", user.get("target_role") or user.get("role"))
    except Exception:
        pass  # Gracefully proceed for guest users

    try:
        res = await generate_chatbot_response(
            message=message,
            history=body.history,
            user_context=user_context,
        )
    except Exception as e:
        logger.error(f"Chatbot response generation failed: {e}", exc_info=True)
        from app.services.intent_router import route_user_query
        from app.agents.chatbot_agent import _generate_grounded_fallback, _generate_contextual_chips
        routing = route_user_query(message)
        res = {
            "success": True,
            "reply": _generate_grounded_fallback(message, routing, user_context),
            "intent": routing.intent,
            "links": [],
            "suggested_actions": _generate_contextual_chips(routing.intent, user_context),
            "provider": "fallback",
            "model": "grounded-engine",
        }

    from app.core.telemetry import get_current_request_id

    return ChatMessageResponse(
        success=res.get("success", True),
        reply=res.get("reply", "I'm ready to assist you. Please ask your question!"),
        intent=res.get("intent", "general"),
        links=res.get("links", []),
        suggested_actions=res.get("suggested_actions", []),
        provider=res.get("provider", "groq"),
        model=res.get("model", "llama-3.3-70b-versatile"),
        request_id=res.get("request_id") or get_current_request_id(),
        latency_ms=res.get("latency_ms"),
    )
