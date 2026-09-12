"""
Fresher.AI — Dedicated Website Knowledge Layer (Layer A)
Contains verified platform facts, core workflows, feature documentation,
FAQs, support configurations, and platform boundary rules.
Kept strictly separate from interview question pools and general LLM knowledge.
"""

from typing import Dict, Any, List
from app.config import settings
from app.services.website_registry import WEBSITE_CAPABILITIES, get_active_capabilities


def get_platform_overview() -> str:
    """Returns the canonical, verified platform description."""
    return """
Fresher.AI is an AI-powered career readiness platform designed specifically for students, freshers, and early-career developers.
It bridges the gap between academic learning and real-world tech hiring through three core pillars:
1. ATS Resume Scoring & Optimization: Analyzes resumes against canonical tech roles, extracts detected skills, highlights high-priority skill gaps, and suggests quantifiable bullet improvements.
2. Personalized Career Roadmaps: Generates progressive weekly learning paths with curated YouTube creators, hands-on portfolio projects, developer tools, and official documentation.
3. Adaptive AI Mock Interviews: Conducts role-tailored technical and behavioral mock interviews with partial-credit scoring, resume deep-dives, and detailed performance reports.
""".strip()


def get_recommended_fresher_workflow() -> List[Dict[str, str]]:
    """Returns the recommended step-by-step path for a new fresher on the platform."""
    return [
        {
            "step": 1,
            "title": "Analyze Your Resume",
            "route": "/scorer",
            "description": "Upload your resume to the ATS Resume Scorer to discover your current score, detected skills, and missing technical requirements.",
        },
        {
            "step": 2,
            "title": "Generate Your Learning Roadmap",
            "route": "/roadmap",
            "description": "Choose your target role (e.g. AI Engineer, Full Stack, Backend) to get a progressive weekly learning roadmap with curated resources and projects.",
        },
        {
            "step": 3,
            "title": "Practice AI Mock Interviews",
            "route": "/interview",
            "description": "Start an adaptive mock interview for your target role. You can optionally attach your resume for personalized deep-dive questions and partial-credit evaluations.",
        },
        {
            "step": 4,
            "title": "Review Performance & Track Progress",
            "route": "/performance",
            "description": "Track your readiness score over time, review category accuracy breakdowns, and examine detailed question-by-question feedback.",
        },
    ]


def get_support_info() -> Dict[str, Any]:
    """
    Returns official support channels directly from application configuration.
    Never invents phone numbers or unverified support handles.
    """
    has_phone = bool(settings.SUPPORT_PHONE and settings.SUPPORT_PHONE.strip())
    return {
        "email": settings.SUPPORT_EMAIL,
        "phone": settings.SUPPORT_PHONE if has_phone else None,
        "phone_available": has_phone,
        "url": settings.SUPPORT_URL,
        "message": (
            f"You can reach official Fresher.AI support via email at {settings.SUPPORT_EMAIL}."
            if not has_phone else
            f"You can reach official Fresher.AI support via email at {settings.SUPPORT_EMAIL} or phone at {settings.SUPPORT_PHONE}."
        )
    }


def get_troubleshooting_guidance(issue_type: str = "general") -> str:
    """Provides actionable troubleshooting steps for common platform issues."""
    issue_lower = issue_type.lower()
    if "interview" in issue_lower or "start" in issue_lower:
        return """
Troubleshooting steps for starting an AI Mock Interview:
1. Verify Microphone & Camera Permissions: Ensure your browser has granted microphone and camera access for the platform.
2. Check Selected Role: Make sure you selected a target role (e.g. AI Engineer, Full Stack, Backend) before clicking start.
3. Check Interview Coins: Ensure you have available interview coins. You can check or top up your coins in the Pricing & Coins section (/pricing).
4. Network Connection: Check your internet connection as the interview engine streams audio and questions in real time.
If the issue persists, please reach out to our team at support@fresherai.com with the error message.
""".strip()

    if "resume" in issue_lower or "upload" in issue_lower:
        return """
Troubleshooting steps for Resume Scorer & Builder:
1. Supported Format: Ensure your resume is a standard text-based PDF or plain text (scanned image PDFs without readable text cannot be parsed).
2. Section Headings: Check that standard section headings (Education, Skills, Experience, Projects) are clearly marked.
3. File Size: Ensure the file size is under 5MB.
""".strip()

    support = get_support_info()
    return f"If you are facing an unexpected technical issue, please describe what happened or contact our support team at {support['email']}."


def format_website_context_for_prompt() -> str:
    """Formats verified website capabilities and facts for LLM prompt injection."""
    capabilities_summary = []
    for cap in get_active_capabilities():
        capabilities_summary.append(f"- **{cap.name}** (Route: `{cap.route}`): {cap.description}")

    support = get_support_info()
    phone_note = f"Phone: {support['phone']}" if support['phone_available'] else "Phone Support: Currently unavailable (Email only)."

    return f"""
=== VERIFIED FRESHER.AI PLATFORM INFORMATION (SOURCE OF TRUTH) ===
{get_platform_overview()}

Active Features & Routes:
{chr(10).join(capabilities_summary)}

Official Support Contact:
- Email: {support['email']}
- {phone_note}
- Official Website: {support['url']}

Important Platform Grounding Rules:
1. All website links MUST come exclusively from verified routes listed above (e.g. /interview, /scorer, /resume, /roadmap, /performance, /solution-video, /dashboard, /pricing).
2. DO NOT invent non-existent features (such as bitcoin simulators, cloud code execution sandboxes, or direct placement guarantees).
3. If phone support is requested and not configured, honestly state that phone support is currently unavailable.
===================================================================
""".strip()
