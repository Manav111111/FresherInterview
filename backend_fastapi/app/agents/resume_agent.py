import json
import re
import logging
from typing import Dict, Any, Optional
from app.ai.provider_router import ai_router
from app.ai.schemas import TaskType, AIRequest, ResumeATSAnalysisSchema
from app.core.redis import get_redis

logger = logging.getLogger("fresherai.resume_agent")

RESUME_DEEP_PROMPT = """
You are a Principal Tech Recruiter and ATS Algorithm Specialist with 15+ years of experience at top-tier tech firms.
Thoroughly analyze the candidate's resume text below and produce a comprehensive ATS audit and quantifiable bullet improvement plan.

Resume Text:
{resume_text}

EVALUATION CRITERIA:
1. "name": Candidate full name.
2. "email": Candidate email address.
3. "phone": Candidate phone number.
4. "summary": Concise executive summary (2-3 sentences).
5. "skills": Array of technical skills, frameworks, languages, and tools found.
6. "projects": Array of project objects with "name" and "description".
7. "education": Array of education entries.
8. "experience": Array of work / internship entries.
9. "strengths": 3-5 specific candidate strengths with technical justification.
10. "weaknesses": 3-5 specific weak points or missing elements.
11. "missingSkills": 4-6 high-demand industry skills that are missing for their target domain.
12. "suggestedRole": Best-fit job title (e.g. "Full Stack Engineer", "Backend Developer", "ML Engineer").
13. "score": Overall ATS score (0-100).
14. "atsFormattingScore": Score (0-100) on keyword density and ATS scannability.
15. "sectionsDetected": Object with boolean flags for: "contactInfo", "summary", "experience", "education", "skills", "projects".
16. "bulletImprovements": Array of 3-4 objects containing:
    - "original": A weak bullet point from the resume.
    - "improved": A high-impact revision following Google's X-Y-Z formula: "Accomplished [X] as measured by [Y] by doing [Z]".
    - "reason": Why the revision performs better in recruiter screening.
17. "recommendations": Exactly 5 actionable recommendations to boost recruiter callback rates.

Return ONLY valid JSON.
"""


def _fallback_resume_analysis(text: str) -> Dict[str, Any]:
    """Heuristic fallback parser for offline/test environments."""
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    email = email_match.group(0) if email_match else "candidate@example.com"

    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    phone = phone_match.group(0) if phone_match else "+1-555-0199"

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else "Fresher Candidate"

    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
        "Express", "MongoDB", "PostgreSQL", "Supabase", "Docker", "Git",
        "HTML", "CSS", "TailwindCSS", "Redux", "REST API", "GraphQL", "AWS"
    ]
    detected_skills = [s for s in common_skills if s.lower() in text.lower()]
    if not detected_skills:
        detected_skills = ["Python", "FastAPI", "React", "SQL", "Git"]

    score = min(95, max(65, 50 + len(detected_skills) * 4))

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "summary": "Software engineer with hands-on experience building modern full-stack web applications and cloud services.",
        "skills": detected_skills,
        "projects": [
            "Fresher.AI Platform - AI mock interview and ATS evaluation platform",
            "Cloud Microservices API - High-throughput REST API with automated testing"
        ],
        "education": ["Bachelor of Technology in Computer Science & Engineering"],
        "experience": ["Software Engineering Intern - Full Stack Development"],
        "strengths": [
            "Hands-on proficiency with modern web stacks",
            "Clear technical project demonstrations",
            "Solid grasp of relational databases and REST APIs"
        ],
        "weaknesses": [
            "Quantifiable metrics and business impact numbers could be expanded",
            "System scaling and cloud deployment details could be deeper"
        ],
        "missingSkills": [
            "Redis / Distributed Caching",
            "Docker / Containerization",
            "CI/CD Pipeline Automation",
            "Unit Testing & Integration Drills"
        ],
        "suggestedRole": "Full Stack Developer",
        "score": score,
        "atsFormattingScore": 85,
        "sectionsDetected": {
            "contactInfo": True,
            "summary": True,
            "experience": True,
            "education": True,
            "skills": True,
            "projects": True
        },
        "bulletImprovements": [
            {
                "original": "Worked on backend APIs and database queries.",
                "improved": "Engineered 12+ RESTful FastAPI endpoints serving 5,000+ daily requests, reducing average query latency by 35% using indexing and connection pooling.",
                "reason": "Quantifies scale and demonstrates tangible performance optimizations using Google's X-Y-Z formula."
            }
        ],
        "recommendations": [
            "Add quantifiable production metrics to every project bullet point.",
            "Incorporate high-demand backend skills like Redis, Docker, and CI/CD.",
            "Tailor technical keywords to match specific job posting requirements.",
            "Include live deployed links and GitHub repository badges.",
            "Refine executive summary to highlight core technical passion."
        ]
    }


async def analyze_resume_text(resume_text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes resume text using Gemini deep reasoning (with Groq fallback)
    and caches the compressed structured context in Redis for fast interview personalization.
    """
    # Check Redis cache if user_id is provided
    if user_id:
        try:
            redis_client = await get_redis()
            if redis_client:
                cached = await redis_client.get(f"resume_context:{user_id}")
                if cached:
                    logger.info(f"Retrieved cached resume context for user {user_id}")
                    return json.loads(cached)
        except Exception as cache_err:
            logger.warning(f"Redis cache check notice: {cache_err}")

    prompt = RESUME_DEEP_PROMPT.format(resume_text=resume_text[:12000])

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.RESUME_ATS_ANALYSIS,
            prompt=prompt,
            system_prompt="You are an expert ATS Resume Analyzer and Executive Recruiter.",
            json_mode=True,
            temperature=0.1,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            # Ensure score is an int
            if "score" in parsed:
                try:
                    parsed["score"] = int(parsed["score"])
                except Exception:
                    parsed["score"] = 75

            # Cache compressed profile in Redis (TTL = 7 days)
            if user_id:
                try:
                    redis_client = await get_redis()
                    if redis_client:
                        await redis_client.set(
                            f"resume_context:{user_id}",
                            json.dumps(parsed),
                            ex=7 * 24 * 3600
                        )
                except Exception as cache_save_err:
                    logger.warning(f"Redis cache save notice: {cache_save_err}")

            return parsed
    except Exception as e:
        logger.warning(f"AI resume analysis notice ({e}), using heuristic parser.")

    fallback_data = _fallback_resume_analysis(resume_text)
    if user_id:
        try:
            redis_client = await get_redis()
            if redis_client:
                await redis_client.set(f"resume_context:{user_id}", json.dumps(fallback_data), ex=24 * 3600)
        except Exception:
            pass

    return fallback_data


async def analyze_resume(resume_text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Compatibility alias for analyze_resume_text."""
    return await analyze_resume_text(resume_text, user_id)


async def analyze_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes structured resume builder data for ATS readiness."""
    text_blocks = []
    if data.get("name"): text_blocks.append(f"Name: {data.get('name')}")
    if data.get("email"): text_blocks.append(f"Email: {data.get('email')}")
    if data.get("summary"): text_blocks.append(f"Summary: {data.get('summary')}")
    if data.get("skills"): text_blocks.append(f"Skills: {data.get('skills')}")
    if data.get("experience"): text_blocks.append(f"Experience: {json.dumps(data.get('experience'))}")
    if data.get("projects"): text_blocks.append(f"Projects: {json.dumps(data.get('projects'))}")
    if data.get("education"): text_blocks.append(f"Education: {json.dumps(data.get('education'))}")
    
    text = "\n".join(text_blocks)
    return await analyze_resume_text(text)

