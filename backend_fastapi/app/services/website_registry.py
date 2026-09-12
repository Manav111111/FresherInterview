"""
Fresher.AI — Website Capability & Route Registry
Single source of truth for runtime-verified website features, routes, and safe navigation links.
Prevents hallucination of non-existent features and blocks unauthorized / arbitrary URLs.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("fresherai.website_registry")


class WebsiteLink(BaseModel):
    """Safe, verified application link returned to frontend clients."""
    id: str = Field(..., description="Unique capability identifier")
    name: str = Field(..., description="Human-friendly feature name")
    path: str = Field(..., description="Verified relative application route")
    description: str = Field("", description="Brief capability summary")


@dataclass
class WebsiteCapability:
    """Runtime-verified website capability."""
    id: str
    name: str
    description: str
    route: str
    status: str  # "active" | "planned" | "unsupported"
    keywords: List[str] = field(default_factory=list)
    audience: str = "freshers and students"
    allowed_for_navigation: bool = True


# ── RUNTIME-VERIFIED WEBSITE CAPABILITIES ────────────────────────────────────
# Populated exclusively from verified frontend routes (frontend/src/App.jsx)
# and backend endpoints (backend_fastapi/app/routes/).
WEBSITE_CAPABILITIES: Dict[str, WebsiteCapability] = {
    "mock_interview": WebsiteCapability(
        id="mock_interview",
        name="AI Mock Interview",
        description="Practice adaptive AI-powered mock interviews tailored to your target role, with partial-credit scoring, resume deep-dives, and detailed feedback.",
        route="/interview",
        status="active",
        keywords=["mock interview", "interview", "practice interview", "interview prep", "technical interview", "ai interview", "start interview"],
        audience="job-seeking freshers preparing for technical or behavioral rounds",
        allowed_for_navigation=True,
    ),
    "resume_scorer": WebsiteCapability(
        id="resume_scorer",
        name="ATS Resume Scorer",
        description="Upload your resume for comprehensive ATS parsing, missing skill identification against target roles, and Google X-Y-Z bullet improvements.",
        route="/scorer",
        status="active",
        keywords=["resume scorer", "ats score", "ats", "resume score", "analyze resume", "check resume", "resume review", "missing skills"],
        audience="candidates optimizing their resume for company ATS filters",
        allowed_for_navigation=True,
    ),
    "resume_builder": WebsiteCapability(
        id="resume_builder",
        name="Resume Builder",
        description="Build and edit professional, ATS-compliant tech resumes with real-time preview and export.",
        route="/resume",
        status="active",
        keywords=["resume builder", "create resume", "build resume", "edit resume", "make a resume", "resume template"],
        audience="freshers creating clean tech resumes from scratch",
        allowed_for_navigation=True,
    ),
    "career_roadmap": WebsiteCapability(
        id="career_roadmap",
        name="Career Roadmaps",
        description="Generate personalized progressive weekly learning roadmaps with curated YouTube creators, hands-on portfolio projects, tools, and documentation.",
        route="/roadmap",
        status="active",
        keywords=["roadmap", "learning roadmap", "learning path", "study plan", "weekly roadmap", "career path", "what to learn"],
        audience="students needing structured guidance for specific engineering roles",
        allowed_for_navigation=True,
    ),
    "performance_analytics": WebsiteCapability(
        id="performance_analytics",
        name="Performance Analytics",
        description="Track your interview readiness trends, average scores, category accuracy, and historical mock interview reports.",
        route="/performance",
        status="active",
        keywords=["performance", "analytics", "readiness", "interview history", "scores", "progress", "track readiness"],
        audience="active candidates tracking their preparation progress over time",
        allowed_for_navigation=True,
    ),
    "solution_video": WebsiteCapability(
        id="solution_video",
        name="AI Solution Video",
        description="Generate interactive whiteboard animated video solutions with audio narration explaining technical algorithms and conceptual problems.",
        route="/solution-video",
        status="active",
        keywords=["solution video", "video solution", "whiteboard", "animated solution", "explain with video", "code animation"],
        audience="learners looking for step-by-step visual explanations of concepts",
        allowed_for_navigation=True,
    ),
    "dashboard": WebsiteCapability(
        id="dashboard",
        name="User Dashboard",
        description="Central candidate hub displaying current readiness score, resume status, active roadmaps, recent mock interviews, and coin balance.",
        route="/dashboard",
        status="active",
        keywords=["dashboard", "home dashboard", "my account", "overview", "main page", "hub"],
        audience="authenticated candidates managing their preparation activities",
        allowed_for_navigation=True,
    ),
    "pricing_coins": WebsiteCapability(
        id="pricing_coins",
        name="Pricing & Interview Coins",
        description="View interview coin packages and credit balances used to start AI mock interviews.",
        route="/pricing",
        status="active",
        keywords=["pricing", "coins", "interview coins", "credits", "buy coins", "subscription", "plans", "cost"],
        audience="candidates managing interview credits and packages",
        allowed_for_navigation=True,
    ),
    "landing_home": WebsiteCapability(
        id="landing_home",
        name="Fresher.AI Home",
        description="The main landing page introducing Fresher.AI's career readiness ecosystem.",
        route="/",
        status="active",
        keywords=["home", "landing", "welcome", "fresher ai", "homepage"],
        audience="new and returning visitors",
        allowed_for_navigation=True,
    ),
}

# ── KNOWN UNSUPPORTED FEATURES ───────────────────────────────────────────────
# Explicitly cataloged so the assistant never hallucinates support for them.
UNSUPPORTED_FEATURES = [
    {
        "keywords": ["bitcoin", "crypto", "cryptocurrency", "trading simulator", "crypto simulator", "stock trading"],
        "reason": "Fresher.AI is a career preparation platform for software engineering and tech roles; it does not offer financial, cryptocurrency, or trading simulators.",
    },
    {
        "keywords": ["github execution", "run my repo", "cloud ide sandbox", "execute github repo", "container runner"],
        "reason": "Fresher.AI does not currently provide a cloud virtual machine or live sandboxed code runner for arbitrary GitHub repositories.",
    },
    {
        "keywords": ["guaranteed job", "placement guarantee", "automated hiring", "direct hiring"],
        "reason": "Fresher.AI provides AI-powered preparation tools, roadmaps, and mock interviews to help candidates succeed, but does not offer direct placement guarantees or automated hiring.",
    },
    {
        "keywords": ["phone call", "call support", "toll free", "customer care number"],
        "reason": "Fresher.AI does not currently offer phone support. Support is provided via email at support@fresherai.com.",
    },
]


def get_capability(cap_id: str) -> Optional[WebsiteCapability]:
    """Retrieves a capability by its unique ID."""
    return WEBSITE_CAPABILITIES.get(cap_id)


def get_active_capabilities() -> List[WebsiteCapability]:
    """Returns all active, navigation-eligible capabilities."""
    return [c for c in WEBSITE_CAPABILITIES.values() if c.status == "active"]


def resolve_capability_link(cap_id: str) -> Optional[WebsiteLink]:
    """Resolves a capability ID to a validated WebsiteLink object."""
    cap = WEBSITE_CAPABILITIES.get(cap_id)
    if not cap or not cap.allowed_for_navigation or cap.status != "active":
        return None
    return WebsiteLink(
        id=cap.id,
        name=cap.name,
        path=cap.route,
        description=cap.description,
    )


def is_verified_route(path: str) -> bool:
    """Validates whether a given relative path corresponds to a verified application route."""
    if not path:
        return False
    clean_path = path.strip().split("?")[0].rstrip("/")
    if clean_path == "":
        clean_path = "/"

    for cap in WEBSITE_CAPABILITIES.values():
        if cap.status != "active":
            continue
        # Check exact or parameterized match (e.g. /interview vs /interview/:id)
        cap_route = cap.route.rstrip("/")
        if cap_route == "":
            cap_route = "/"
        if clean_path == cap_route:
            return True
        if ":" in cap.route and clean_path.startswith(cap.route.split(":")[0]):
            return True

    return False


def resolve_links_for_query(query: str, max_links: int = 2) -> List[WebsiteLink]:
    """
    Finds verified navigation links matching user query keywords.
    Ensures the LLM cannot fabricate unverified routes.
    """
    q_lower = query.lower().strip()
    matches: List[WebsiteLink] = []

    # Check for direct keyword matches
    for cap in get_active_capabilities():
        if any(kw in q_lower for kw in cap.keywords):
            link = resolve_capability_link(cap.id)
            if link and not any(m.id == link.id for m in matches):
                matches.append(link)
                if len(matches) >= max_links:
                    break

    return matches


def check_unsupported_feature(query: str) -> Optional[str]:
    """
    Checks if a user is asking about an unsupported or non-existent feature.
    Returns an honest disclaimer explanation if matched, or None.
    """
    q_lower = query.lower().strip()
    for item in UNSUPPORTED_FEATURES:
        if any(kw in q_lower for kw in item["keywords"]):
            return item["reason"]
    return None
