"""
Fresher.AI — Intent Router
Lightweight, high-accuracy intent classification for user messages.
Determines knowledge retrieval path, navigation relevance, and support escalation.
"""

import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class IntentRoutingDecision(BaseModel):
    """Routing decision determining context retrieval and response mode."""
    intent: str = Field(..., description="Target intent category")
    knowledge_sources: List[str] = Field(default_factory=list, description="Knowledge sources to query: 'website', 'career', 'interview', 'general'")
    include_navigation: bool = Field(False, description="Whether to attach verified navigation links")
    is_support: bool = Field(False, description="Whether this query requires support or troubleshooting handling")
    primary_capability_id: str = Field("", description="Primary capability ID if navigation/feature related")


class AssistantIntent:
    WEBSITE_INFORMATION = "website_information"
    FEATURE_GUIDANCE = "feature_guidance"
    NAVIGATION = "navigation"
    INTERVIEW_HELP = "interview_help"
    RESUME_HELP = "resume_help"
    ROADMAP_HELP = "roadmap_help"
    LEARNING_HELP = "learning_help"
    TECHNICAL_QUESTION = "technical_question"
    CAREER_GUIDANCE = "career_guidance"
    ACCOUNT_HELP = "account_help"
    SUPPORT = "support"
    GENERAL = "general"


def route_user_query(message: str) -> IntentRoutingDecision:
    """
    Classifies a user message into an IntentRoutingDecision.
    Fast, deterministic rule-based matching with fallback to general.
    """
    msg = message.lower().strip()

    # ── 1. Support & Troubleshooting ─────────────────────────────────────────
    support_keywords = [
        "contact support", "support number", "support email", "phone number",
        "customer care", "helpdesk", "report bug", "facing an error",
        "getting an error", "failed to", "cannot start", "can't start",
        "not working", "broken", "issue with", "troubleshoot", "problem with"
    ]
    if any(kw in msg for kw in support_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.SUPPORT,
            knowledge_sources=["website"],
            include_navigation=False,
            is_support=True,
            primary_capability_id="",
        )

    # ── 2. Navigation Requests ───────────────────────────────────────────────
    nav_keywords = [
        "where can i", "where is the", "take me to", "go to", "navigate to",
        "open the", "link to", "how do i get to", "access the"
    ]
    is_nav = any(kw in msg for kw in nav_keywords)
    if is_nav or "take me" in msg:
        cap_id = "mock_interview"
        if "resume" in msg or "ats" in msg or "scorer" in msg:
            cap_id = "resume_scorer" if "score" in msg or "ats" in msg or "analyzer" in msg else "resume_builder"
        elif "roadmap" in msg or "learning path" in msg:
            cap_id = "career_roadmap"
        elif "performance" in msg or "history" in msg or "analytics" in msg:
            cap_id = "performance_analytics"
        elif "video" in msg or "whiteboard" in msg:
            cap_id = "solution_video"
        elif "pricing" in msg or "coin" in msg or "credit" in msg:
            cap_id = "pricing_coins"
        elif "dashboard" in msg or "home" in msg:
            cap_id = "dashboard"

        return IntentRoutingDecision(
            intent=AssistantIntent.NAVIGATION,
            knowledge_sources=["website"],
            include_navigation=True,
            is_support=False,
            primary_capability_id=cap_id,
        )

    # ── 3. Website Information / Mission ─────────────────────────────────────
    website_info_keywords = [
        "what is fresher.ai", "what is fresher ai", "what is this website",
        "what can i do here", "what does this website do", "about fresher.ai",
        "what does fresher ai do", "tell me about this platform", "how does this platform work",
        "what can i do on this website", "how does fresher.ai work"
    ]
    if any(kw in msg for kw in website_info_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.WEBSITE_INFORMATION,
            knowledge_sources=["website"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="landing_home",
        )

    # ── 4. Career Guidance / Fresher Where to Start ───────────────────────────
    where_to_start_keywords = [
        "where should i start", "where do i start", "i am a fresher", "i'm a fresher",
        "how should i use this website", "how to start", "new here", "getting started",
        "how to begin", "first step"
    ]
    if any(kw in msg for kw in where_to_start_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.CAREER_GUIDANCE,
            knowledge_sources=["website", "career"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="resume_scorer",
        )

    # ── 5. Feature Guidance ──────────────────────────────────────────────────
    feature_guidance_keywords = [
        "how does the roadmap work", "how does the interview work", "how does ats score work",
        "how does mock interview work", "how do coins work", "how does the scorer work",
        "explain the features", "what features are available"
    ]
    if any(kw in msg for kw in feature_guidance_keywords):
        cap_id = "mock_interview" if "interview" in msg else ("resume_scorer" if "resume" in msg or "ats" in msg else "career_roadmap")
        return IntentRoutingDecision(
            intent=AssistantIntent.FEATURE_GUIDANCE,
            knowledge_sources=["website"],
            include_navigation=True,
            is_support=False,
            primary_capability_id=cap_id,
        )

    # ── 6. Account & Coins / Pricing ─────────────────────────────────────────
    account_keywords = [
        "interview coin", "coins balance", "how to get coins", "pricing plan",
        "buy coins", "subscription", "how much does it cost", "is fresher.ai free",
        "free tier", "coin cost", "my credits"
    ]
    if any(kw in msg for kw in account_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.ACCOUNT_HELP,
            knowledge_sources=["website"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="pricing_coins",
        )

    # ── 7. Resume Help & Optimization ────────────────────────────────────────
    resume_keywords = [
        "resume", "ats", "bullet point", "x-y-z", "improve my resume",
        "resume review", "resume feedback", "ats friendly", "missing skills in resume"
    ]
    if any(kw in msg for kw in resume_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.RESUME_HELP,
            knowledge_sources=["website", "career"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="resume_scorer",
        )

    # ── 8. Roadmap & Learning Paths ──────────────────────────────────────────
    roadmap_keywords = [
        "roadmap", "learning path", "12-week", "study plan", "what to learn for",
        "curriculum for", "learning roadmap", "weekly plan"
    ]
    if any(kw in msg for kw in roadmap_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.ROADMAP_HELP,
            knowledge_sources=["website", "career"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="career_roadmap",
        )

    # ── 9. Learning Resources / YouTube Channels / Projects ──────────────────
    learning_keywords = [
        "youtube channel", "youtube creator", "best channels for", "portfolio project",
        "practice project", "learning resource", "best resource to learn", "where to learn"
    ]
    if any(kw in msg for kw in learning_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.LEARNING_HELP,
            knowledge_sources=["career"],
            include_navigation=False,
            is_support=False,
            primary_capability_id="career_roadmap",
        )

    # ── 10. Interview Preparation & Questions ────────────────────────────────
    interview_keywords = [
        "interview", "tell me about yourself", "why should we hire you",
        "behavioral question", "star method", "mock interview prep",
        "interview answer strategy", "system design interview", "hr round"
    ]
    if any(kw in msg for kw in interview_keywords):
        return IntentRoutingDecision(
            intent=AssistantIntent.INTERVIEW_HELP,
            knowledge_sources=["interview", "website"],
            include_navigation=True,
            is_support=False,
            primary_capability_id="mock_interview",
        )

    # ── 11. Technical Conceptual Questions ───────────────────────────────────
    tech_starters = [
        "what is", "explain", "how does", "what are", "difference between",
        "why do we use", "define", "principles of", "concept of", "how to implement"
    ]
    tech_topics = [
        "rag", "docker", "kubernetes", "jwt", "oauth", "rest api", "microservices",
        "binary search", "dsa", "sql", "nosql", "fastapi", "react", "langchain",
        "langgraph", "qdrant", "redis", "supabase", "transformer", "llm",
        "embedding", "vector database", "acid properties", "git", "ci/cd"
    ]
    if any(kw in msg for kw in tech_topics) or any(msg.startswith(ts) for ts in tech_starters):
        return IntentRoutingDecision(
            intent=AssistantIntent.TECHNICAL_QUESTION,
            knowledge_sources=["general"],
            include_navigation=False,
            is_support=False,
            primary_capability_id="",
        )

    # ── 12. Default / General Conversation ───────────────────────────────────
    return IntentRoutingDecision(
        intent=AssistantIntent.GENERAL,
        knowledge_sources=["general"],
        include_navigation=False,
        is_support=False,
        primary_capability_id="",
    )
