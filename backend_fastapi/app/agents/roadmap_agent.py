import json
import re
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import get_llm
from app.config import settings

logger = logging.getLogger("fresherai.roadmap_agent")

ROADMAP_SYSTEM_PROMPT = """
You are an Expert Career Mentor, Senior Software Architect, and Learning Roadmap Generator.

Your task is to generate a highly personalized, industry-standard roadmap that guides a candidate to achieve their target role and salary package.

Instructions:
1. Carefully analyze candidate skills and missing skills if resume is provided.
2. If resume is provided:
   - Focus on missing skills and advanced concepts.
   - Build upon the candidate's existing foundation.
3. If no resume is provided:
   - Generate a comprehensive roadmap from fundamentals to advanced production concepts.
4. Structure 8 to 12 progressive modules in logical learning order.
5. Provide concise 2-3 line descriptions for each module.
6. Return ONLY valid JSON matching the format below. No markdown formatting.

Format:
{
  "title": "Mastery Roadmap for Target Role",
  "targetPackage": "Target Package",
  "duration": "12 Weeks",
  "level": "Intermediate",
  "modules": [
    {
      "title": "Module Title",
      "duration": "1 Week",
      "difficulty": "Easy",
      "description": "Concise description of key concepts and projects."
    }
  ]
}

Difficulty must be EXACTLY: Easy, Medium, or Hard.
Level must be EXACTLY: Beginner, Intermediate, or Advanced.
"""


def _generate_fallback_roadmap(role: str, target_package: str, resume: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Provides high-quality realistic fallback roadmap when Groq API key is not active."""
    modules = [
        {
            "title": f"{role} Core Fundamentals & Architecture",
            "duration": "2 Weeks",
            "difficulty": "Easy",
            "description": f"Master the essential building blocks, language fundamentals, and clean code principles required for a {role}."
        },
        {
            "title": "Modern Frontend & Component State Management",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Build interactive, accessible user interfaces using React, component life-cycle patterns, and centralized state management."
        },
        {
            "title": "High-Performance Backend APIs with FastAPI & REST",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Design secure, async RESTful APIs, request validation with Pydantic, and session middleware."
        },
        {
            "title": "Relational Data Modeling & PostgreSQL / Supabase",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Implement efficient schema design, database migrations, indexes, JSONB querying, and transactions."
        },
        {
            "title": "Caching Strategies & Performance Optimization (Redis)",
            "duration": "1 Week",
            "difficulty": "Hard",
            "description": "Implement Redis caching, session stores, rate limiting, and database query optimization."
        },
        {
            "title": "Cloud Infrastructure, Containerization & CI/CD",
            "duration": "2 Weeks",
            "difficulty": "Hard",
            "description": "Containerize full-stack services using Docker and orchestrate automated testing and deployment pipelines."
        },
        {
            "title": "Production Capstone Project & Mock Interview Prep",
            "duration": "1 Week",
            "difficulty": "Hard",
            "description": "Deploy an end-to-end full-stack SaaS application with real-world authentication, payments, and system monitoring."
        }
    ]

    # Attach resources
    enriched_modules = []
    for mod in modules:
        query_title = urllib.parse.quote(f"{mod['title']} tutorial")
        doc_query = urllib.parse.quote(f"{mod['title']} documentation")
        enriched_modules.append({
            **mod,
            "youtube": f"https://www.youtube.com/results?search_query={query_title}",
            "article": f"https://dev.to/search?q={doc_query}",
        })

    return {
        "title": f"{role} Accelerated Career Roadmap",
        "targetPackage": target_package or "15 LPA",
        "duration": "12 Weeks",
        "level": "Intermediate",
        "modules": enriched_modules,
    }


async def generate_roadmap(
    role: str,
    target_package: str,
    use_resume: bool = False,
    resume: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates a personalized career roadmap via Groq LLaMA 3.3 70B,
    enriched with curated documentation and video learning links.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        logger.info("Using heuristic roadmap fallback (no active GROQ_API_KEY).")
        return _generate_fallback_roadmap(role, target_package, resume)

    try:
        llm = get_llm()
        resume_snippet = ""
        if use_resume and resume:
            resume_snippet = f"""
Candidate Skills: {', '.join(resume.get('skills', []))}
Missing Skills: {', '.join(resume.get('missingSkills', []))}
Projects: {', '.join(resume.get('projects', []))}
Summary: {resume.get('summary', '')}
"""

        user_content = f"""
Target Role: {role}
Target Package: {target_package}
{resume_snippet}
"""
        messages = [
            SystemMessage(content=ROADMAP_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = await llm.ainvoke(messages)
        content = re.sub(r"^```(?:json)?\n?", "", response.content.strip(), flags=re.MULTILINE)
        content = re.sub(r"\n?```$", "", content, flags=re.MULTILINE).strip()

        parsed_data = json.loads(content)

        # Capitalize level and difficulty formatting
        parsed_data["level"] = (parsed_data.get("level") or "Intermediate").capitalize()

        raw_modules = parsed_data.get("modules", [])
        enriched_modules = []

        for mod in raw_modules:
            title = mod.get("title", "Core Engineering Concept")
            query_title = urllib.parse.quote(f"{title} tutorial")
            doc_query = urllib.parse.quote(f"{title} official docs")
            difficulty = (mod.get("difficulty") or "Medium").capitalize()
            if difficulty not in ["Easy", "Medium", "Hard"]:
                difficulty = "Medium"

            enriched_modules.append({
                "title": title,
                "duration": mod.get("duration", "1 Week"),
                "difficulty": difficulty,
                "description": mod.get("description", ""),
                "youtube": f"https://www.youtube.com/results?search_query={query_title}",
                "article": f"https://dev.to/search?q={doc_query}",
            })

        parsed_data["modules"] = enriched_modules
        return parsed_data

    except Exception as e:
        logger.error(f"Error generating AI roadmap ({e}). Falling back to heuristic roadmap.")
        return _generate_fallback_roadmap(role, target_package, resume)
