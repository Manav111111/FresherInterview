"""
Fresher.AI Knowledge Base — Career Transitions Data Module
Structured transition pathways between tech roles, bridge skills, overlap percentages, and realistic timeframes.
"""

def _embed_transition(from_role, to_role, overlap, time, bridge_skills, advice):
    return (
        f"Career Transition: {from_role} -> {to_role}\n"
        f"Skill Overlap: {overlap}%\n"
        f"Estimated Transition Time: {time}\n"
        f"Key Bridge Skills Needed: {bridge_skills}\n"
        f"Strategic Advice: {advice}"
    )

CAREER_TRANSITIONS = [
    {
        "transition_id": "trans_sde_to_ai",
        "current_role_id": "role_sde",
        "target_role_id": "role_ai_engineer",
        "transition_title": "Software Development Engineer (SDE) -> AI Engineer",
        "skill_overlap_percentage": 65.0,
        "estimated_months_to_transition": "2 - 4 Months",
        "difficulty": "moderate",
        "key_bridge_skills_to_acquire": "skill_llm_fundamentals;skill_rag;skill_advanced_rag;skill_qdrant;skill_langgraph;skill_rag_evaluation",
        "already_mastered_advantages": "Strong coding fundamentals, data structures, algorithms, modular system architecture, and API design principles.",
        "recommended_portfolio_bridge_project": "proj_ai_001 (Enterprise Multimodal RAG with Qdrant & Citation Grounding)",
        "strategic_career_advice": "Leverage your backend engineering discipline (clean architecture, async code, testing) which 90% of amateur AI developers lack. Focus on vector database indexing and quantitative RAG evaluation.",
        "embedding_text": _embed_transition("SDE / Backend Developer", "AI Engineer", 65.0, "2-4 Months", "RAG, Vector DBs (Qdrant), LangGraph, LLM Evaluation", "Leverage strong backend discipline and build production RAG systems with rigorous evaluation benchmarks.")
    },
    {
        "transition_id": "trans_fe_to_fs",
        "current_role_id": "role_frontend_developer",
        "target_role_id": "role_full_stack_developer",
        "transition_title": "Frontend Developer -> Full Stack Developer",
        "skill_overlap_percentage": 60.0,
        "estimated_months_to_transition": "2 - 3 Months",
        "difficulty": "low",
        "key_bridge_skills_to_acquire": "skill_sql;skill_postgresql;skill_orm;skill_redis;skill_authentication;skill_docker",
        "already_mastered_advantages": "Deep mastery of JavaScript/TypeScript, React component state, asynchronous data fetching, and browser client lifecycle.",
        "recommended_portfolio_bridge_project": "proj_fs_001 (Full Stack SaaS Platform with Multi-Tenancy & Stripe Billing)",
        "strategic_career_advice": "Transition naturally through Next.js Server Components and Server Actions into backend API design and PostgreSQL relational data modeling.",
        "embedding_text": _embed_transition("Frontend Developer", "Full Stack Developer", 60.0, "2-3 Months", "PostgreSQL, SQL, Prisma, Redis, Authentication, Docker", "Transition via Next.js Server Components into relational database design and backend architecture.")
    },
    {
        "transition_id": "trans_be_to_devops",
        "current_role_id": "role_backend_developer",
        "target_role_id": "role_devops_engineer",
        "transition_title": "Backend Developer -> DevOps / Cloud Engineer",
        "skill_overlap_percentage": 50.0,
        "estimated_months_to_transition": "3 - 5 Months",
        "difficulty": "moderate",
        "key_bridge_skills_to_acquire": "skill_kubernetes;skill_terraform;skill_aws;skill_infrastructure_as_code;skill_monitoring",
        "already_mastered_advantages": "Understanding of server architecture, networking basics, API protocols, and software development lifecycles.",
        "recommended_portfolio_bridge_project": "proj_devops_001 (Production Kubernetes GitOps Platform on AWS)",
        "strategic_career_advice": "Emphasize Infrastructure as Code (Terraform) and Kubernetes orchestration; your programming background makes you exceptionally strong at automation scripting and Helm templating.",
        "embedding_text": _embed_transition("Backend Developer", "DevOps Engineer", 50.0, "3-5 Months", "Kubernetes, Terraform, AWS, Prometheus, ArgoCD", "Use software coding background to excel at Infrastructure as Code, Helm templating, and GitOps automation.")
    },
    {
        "transition_id": "trans_qa_to_sdet",
        "current_role_id": "role_qa_engineer",
        "target_role_id": "role_sde",
        "transition_title": "QA Engineer -> Software Development Engineer in Test (SDET) / SDE",
        "skill_overlap_percentage": 45.0,
        "estimated_months_to_transition": "3 - 6 Months",
        "difficulty": "moderate",
        "key_bridge_skills_to_acquire": "skill_data_structures;skill_algorithms;skill_python;skill_typescript;skill_cicd",
        "already_mastered_advantages": "Strong testing mindset, edge-case identification, bug triage, and quality assurance principles.",
        "recommended_portfolio_bridge_project": "proj_fs_002 (Distributed URL Shortener with Automated Test Suite)",
        "strategic_career_advice": "Focus heavily on Data Structures and Algorithms (LeetCode/NeetCode) and building full test automation frameworks integrated into GitHub Actions CI/CD pipelines.",
        "embedding_text": _embed_transition("QA Engineer", "SDET / SDE", 45.0, "3-6 Months", "Data Structures, Algorithms, Python/TS, CI/CD Pipelines", "Master Data Structures and Algorithms and build automated end-to-end testing frameworks in CI/CD.")
    },
    {
        "transition_id": "trans_ds_to_ai",
        "current_role_id": "role_data_scientist",
        "target_role_id": "role_ai_engineer",
        "transition_title": "Data Scientist -> AI Engineer",
        "skill_overlap_percentage": 55.0,
        "estimated_months_to_transition": "2 - 3 Months",
        "difficulty": "low",
        "key_bridge_skills_to_acquire": "skill_fastapi;skill_docker;skill_rag;skill_langgraph;skill_qdrant;skill_guardrails",
        "already_mastered_advantages": "Strong Python programming, statistical reasoning, model evaluation metrics, and embeddings intuition.",
        "recommended_portfolio_bridge_project": "proj_ai_001 (Enterprise Multimodal RAG with Qdrant)",
        "strategic_career_advice": "Move out of static Jupyter notebooks and into production software engineering: wrap models in FastAPI microservices, containerize with Docker, and build cyclical agentic workflows.",
        "embedding_text": _embed_transition("Data Scientist", "AI Engineer", 55.0, "2-3 Months", "FastAPI, Docker, RAG, LangGraph, Qdrant Vector DB", "Transition from Jupyter notebooks to production software engineering with FastAPI, Docker, and LangGraph.")
    }
]

def get_career_transitions():
    return CAREER_TRANSITIONS

def get_career_transitions_headers():
    return [
        "transition_id", "current_role_id", "target_role_id",
        "transition_title", "skill_overlap_percentage",
        "estimated_months_to_transition", "difficulty",
        "key_bridge_skills_to_acquire", "already_mastered_advantages",
        "recommended_portfolio_bridge_project", "strategic_career_advice",
        "embedding_text"
    ]
