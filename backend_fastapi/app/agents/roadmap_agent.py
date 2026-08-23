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
Generate a comprehensive, industry-tailored learning roadmap, core syllabus, and essential tools/website links to help a candidate achieve their target role and salary package.

Role: {role}
Target Package: {target_package}
Candidate Resume Context:
{resume_context}

RULES:
1. Generate a structured 4-pillar "syllabus" covering the essential theoretical & practical domain pillars and in-depth topics required to crack high-paying interviews for this specific role: {role}.
2. Generate 6 to 8 "essentialTools" (the exact tools, databases, cloud platforms, and frameworks a professional in this role MUST know and visit, such as GitHub, Supabase, Firebase, MongoDB, Docker, PostgreSQL, Redis, Postman, etc., with their real official website URLs).
3. Generate 6 to 8 progressive "modules" structured from foundations to production mastery.
   For each module provide:
   - "title": Descriptive module name.
   - "duration": e.g. "2 Weeks".
   - "difficulty": "Easy", "Medium", or "Hard".
   - "description": Concise description (2-3 sentences).
   - "topics": Array of 3-5 core technical subtopics.
   - "projects": Array of 1-2 portfolio projects to build.
   - "interviewImportance": "High", "Critical", or "Medium".
4. Return ONLY valid JSON matching this schema:
{{
  "title": "Mastery Roadmap for {role}",
  "targetPackage": "{target_package}",
  "duration": "12 Weeks",
  "level": "Intermediate",
  "syllabus": [
    {{
      "pillar": "Core Pillar Name",
      "description": "Why this pillar is critical for this role",
      "topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4"]
    }}
  ],
  "essentialTools": [
    {{
      "name": "Tool / Platform Name (e.g. GitHub, Supabase, Docker, MongoDB)",
      "url": "https://official-website-link",
      "category": "Category Name (e.g. Database, DevOps, Caching)",
      "description": "Why a candidate must master and visit this tool",
      "tag": "Essential"
    }}
  ],
  "modules": [
    {{
      "title": "Module Title",
      "duration": "2 Weeks",
      "difficulty": "Easy",
      "description": "Module description",
      "topics": ["Topic 1", "Topic 2"],
      "projects": ["Project 1"],
      "interviewImportance": "Critical"
    }}
  ]
}}
"""


def _generate_fallback_roadmap(role: str, target_package: str, resume: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Provides dynamic fallback roadmap when LLM is offline."""
    role_name = role or "Software Engineer"
    pkg = target_package or "15 LPA"

    modules = [
        {
            "title": f"{role_name} Core Fundamentals & Clean Architecture",
            "duration": "2 Weeks",
            "difficulty": "Easy",
            "description": f"Master essential language fundamentals, design patterns, and algorithmic foundations required for a {role_name}.",
            "topics": ["Language Fundamentals", "Design Patterns", "Clean Code", "Data Structures"],
            "projects": ["Core CLI Application", "Unit Test Suite"],
            "interviewImportance": "Critical",
        },
        {
            "title": "Database Engineering, Modeling & Indexing",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Implement relational schemas, transactions, connection pooling, and complex queries.",
            "topics": ["PostgreSQL / Supabase", "Query Profiling", "Transactions", "Migrations"],
            "projects": ["E-Commerce Data Store"],
            "interviewImportance": "Critical",
        },
        {
            "title": "High-Throughput APIs & Microservices",
            "duration": "2 Weeks",
            "difficulty": "Medium",
            "description": "Design asynchronous RESTful endpoints, request validation, authentication, and error handling.",
            "topics": ["API Gateway", "Async I/O", "JWT Auth", "Input Validation"],
            "projects": ["Scalable Authentication & API Gateway"],
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
            "title": "Production Capstone & Live Mock Interview Prep",
            "duration": "1 Week",
            "difficulty": "Hard",
            "description": "Deploy a complete production-grade SaaS application with live monitoring and end-to-end testing.",
            "topics": ["System Integration", "Telemetry & Logs", "Live Mock Interviews"],
            "projects": ["Production Capstone Application"],
            "interviewImportance": "Critical",
        }
    ]

    for mod in modules:
        query_title = urllib.parse.quote(f"{mod['title']} tutorial")
        doc_query = urllib.parse.quote(f"{mod['title']} documentation")
        mod["videoUrl"] = f"https://www.youtube.com/results?search_query={query_title}"
        mod["docUrl"] = f"https://www.google.com/search?q={doc_query}"
        mod["youtube"] = mod["videoUrl"]
        mod["docs"] = mod["docUrl"]
        mod["article"] = mod["docUrl"]

    default_tools = [
        {"name": "GitHub", "url": "https://github.com", "category": "Version Control & CI/CD", "description": "Repository hosting, code reviews, and GitHub Actions CI/CD workflows.", "tag": "Essential"},
        {"name": "PostgreSQL", "url": "https://www.postgresql.org", "category": "Relational Database", "description": "Enterprise-grade SQL database with robust ACID compliance and JSONB support.", "tag": "Core DB"},
        {"name": "Supabase", "url": "https://supabase.com", "category": "PostgreSQL & BaaS", "description": "Instant PostgreSQL database, Auth, Storage, and Realtime APIs.", "tag": "Cloud Backend"},
        {"name": "Firebase", "url": "https://firebase.google.com", "category": "NoSQL & Serverless", "description": "Firestore NoSQL database, Auth, Cloud Functions, and push notifications.", "tag": "BaaS"},
        {"name": "MongoDB", "url": "https://www.mongodb.com", "category": "NoSQL Document Store", "description": "Scalable JSON document database for rapid schema evolution.", "tag": "NoSQL DB"},
        {"name": "Docker", "url": "https://www.docker.com", "category": "Containerization", "description": "Standardized container platform ensuring dev and cloud parity.", "tag": "DevOps"},
        {"name": "Redis", "url": "https://redis.io", "category": "In-Memory Caching", "description": "Sub-millisecond in-memory data store for caching, messaging, and rate limiting.", "tag": "Performance"},
        {"name": "Postman", "url": "https://www.postman.com", "category": "API Testing & Docs", "description": "Complete API platform for designing, testing, and documenting endpoints.", "tag": "Testing"}
    ]

    default_syllabus = [
        {"pillar": "Core Architecture & Protocols", "description": f"Designing high-throughput, secure, and maintainable services for {role_name}.", "topics": ["RESTful Standards & HTTP Semantics", "Asynchronous I/O & Concurrency", "Authentication & Security", "API Rate Limiting"]},
        {"pillar": "Database Engineering & Storage", "description": "Data modeling, transactions, and indexing strategies.", "topics": ["Relational SQL Modeling", "Indexing Optimization", "ACID Transactions", "NoSQL Document Stores"]},
        {"pillar": "Caching & Distributed Systems", "description": "Engineering resilient, low-latency backends.", "topics": ["In-Memory Caching (Redis)", "Cache-Aside Patterns", "Message Queues", "System Idempotency"]},
        {"pillar": "DevOps, CI/CD & Production Cloud", "description": "Containerizing, deploying, and observing workloads.", "topics": ["Docker Containers", "Automated CI/CD", "Structured Logging", "Cloud Deployment"]}
    ]

    return {
        "title": f"Mastery Roadmap for {role_name}",
        "targetPackage": pkg,
        "duration": "12 Weeks",
        "level": "Intermediate",
        "syllabus": default_syllabus,
        "essentialTools": default_tools,
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
            system_prompt="You are a Principal Engineering Career Mentor and Curriculum Architect.",
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

            syllabus = parsed.get("syllabus", [])
            essential_tools = parsed.get("essentialTools", [])

            # If the LLM returned empty arrays, use fallback generators
            if not syllabus or not isinstance(syllabus, list) or len(syllabus) == 0:
                fallback = _generate_fallback_roadmap(role, target_package, resume)
                syllabus = fallback["syllabus"]

            if not essential_tools or not isinstance(essential_tools, list) or len(essential_tools) == 0:
                fallback = _generate_fallback_roadmap(role, target_package, resume)
                essential_tools = fallback["essentialTools"]

            return {
                "title": parsed.get("title", f"Mastery Roadmap for {role}"),
                "targetPackage": parsed.get("targetPackage", target_package or "15 LPA"),
                "duration": parsed.get("duration", "12 Weeks"),
                "level": parsed.get("level", "Intermediate"),
                "syllabus": syllabus,
                "essentialTools": essential_tools,
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


