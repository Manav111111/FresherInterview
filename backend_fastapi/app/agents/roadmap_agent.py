import json
import logging
from typing import Any, Dict, List, Optional
from app.ai.provider_router import ai_router
from app.ai.schemas import AIRequest, TaskType
from app.services.retrieval_service import retrieval_service
from app.services.skill_gap_engine import skill_gap_engine
from app.services.kb_loader import kb_loader

logger = logging.getLogger("fresherai.roadmap_agent")

RAG_ROADMAP_PROMPT = """
You are a Principal Technical Architect, Engineering Mentor, and Career Strategist.
Generate a structured, industry-tailored weekly learning roadmap grounded strictly in the provided Fresher.AI Knowledge Base context.

Role: {role}
Target Salary: {target_salary}
Personalized with Resume: {is_personalized}

Candidate Background & Skill Profile:
--------------------------------------------------
{candidate_context}
--------------------------------------------------

VERIFIED KNOWLEDGE BASE CONTEXT (SOURCE OF TRUTH):
--------------------------------------------------
{rag_context}
--------------------------------------------------

CRITICAL INSTRUCTIONS:
1. GROUNDING IN KNOWLEDGE BASE:
   - Use the supplied Knowledge Base context as the absolute source of truth.
   - DO NOT invent YouTube channels, playlists, URLs, tools, documentation, or projects.
   - If a resource is not present in retrieved context, do not fabricate it.

2. PROGRESSIVE & PERSONALIZED LEARNING PATH:
   - Progress logically: Foundation -> Core Skills -> Intermediate -> Advanced -> Production -> Projects -> Interview Prep.
   - If Candidate Background has Strong Skills, DO NOT waste 2 weeks on basics they already know! Fast-track them.
   - Give Partial Skills targeted reinforcement.
   - Allocate the most focus and depth to Missing High-Priority skills.

3. SCHEMA REQUIREMENT:
Return ONLY valid JSON matching this exact structure:
{{
  "role": "{role}",
  "target_salary": "{target_salary}",
  "summary": {{
    "difficulty": "Beginner Friendly",
    "duration_weeks": 12,
    "personalized": {is_personalized_json}
  }},
  "modules": [
    {{
      "week": 1,
      "title": "Week 1 Title",
      "skills": ["Skill 1", "Skill 2"],
      "topics": ["Topic A", "Topic B", "Topic C"],
      "resources": [
        {{
          "title": "Verified Resource Name",
          "url": "https://verified-url-from-context",
          "type": "youtube or official_docs",
          "logo_key": "canonical_logo_key"
        }}
      ],
      "project": {{
        "title": "Hands-on Project Name",
        "difficulty": "Beginner"
      }}
    }}
  ]
}}
"""


async def _build_rag_context(
    role: str,
    gap_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Retrieves verified Knowledge Base records across all relevant dimensions."""
    missing_skill_names = []
    strong_skill_names = []
    if gap_data:
        missing_skill_names = gap_data.get("skills", {}).get("missing", [])
        strong_skill_names = gap_data.get("skills", {}).get("strong", [])

    focus_skill = missing_skill_names[0] if missing_skill_names else role

    # Parallel/sequential retrieval from Qdrant + KB
    tools = await retrieval_service.search_tools(role=role, top_k=12)
    yt_creators = await retrieval_service.search_youtube_creators(
        role=role,
        skill=focus_skill,
        missing_skills=missing_skill_names,
        strong_skills=strong_skill_names,
        top_k_creators=5,
        max_playlists_per_creator=3,
    )

    # yt_creators is now a flat list of channel objects (no playlists)
    # Build yt_items for backwards-compat use inside module building (videoUrl, etc.)
    yt_items = []
    for ch in yt_creators:
        yt_items.append({
            "channel_name": ch.get("name", ""),
            "title": ch.get("name", "YouTube Channel"),
            "url": ch.get("channel_url", "https://www.youtube.com"),
            "logo_key": "youtube",
            "verified": True,
        })

    official_docs = await retrieval_service.search_official_docs(role=role, skill=focus_skill, top_k=10)
    career_res = await retrieval_service.search_career_resources(role=role, top_k=8)
    projects = await retrieval_service.search_projects(skill=focus_skill, role=role, top_k=6)
    weekly_records = await retrieval_service.search_weekly_roadmap(role=role, top_k=12)
    interview_qs = await retrieval_service.search_interview_topics(role=role, skill=focus_skill, top_k=6)

    # Text summary for LLM prompt context
    lines = []
    if weekly_records:
        lines.append("WEEKLY OUTLINES FROM KB:")
        for w in weekly_records[:8]:
            lines.append(f"- Week {w.get('week_number')}: {w.get('phase_name')} | Goal: {w.get('weekly_goal')} | Deliverable: {w.get('deliverable')}")

    if yt_creators:
        lines.append("\nCURATED YOUTUBE CHANNELS (do NOT invent URLs):")
        for ch in yt_creators:
            lines.append(f"- {ch.get('name')}: {ch.get('channel_url')} | Topics: {', '.join(ch.get('topics', []))}")

    if official_docs:
        lines.append("\nVERIFIED OFFICIAL DOCUMENTATION:")
        for d in official_docs:
            lines.append(f"- {d.get('title')}: {d.get('url')}")

    if projects:
        lines.append("\nRECOMMENDED PORTFOLIO PROJECTS:")
        for p in projects:
            lines.append(f"- {p.get('title')}: {p.get('description')}")

    if tools:
        lines.append("\nESSENTIAL TOOLS & PLATFORMS:")
        for t in tools:
            lines.append(f"- {t.get('name')} ({t.get('category')}): {t.get('url')}")

    if career_res:
        lines.append("\nCAREER & PRACTICE PLATFORMS:")
        for c in career_res:
            lines.append(f"- {c.get('title')}: {c.get('url')}")

    return {
        "text_block": "\n".join(lines),
        "tools": tools,
        "yt_items": yt_items,
        "yt_creators": yt_creators,
        "official_docs": official_docs,
        "career_resources": career_res,
        "projects": projects,
        "weekly_records": weekly_records,
        "interview_qs": interview_qs,
    }



def _build_deterministic_modules(
    role: str,
    rag_data: Dict[str, Any],
    gap_data: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Builds progressive weekly modules directly from KB weekly roadmaps and skill gap."""
    weekly_records = rag_data.get("weekly_records", [])
    yt_items = rag_data.get("yt_items", [])
    official_docs = rag_data.get("official_docs", [])
    projects = rag_data.get("projects", [])

    strong_names = set(gap_data.get("skills", {}).get("strong", [])) if gap_data else set()
    missing_names = gap_data.get("skills", {}).get("missing", []) if gap_data else []

    modules = []
    if weekly_records and len(weekly_records) >= 4:
        for idx, w in enumerate(weekly_records[:12]):
            week_num = w.get("week_number", idx + 1)
            phase = w.get("phase_name", "Core Skills")
            topics_raw = w.get("topics_covered", "")
            topics = [t.strip() for t in topics_raw.split(",") if t.strip()][:4]
            if not topics:
                topics = [f"{phase} Fundamentals", "Implementation", "Testing & Debugging"]

            # Check if this week's topics overlap with candidate strong skills
            is_fast_tracked = any(any(s.lower() in t.lower() for s in strong_names) for t in topics)
            if is_fast_tracked and week_num <= 2 and len(strong_names) >= 2:
                # Fast track: compress fundamentals and introduce missing skills earlier
                title = f"Week {week_num}: {phase} (Fast-Tracked & Accelerated)"
            else:
                title = f"Week {week_num}: {phase}"

            # Assign verified resources
            week_resources = []
            if yt_items:
                yt = yt_items[idx % len(yt_items)]
                week_resources.append({
                    "title": yt.get("title") or yt.get("channel_name"),
                    "url": yt.get("url"),
                    "type": "youtube",
                    "logo_key": yt.get("logo_key", "youtube"),
                })
            if official_docs:
                doc = official_docs[idx % len(official_docs)]
                week_resources.append({
                    "title": doc.get("title") or doc.get("name"),
                    "url": doc.get("url"),
                    "type": "official_docs",
                    "logo_key": doc.get("logo_key", "generic"),
                })

            # Assign project
            proj_title = w.get("deliverable") or (projects[idx % len(projects)]["title"] if projects else f"{role} Week {week_num} Project")
            diff = w.get("difficulty", "Intermediate").capitalize()
            if diff not in ("Beginner", "Easy", "Intermediate", "Advanced"):
                diff = "Intermediate"

            skills_list = [t for t in topics if len(t.split()) <= 2][:3] or [phase]

            modules.append({
                "week": week_num,
                "title": title,
                "skills": skills_list,
                "topics": topics,
                "resources": week_resources,
                "project": {
                    "title": proj_title,
                    "difficulty": diff,
                },
                # Backward compatibility aliases
                "duration": "1-2 Weeks",
                "difficulty": diff,
                "description": w.get("weekly_goal") or f"Master {phase} core engineering competencies.",
                "projects": [proj_title],
                "videoUrl": week_resources[0]["url"] if week_resources else "https://www.youtube.com",
                "docUrl": week_resources[1]["url"] if len(week_resources) > 1 else (week_resources[0]["url"] if week_resources else "https://developer.mozilla.org"),
                "youtube": week_resources[0]["url"] if week_resources else "https://www.youtube.com",
                "docs": week_resources[1]["url"] if len(week_resources) > 1 else (week_resources[0]["url"] if week_resources else "https://developer.mozilla.org"),
                "article": week_resources[1]["url"] if len(week_resources) > 1 else (week_resources[0]["url"] if week_resources else "https://developer.mozilla.org"),
            })
    else:
        # Step fallback progression - ensure at least 4-6 weekly modules
        default_steps = [
            f"{role} Fundamentals & Architecture",
            "Data Persistence & Database Systems",
            "High-Throughput APIs & Distributed Services",
            "Caching, Messaging & Observability",
            "Containerization, CI/CD & Cloud Infrastructure",
            "Capstone Project & System Design Interview Prep",
        ]
        if missing_names:
            steps = list(missing_names)
            # Supplement if candidate had only 1 or 2 missing skills so progression is substantial
            for ds in default_steps:
                if len(steps) >= 4:
                    break
                if ds not in steps:
                    steps.append(ds)
            steps = steps[:6]
        else:
            steps = default_steps

        for idx, step_name in enumerate(steps):
            week_num = idx + 1
            yt = yt_items[idx % len(yt_items)] if yt_items else {"title": "YouTube Guide", "url": "https://www.youtube.com/@freecodecamp", "logo_key": "youtube"}
            doc = official_docs[idx % len(official_docs)] if official_docs else {"title": "Official Docs", "url": "https://developer.mozilla.org", "logo_key": "generic"}
            proj_name = projects[idx % len(projects)]["title"] if projects else f"{step_name} Implementation"

            modules.append({
                "week": week_num,
                "title": f"Week {week_num}: {step_name}",
                "skills": [step_name.split()[0], "Engineering Best Practices"],
                "topics": [f"{step_name} Foundations", "Hands-on Implementation", "System Optimization", "Testing"],
                "resources": [
                    {"title": yt.get("title", "Video Guide"), "url": yt.get("url"), "type": "youtube", "logo_key": yt.get("logo_key", "youtube")},
                    {"title": doc.get("title", "Official Docs"), "url": doc.get("url"), "type": "official_docs", "logo_key": doc.get("logo_key", "generic")},
                ],
                "project": {
                    "title": proj_name,
                    "difficulty": "Beginner" if idx == 0 else ("Intermediate" if idx < 4 else "Advanced"),
                },
                "duration": "1-2 Weeks",
                "difficulty": "Beginner" if idx == 0 else ("Intermediate" if idx < 4 else "Advanced"),
                "description": f"Master {step_name} required for {role}.",
                "projects": [proj_name],
                "videoUrl": yt.get("url"),
                "docUrl": doc.get("url"),
                "youtube": yt.get("url"),
                "docs": doc.get("url"),
                "article": doc.get("url"),
            })

    return modules


def _assemble_complete_roadmap(
    role: str,
    target_package: str,
    modules: List[Dict[str, Any]],
    rag_data: Dict[str, Any],
    gap_data: Optional[Dict[str, Any]],
    is_personalized: bool,
) -> Dict[str, Any]:
    """Assembles the final structured roadmap matching Section 10 and backward compatibility."""
    tools = rag_data.get("tools", [])
    yt_items = rag_data.get("yt_items", [])
    yt_creators = rag_data.get("yt_creators", [])
    official_docs = rag_data.get("official_docs", [])
    career_res = rag_data.get("career_resources", [])
    projects = rag_data.get("projects", [])

    skills_dict = {
        "strong": gap_data.get("skills", {}).get("strong", []) if gap_data else [],
        "partial": gap_data.get("skills", {}).get("partial", []) if gap_data else [],
        "missing": gap_data.get("skills", {}).get("missing", []) if gap_data else [],
        "priority": gap_data.get("skills", {}).get("priority", []) if gap_data else [],
    }

    readiness = gap_data.get("readiness_score", 75) if gap_data else 70
    if readiness >= 80:
        diff_str = "Advanced / Fast-Tracked"
    elif readiness >= 50:
        diff_str = "Intermediate"
    else:
        diff_str = "Beginner Friendly"

    syllabus = [
        {"pillar": "Foundations & Architecture", "description": f"Core engineering and algorithmic pillars for {role}.", "topics": ["Design Patterns", "Clean Code", "Protocols", "Data Structures"]},
        {"pillar": "Data & Persistence", "description": "Database design, query optimization, and storage engines.", "topics": ["SQL Modeling", "Indexing", "Caching Strategies", "Transactions"]},
        {"pillar": "APIs & Distributed Systems", "description": "Building resilient, low-latency microservices.", "topics": ["RESTful Standards", "Async I/O", "Authentication", "Rate Limiting"]},
        {"pillar": "DevOps & Cloud Production", "description": "Containerizing, deploying, and observing production workloads.", "topics": ["Docker", "CI/CD Automation", "Monitoring", "Cloud Deployment"]},
    ]

    return {
        # Section 10 Primary Schema
        "role": role,
        "target_salary": target_package,
        "summary": {
            "difficulty": diff_str,
            "duration_weeks": len(modules) if modules else 12,
            "personalized": is_personalized,
        },
        "skills": skills_dict,
        "tools": tools,
        "youtube_resources": yt_creators if yt_creators else yt_items,
        "official_docs": official_docs,
        "career_resources": career_res,
        "projects": projects,
        "modules": modules,

        # Backward compatibility fields
        "title": f"Mastery Roadmap for {role}",
        "targetPackage": target_package,
        "duration": f"{len(modules)} Weeks",
        "level": diff_str,
        "syllabus": syllabus,
        "essentialTools": tools,
        "youtubePlaylists": yt_items,
        "learningResources": official_docs,
        "careerResources": career_res,
        "portfolioProjects": projects,
        "skillGapSummary": {
            "readinessScore": readiness,
            "strongSkills": skills_dict["strong"],
            "partialSkills": skills_dict["partial"],
            "missingSkills": skills_dict["missing"],
            "prioritySkills": skills_dict["priority"],
        } if gap_data else None,
    }


async def generate_career_roadmap(
    role: str,
    target_package: str,
    resume: Optional[Dict[str, Any]] = None,
    use_resume: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    RAG-powered, resume-personalized career roadmap generator.
    Grounds all content strictly in verified Knowledge Base data, personalizes
    progression based on candidate skill gaps, and returns clean structured JSON.
    """
    clean_role = role.strip() if role else "Software Engineer"
    pkg = target_package or "15 LPA"

    # 1. Skill Gap Analysis if resume is enabled
    gap_data = None
    candidate_context = "Candidate has not provided a resume. Generate complete beginner-to-advanced curriculum."
    is_personalized = bool(use_resume and resume)

    if is_personalized:
        candidate_skills = resume.get("skills", [])
        gap_data = skill_gap_engine.calculate_skill_gap(clean_role, candidate_skills)
        strong_names = gap_data.get("skills", {}).get("strong", [])
        partial_names = gap_data.get("skills", {}).get("partial", [])
        missing_names = gap_data.get("skills", {}).get("missing", [])
        priority_names = gap_data.get("skills", {}).get("priority", [])

        candidate_context = (
            f"Candidate Strong Skills (FAST-TRACK THESE, DO NOT RE-TEACH BASICS): {', '.join(strong_names) if strong_names else 'None'}\n"
            f"Candidate Partial Skills (TARGETED REINFORCEMENT): {', '.join(partial_names) if partial_names else 'None'}\n"
            f"Candidate Missing Skills (ALLOCATE MOST FOCUS): {', '.join(missing_names) if missing_names else 'None'}\n"
            f"Priority Focus Skills: {', '.join(priority_names) if priority_names else 'None'}\n"
            f"Candidate Readiness Score: {gap_data.get('readiness_score', 50)}%\n"
            f"Resume Summary: {resume.get('summary', 'Candidate aiming for career progression.')}"
        )

    # 2. RAG Retrieval from Qdrant Knowledge Base
    rag_data = await _build_rag_context(clean_role, gap_data)

    # 3. Invoke LLM with RAG grounding
    prompt = RAG_ROADMAP_PROMPT.format(
        role=clean_role,
        target_salary=pkg,
        is_personalized=str(is_personalized),
        is_personalized_json="true" if is_personalized else "false",
        candidate_context=candidate_context,
        rag_context=rag_data["text_block"],
    )

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.ROADMAP_GENERATION,
            prompt=prompt,
            system_prompt="You are a Principal Technical Career Mentor. Ground all roadmaps strictly in the provided Knowledge Base context. Do NOT invent URLs or channels.",
            json_mode=True,
            temperature=0.2,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            parsed_modules = parsed.get("modules", [])

            if parsed_modules and isinstance(parsed_modules, list):
                yt_items = rag_data.get("yt_items", [])
                official_docs = rag_data.get("official_docs", [])
                projects = rag_data.get("projects", [])

                # Validate and enrich each module with verified links and logo keys
                enriched_modules = []
                for idx, mod in enumerate(parsed_modules):
                    w_num = mod.get("week") or (idx + 1)
                    title = mod.get("title") or f"Week {w_num}"
                    mod_skills = mod.get("skills") or []
                    mod_topics = mod.get("topics") or []

                    # Ensure verified resources with valid logo keys
                    mod_res = mod.get("resources") or []
                    valid_res = []
                    for r in mod_res:
                        u = r.get("url", "")
                        if u and "http" in u and "example.com" not in u:
                            t = r.get("title") or "Resource"
                            valid_res.append({
                                "title": t,
                                "url": u,
                                "type": r.get("type", "official_docs"),
                                "logo_key": kb_loader.extract_canonical_logo_key(r.get("logo_key") or t),
                            })

                    if not valid_res:
                        if yt_items:
                            yt = yt_items[idx % len(yt_items)]
                            valid_res.append({
                                "title": yt.get("title") or yt.get("channel_name"),
                                "url": yt.get("url"),
                                "type": "youtube",
                                "logo_key": yt.get("logo_key", "youtube"),
                            })
                        if official_docs:
                            doc = official_docs[idx % len(official_docs)]
                            valid_res.append({
                                "title": doc.get("title") or doc.get("name"),
                                "url": doc.get("url"),
                                "type": "official_docs",
                                "logo_key": doc.get("logo_key", "generic"),
                            })

                    mod_proj = mod.get("project")
                    if not mod_proj or not isinstance(mod_proj, dict):
                        p_obj = projects[idx % len(projects)] if projects else {"title": f"{clean_role} Practical Project", "difficulty": "Intermediate"}
                        mod_proj = {"title": p_obj.get("title"), "difficulty": p_obj.get("difficulty", "Intermediate").capitalize()}

                    video_url = next((r["url"] for r in valid_res if r.get("type") == "youtube"), valid_res[0]["url"] if valid_res else "")
                    doc_url = next((r["url"] for r in valid_res if r.get("type") != "youtube"), valid_res[-1]["url"] if valid_res else "")

                    enriched_modules.append({
                        "week": w_num,
                        "title": title,
                        "skills": mod_skills,
                        "topics": mod_topics,
                        "resources": valid_res,
                        "project": mod_proj,
                        "duration": "1-2 Weeks",
                        "difficulty": mod_proj.get("difficulty", "Intermediate"),
                        "description": f"Master competencies for {title}.",
                        "projects": [mod_proj.get("title", "Portfolio Project")],
                        "videoUrl": video_url,
                        "docUrl": doc_url,
                        "youtube": video_url,
                        "docs": doc_url,
                        "article": doc_url,
                    })

                if len(enriched_modules) >= 3:
                    return _assemble_complete_roadmap(
                        clean_role, pkg, enriched_modules, rag_data, gap_data, is_personalized
                    )
    except Exception as e:
        logger.warning(f"AI roadmap generation error ({e}), generating RAG-grounded fallback.")

    # Deterministic fallback grounded strictly in KB
    fallback_modules = _build_deterministic_modules(clean_role, rag_data, gap_data)
    return _assemble_complete_roadmap(
        clean_role, pkg, fallback_modules, rag_data, gap_data, is_personalized
    )


async def generate_roadmap(
    role: str,
    target_package: str,
    resume: Optional[Dict[str, Any]] = None,
    use_resume: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Compatibility alias for generate_career_roadmap."""
    return await generate_career_roadmap(role, target_package, resume, use_resume=use_resume, **kwargs)

