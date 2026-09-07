"""
Fresher.AI Knowledge Base — Market Signals Data Module
2025–2026 Tech Market Intelligence, hiring demand, salary bands, and emerging trends.
"""

def _embed_market_signal(role_id, role_name, demand_trend, yoy_growth, salary_inr, salary_usd, top_skills):
    return (
        f"Role: {role_name} ({role_id})\n"
        f"Demand Trend: {demand_trend}\n"
        f"YoY Hiring Growth: {yoy_growth}\n"
        f"Fresher/Entry Salary (India): {salary_inr}\n"
        f"Fresher/Entry Salary (US): {salary_usd}\n"
        f"Most In-Demand Skills: {top_skills}"
    )

MARKET_SIGNALS = [
    {
        "signal_id": "sig_ai_001",
        "role_id": "role_ai_engineer",
        "role_name": "AI Engineer",
        "demand_trend": "Exponentially Rising",
        "yoy_hiring_growth_percent": 142.0,
        "entry_salary_inr_lpa": "12.0 - 24.0 LPA",
        "entry_salary_usd_k": "$115k - $165k",
        "mid_salary_inr_lpa": "24.0 - 45.0 LPA",
        "mid_salary_usd_k": "$160k - $240k",
        "senior_salary_inr_lpa": "45.0 - 80.0+ LPA",
        "senior_salary_usd_k": "$230k - $380k+",
        "remote_friendly_score": 9,
        "hiring_sectors": "Enterprise SaaS, FinTech, HealthTech, Developer Tooling, Autonomous Systems",
        "top_in_demand_skills": "skill_rag;skill_langgraph;skill_qdrant;skill_fastapi;skill_guardrails;skill_ai_agents",
        "emerging_trends_2026": "Autonomous multi-agent orchestration, local SLM deployment on edge/quantized hardware, structured synthetic evaluation datasets (RAGAS), and strict AI security guardrails.",
        "market_risk_or_headwind": "Commoditization of simple prompt wrapper startups; companies require deep systems engineering skills (FastAPI, Redis, Docker, vector DB indexing) rather than surface-level API calls.",
        "embedding_text": _embed_market_signal("role_ai_engineer", "AI Engineer", "Exponentially Rising", "+142%", "12.0 - 24.0 LPA", "$115k - $165k", "RAG, LangGraph, Qdrant, FastAPI, Guardrails, AI Agents")
    },
    {
        "signal_id": "sig_fs_001",
        "role_id": "role_full_stack_developer",
        "role_name": "Full Stack Developer",
        "demand_trend": "Consistently High",
        "yoy_hiring_growth_percent": 28.0,
        "entry_salary_inr_lpa": "6.0 - 14.0 LPA",
        "entry_salary_usd_k": "$85k - $125k",
        "mid_salary_inr_lpa": "14.0 - 28.0 LPA",
        "mid_salary_usd_k": "$125k - $180k",
        "senior_salary_inr_lpa": "28.0 - 55.0+ LPA",
        "senior_salary_usd_k": "$175k - $260k+",
        "remote_friendly_score": 8,
        "hiring_sectors": "Startups, E-Commerce, B2B SaaS, IT Services, Consumer Tech",
        "top_in_demand_skills": "skill_nextjs;skill_react;skill_typescript;skill_postgresql;skill_redis;skill_docker",
        "emerging_trends_2026": "Next.js App Router & Server Components dominance, full TypeScript end-to-end type safety, integration of AI copilot APIs into existing web applications.",
        "market_risk_or_headwind": "Basic HTML/CSS/JS junior developers without modern framework and backend database depth face fierce competition.",
        "embedding_text": _embed_market_signal("role_full_stack_developer", "Full Stack Developer", "Consistently High", "+28%", "6.0 - 14.0 LPA", "$85k - $125k", "Next.js, React, TypeScript, PostgreSQL, Redis, Docker")
    },
    {
        "signal_id": "sig_devops_001",
        "role_id": "role_devops_engineer",
        "role_name": "DevOps Engineer",
        "demand_trend": "High & Critical",
        "yoy_hiring_growth_percent": 45.0,
        "entry_salary_inr_lpa": "8.0 - 16.0 LPA",
        "entry_salary_usd_k": "$95k - $140k",
        "mid_salary_inr_lpa": "16.0 - 32.0 LPA",
        "mid_salary_usd_k": "$140k - $200k",
        "senior_salary_inr_lpa": "32.0 - 65.0+ LPA",
        "senior_salary_usd_k": "$195k - $300k+",
        "remote_friendly_score": 9,
        "hiring_sectors": "Cloud Infrastructure, FinTech, Healthcare, Enterprise Tech, Web3",
        "top_in_demand_skills": "skill_kubernetes;skill_terraform;skill_aws;skill_cicd;skill_docker;skill_monitoring",
        "emerging_trends_2026": "GitOps with ArgoCD, Platform Engineering internal developer portals (Backstage), Kubernetes cost optimization (FinOps), and cloud-native security (DevSecOps).",
        "market_risk_or_headwind": "Manual sysadmin workflows are obsolete; companies mandate 100% Infrastructure as Code (Terraform) and container orchestration.",
        "embedding_text": _embed_market_signal("role_devops_engineer", "DevOps Engineer", "High & Critical", "+45%", "8.0 - 16.0 LPA", "$95k - $140k", "Kubernetes, Terraform, AWS, CI/CD, Docker, Prometheus")
    },
    {
        "signal_id": "sig_ds_001",
        "role_id": "role_data_scientist",
        "role_name": "Data Scientist",
        "demand_trend": "Steady & Maturing",
        "yoy_hiring_growth_percent": 22.0,
        "entry_salary_inr_lpa": "7.0 - 15.0 LPA",
        "entry_salary_usd_k": "$90k - $135k",
        "mid_salary_inr_lpa": "15.0 - 30.0 LPA",
        "mid_salary_usd_k": "$135k - $190k",
        "senior_salary_inr_lpa": "30.0 - 55.0+ LPA",
        "senior_salary_usd_k": "$185k - $275k+",
        "remote_friendly_score": 8,
        "hiring_sectors": "Banking, Insurance, Healthcare Analytics, Retail, Supply Chain",
        "top_in_demand_skills": "skill_statistics;skill_pandas;skill_supervised_learning;skill_scikit_learn;skill_mlops;skill_sql",
        "emerging_trends_2026": "Convergence toward MLOps (model deployment and monitoring) and integration with Generative AI / tabular foundation models.",
        "market_risk_or_headwind": "Pure exploratory Jupyter notebook analysis is no longer enough; hiring managers demand software engineering and model productionization skills.",
        "embedding_text": _embed_market_signal("role_data_scientist", "Data Scientist", "Steady & Maturing", "+22%", "7.0 - 15.0 LPA", "$90k - $135k", "Statistics, Pandas, Supervised Learning, scikit-learn, MLOps, SQL")
    }
]

def get_market_signals():
    return MARKET_SIGNALS

def get_market_signals_headers():
    return [
        "signal_id", "role_id", "role_name", "demand_trend",
        "yoy_hiring_growth_percent", "entry_salary_inr_lpa",
        "entry_salary_usd_k", "mid_salary_inr_lpa", "mid_salary_usd_k",
        "senior_salary_inr_lpa", "senior_salary_usd_k", "remote_friendly_score",
        "hiring_sectors", "top_in_demand_skills", "emerging_trends_2026",
        "market_risk_or_headwind", "embedding_text"
    ]
