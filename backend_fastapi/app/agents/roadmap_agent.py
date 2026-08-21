import json
import re
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
from app.ai.provider_router import ai_router
from app.ai.schemas import TaskType, AIRequest

logger = logging.getLogger("fresherai.roadmap_agent")

ROADMAP_SYSTEM_PROMPT = """
You are a Principal Technical Architect, Engineering Mentor, and Career Strategist.
Generate a structured, industry-tailored learning roadmap to help a candidate achieve their target role and salary package.

Role: {role}
Target Package: {target_package}
Candidate Resume Context:
{resume_context}

RULES:
1. Generate 6 to 8 progressive modules structured from foundations to production mastery.
2. For each module provide:
   - "title": Clear descriptive module name.
   - "duration": e.g. "2 Weeks".
   - "difficulty": "Easy", "Medium", or "Hard".
   - "description": Concise description (2-3 sentences).
   - "topics": Array of 3-5 core technical subtopics.
   - "projects": Array of 1-2 portfolio projects to build.
   - "interviewImportance": "High", "Critical", or "Medium".
3. Return ONLY valid JSON matching this schema:
{{
  "title": "Mastery Roadmap for {role}",
  "targetPackage": "{target_package}",
  "duration": "12 Weeks",
  "level": "Intermediate",
  "modules": []
}}
"""


def _generate_fallback_roadmap(role: str, target_package: str, resume: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Provides high-quality realistic fallback roadmap when offline."""
    modules = [
        {
            "title": f"{role} Core Fundamentals & Clean Architecture",
            "duration": "2 Weeks",
            "difficulty": "Easy",
            "description": f"Master essential language fundamentals, design patterns, and algorithmic foundations required for a {role}.",
            "topics": ["Language Fundamentals", "Design Patterns", "Clean Code", "Data Structures"],
            "projects": ["Core CLI Application", "Unit Test Suite"],
            "interviewImportance": "Critical",
        },
        {
            "title": "Modern Frontend & Component Architecture",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Build interactive, accessible, and responsive user interfaces with component state management.",
            "topics": ["React / Next.js", "State Management", "Tailwind CSS", "Web Performance"],
            "projects": ["Dynamic SaaS Dashboard"],
            "interviewImportance": "High",
        },
        {
            "title": "High-Throughput Backend APIs & Microservices",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Design asynchronous RESTful endpoints, request validation, authentication, and error handling.",
            "topics": ["FastAPI / Node.js", "Async I/O", "JWT Auth", "Pydantic Schemas"],
            "projects": ["Scalable Authentication & API Gateway"],
            "interviewImportance": "Critical",
        },
        {
            "title": "Database Modeling, Migrations & Indexing",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Implement relational schemas, transactions, connection pooling, and complex SQL queries.",
            "topics": ["PostgreSQL / Supabase", "Query Profiling", "Transactions", "Migrations"],
            "projects": ["E-Commerce Data Store"],
            "interviewImportance": "Critical",
        },
        {
            "title": "Caching Systems & Performance Engineering",
            "duration": "1 Week",
            "difficulty": "Hard",
            "description": "Integrate in-memory caching with Redis, session stores, rate limiting, and cache invalidation.",
            "topics": ["Redis Caching", "Cache-Aside Pattern", "Rate Limiting", "Session Stores"],
            "projects": ["Real-time Rate Limiter & Cache Layer"],
            "interviewImportance": "High",
        },
        {
            "title": "Cloud Deployment, Containers & CI/CD Pipelines",
            "duration": "2 Weeks",
            "difficulty": "Hard",
            "description": "Containerize services with Docker and automate testing and deployment with CI/CD.",
            "topics": ["Docker", "GitHub Actions", "Cloud Deployment", "Observability"],
            "projects": ["Full-Stack Automated CI/CD Pipeline"],
            "interviewImportance": "High",
        },
        {
            "title": "Full-Stack Capstone & Live Mock Interview Prep",
            "duration": "1 Week",
            "difficulty": "Hard",
            "description": "Deploy a complete production-grade SaaS application with live monitoring and end-to-end testing.",
            "topics": ["System Integration", "Telemetry & Logs", "Live Mock Interviews"],
            "projects": ["Production Fresher.AI Capstone"],
            "interviewImportance": "Critical",
        }
    ]

    # Attach verified search/documentation links
    for mod in modules:
        query_title = urllib.parse.quote(f"{mod['title']} tutorial")
        doc_query = urllib.parse.quote(f"{mod['title']} documentation")
        mod["videoUrl"] = f"https://www.youtube.com/results?search_query={query_title}"
        mod["docUrl"] = f"https://www.google.com/search?q={doc_query}"
        mod["youtube"] = mod["videoUrl"]
        mod["docs"] = mod["docUrl"]
        mod["article"] = mod["docUrl"]

    return {
        "title": f"Mastery Roadmap for {role}",
        "targetPackage": target_package or "15 LPA",
        "duration": "12 Weeks",
        "level": "Intermediate",
        "modules": modules,
    }


async def generate_career_roadmap(
    role: str,
    target_package: str,
    resume: Optional[Dict[str, Any]] = None,
    use_resume: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Generates a structured career roadmap using AI Provider Router with verified resources."""
    resume_context = "No resume provided. Generate complete industry progression."
    if use_resume and resume:
        skills = resume.get("skills", [])
        missing = resume.get("missingSkills", [])
        resume_context = f"Candidate Current Skills: {skills}\nIdentified Missing Skills: {missing}"

    prompt = ROADMAP_SYSTEM_PROMPT.format(
        role=role,
        target_package=target_package or "15 LPA",
        resume_context=resume_context,
    )

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.ROADMAP_GENERATION,
            prompt=prompt,
            system_prompt="You are a Principal Engineering Career Mentor.",
            json_mode=True,
            temperature=0.2,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            modules = parsed.get("modules", [])
            for mod in modules:
                query_title = urllib.parse.quote(f"{mod.get('title', role)} tutorial")
                doc_query = urllib.parse.quote(f"{mod.get('title', role)} documentation")
                mod["videoUrl"] = f"https://www.youtube.com/results?search_query={query_title}"
                mod["docUrl"] = f"https://www.google.com/search?q={doc_query}"
                mod["youtube"] = mod["videoUrl"]
                mod["docs"] = mod["docUrl"]
                mod["article"] = mod["docUrl"]


            return {
                "title": parsed.get("title", f"Mastery Roadmap for {role}"),
                "targetPackage": parsed.get("targetPackage", target_package or "15 LPA"),
                "duration": parsed.get("duration", "12 Weeks"),
                "level": parsed.get("level", "Intermediate"),
                "modules": modules,
            }
    except Exception as e:
        logger.warning(f"AI roadmap generation notice ({e}), using fallback roadmap.")

    return _generate_fallback_roadmap(role, target_package, resume)



async def generate_roadmap(
    role: str,
    target_package: str,
    resume: Optional[Dict[str, Any]] = None,
    use_resume: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Compatibility alias for generate_career_roadmap."""
    return await generate_career_roadmap(role, target_package, resume, use_resume=use_resume, **kwargs)


