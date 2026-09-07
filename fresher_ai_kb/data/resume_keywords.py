"""
Fresher.AI Knowledge Base — Resume Keywords Data Module
ATS-optimized keywords, high-impact action verbs, and power achievement bullets per role.
"""

def _embed_resume_kw(role_id, category, keyword, context):
    return f"Role: {role_id}\nCategory: {category}\nKeyword: {keyword}\nContext / Impact Example: {context}"

RESUME_KEYWORDS = [
    # AI ENGINEER
    {"keyword_id": "kw_ai_001", "role_id": "role_ai_engineer", "category": "Core Technology", "keyword": "Retrieval-Augmented Generation (RAG)", "importance_weight": 1.0, "frequency_in_job_postings": "94%",
     "action_verbs": "Architected, Implemented, Engineered, Deployed", "bullet_context_example": "Architected an Enterprise RAG platform using Qdrant and FastAPI, achieving 96% context retrieval precision on multi-format PDFs.",
     "related_skill_ids": "skill_rag;skill_advanced_rag;skill_qdrant", "embedding_text": _embed_resume_kw("role_ai_engineer", "Core Technology", "Retrieval-Augmented Generation (RAG)", "Architected an Enterprise RAG platform using Qdrant and FastAPI achieving 96% context retrieval precision.")},

    {"keyword_id": "kw_ai_002", "role_id": "role_ai_engineer", "category": "AI Frameworks", "keyword": "LangGraph & AI Agents", "importance_weight": 1.0, "frequency_in_job_postings": "88%",
     "action_verbs": "Orchestrated, Developed, Built, Designed", "bullet_context_example": "Engineered autonomous multi-agent workflows using LangGraph with state checkpointing and human-in-the-loop approval gates.",
     "related_skill_ids": "skill_ai_agents;skill_langgraph;skill_multi_agent_systems", "embedding_text": _embed_resume_kw("role_ai_engineer", "AI Frameworks", "LangGraph & AI Agents", "Engineered autonomous multi-agent workflows using LangGraph with state checkpointing and approval gates.")},

    {"keyword_id": "kw_ai_003", "role_id": "role_ai_engineer", "category": "Vector Databases", "keyword": "Qdrant Vector Database", "importance_weight": 0.9, "frequency_in_job_postings": "82%",
     "action_verbs": "Indexed, Optimized, Benchmarked, Queried", "bullet_context_example": "Optimized Qdrant HNSW vector index and payload filtering, supporting sub-30ms semantic similarity queries across 500k vectors.",
     "related_skill_ids": "skill_qdrant;skill_vector_search;skill_metadata_filtering", "embedding_text": _embed_resume_kw("role_ai_engineer", "Vector Databases", "Qdrant Vector Database", "Optimized Qdrant HNSW vector index and payload filtering supporting sub-30ms similarity queries across 500k vectors.")},

    {"keyword_id": "kw_ai_004", "role_id": "role_ai_engineer", "category": "AI Evaluation", "keyword": "RAGAS & LLM Evaluation", "importance_weight": 0.9, "frequency_in_job_postings": "76%",
     "action_verbs": "Evaluated, Benchmarked, Quantified, Validated", "bullet_context_example": "Implemented automated CI/CD RAG evaluation pipelines with RAGAS, maintaining >0.92 faithfulness and zero hallucinated citations.",
     "related_skill_ids": "skill_rag_evaluation;skill_llm_evaluation", "embedding_text": _embed_resume_kw("role_ai_engineer", "AI Evaluation", "RAGAS & LLM Evaluation", "Implemented automated CI/CD RAG evaluation pipelines with RAGAS maintaining >0.92 faithfulness.")},

    {"keyword_id": "kw_ai_005", "role_id": "role_ai_engineer", "category": "AI Security", "keyword": "Prompt Injection Mitigation", "importance_weight": 0.8, "frequency_in_job_postings": "70%",
     "action_verbs": "Secured, Hardened, Sanitized, Audited", "bullet_context_example": "Hardened AI production APIs with input guardrails and Microsoft Presidio PII masking, stopping 98% of prompt injection attacks.",
     "related_skill_ids": "skill_guardrails;skill_prompt_injection;skill_ai_security", "embedding_text": _embed_resume_kw("role_ai_engineer", "AI Security", "Prompt Injection Mitigation", "Hardened AI production APIs with input guardrails and Presidio PII masking stopping 98% of prompt injections.")},

    # FULL STACK / BACKEND DEVELOPER
    {"keyword_id": "kw_fs_001", "role_id": "role_full_stack_developer", "category": "Frontend Frameworks", "keyword": "Next.js 14 App Router & Server Components", "importance_weight": 1.0, "frequency_in_job_postings": "92%",
     "action_verbs": "Developed, Implemented, Streamlined, Re-architected", "bullet_context_example": "Built full-stack web applications using Next.js 14 App Router and React Server Components, cutting initial page load times by 40%.",
     "related_skill_ids": "skill_nextjs;skill_react;skill_typescript", "embedding_text": _embed_resume_kw("role_full_stack_developer", "Frontend Frameworks", "Next.js 14 App Router & Server Components", "Built full-stack applications with Next.js 14 App Router and RSC cutting load times by 40%.")},

    {"keyword_id": "kw_fs_002", "role_id": "role_full_stack_developer", "category": "Backend & Database", "keyword": "PostgreSQL & Prisma ORM", "importance_weight": 1.0, "frequency_in_job_postings": "90%",
     "action_verbs": "Designed, Migrated, Optimized, Normalized", "bullet_context_example": "Designed normalized relational schemas and optimized Prisma query joins in PostgreSQL, reducing slow query latency by 65%.",
     "related_skill_ids": "skill_postgresql;skill_sql;skill_orm", "embedding_text": _embed_resume_kw("role_full_stack_developer", "Backend & Database", "PostgreSQL & Prisma ORM", "Designed normalized relational schemas and optimized Prisma query joins in PostgreSQL reducing latency by 65%.")},

    {"keyword_id": "kw_fs_003", "role_id": "role_full_stack_developer", "category": "Caching & Performance", "keyword": "Redis In-Memory Caching", "importance_weight": 0.9, "frequency_in_job_postings": "85%",
     "action_verbs": "Cached, Accelerated, Scaled, Throttled", "bullet_context_example": "Implemented Cache-Aside pattern in Redis with distributed rate limiting, reducing database read load by 80% under peak traffic.",
     "related_skill_ids": "skill_redis;skill_caching", "embedding_text": _embed_resume_kw("role_full_stack_developer", "Caching & Performance", "Redis In-Memory Caching", "Implemented Cache-Aside pattern in Redis with distributed rate limiting reducing DB read load by 80%.")},

    {"keyword_id": "kw_fs_004", "role_id": "role_full_stack_developer", "category": "Authentication", "keyword": "JWT & OAuth 2.0 Authentication", "importance_weight": 0.9, "frequency_in_job_postings": "88%",
     "action_verbs": "Authenticated, Protected, Secured, Enforced", "bullet_context_example": "Secured REST APIs with rotating JWT tokens in HTTP-only cookies and OAuth2 social authentication with Role-Based Access Control.",
     "related_skill_ids": "skill_authentication;skill_authorization", "embedding_text": _embed_resume_kw("role_full_stack_developer", "Authentication", "JWT & OAuth 2.0 Authentication", "Secured REST APIs with rotating JWT tokens in HTTP-only cookies and OAuth2 social auth with RBAC.")},

    # DEVOPS ENGINEER
    {"keyword_id": "kw_devops_001", "role_id": "role_devops_engineer", "category": "Container Orchestration", "keyword": "Kubernetes & EKS Cluster Management", "importance_weight": 1.0, "frequency_in_job_postings": "95%",
     "action_verbs": "Orchestrated, Provisioned, Scaled, Deployed", "bullet_context_example": "Managed production AWS EKS Kubernetes clusters with HPA autoscaling rules and Helm charts, ensuring 99.99% application availability.",
     "related_skill_ids": "skill_kubernetes;skill_aws;skill_docker", "embedding_text": _embed_resume_kw("role_devops_engineer", "Container Orchestration", "Kubernetes & EKS Cluster Management", "Managed production AWS EKS clusters with HPA autoscaling rules and Helm charts ensuring 99.99% uptime.")},

    {"keyword_id": "kw_devops_002", "role_id": "role_devops_engineer", "category": "Infrastructure as Code", "keyword": "Terraform Cloud Provisioning", "importance_weight": 1.0, "frequency_in_job_postings": "91%",
     "action_verbs": "Automated, Modularized, Provisioned, Versioned", "bullet_context_example": "Automated 100% of AWS cloud infrastructure using modular Terraform HCL with remote state locking and multi-environment workspaces.",
     "related_skill_ids": "skill_terraform;skill_infrastructure_as_code;skill_aws", "embedding_text": _embed_resume_kw("role_devops_engineer", "Infrastructure as Code", "Terraform Cloud Provisioning", "Automated 100% of AWS infrastructure using modular Terraform HCL with remote state locking.")},

    {"keyword_id": "kw_devops_003", "role_id": "role_devops_engineer", "category": "CI/CD & GitOps", "keyword": "ArgoCD & GitHub Actions CI/CD", "importance_weight": 0.95, "frequency_in_job_postings": "88%",
     "action_verbs": "Continuous Integration, Continuous Deployment, GitOps, Automated", "bullet_context_example": "Built automated GitHub Actions CI pipelines with Trivy container security gates and declarative ArgoCD GitOps continuous delivery.",
     "related_skill_ids": "skill_cicd;skill_github_actions;skill_kubernetes", "embedding_text": _embed_resume_kw("role_devops_engineer", "CI/CD & GitOps", "ArgoCD & GitHub Actions CI/CD", "Built automated GitHub Actions CI pipelines with Trivy security gates and ArgoCD GitOps delivery.")},

    {"keyword_id": "kw_devops_004", "role_id": "role_devops_engineer", "category": "Observability", "keyword": "Prometheus & Grafana Observability", "importance_weight": 0.9, "frequency_in_job_postings": "85%",
     "action_verbs": "Monitored, Instrumented, Visualized, Alerted", "bullet_context_example": "Deployed Prometheus Operator and customized Grafana dashboards, tracking cluster Golden Signals and firing automated Slack alerts.",
     "related_skill_ids": "skill_monitoring;skill_kubernetes", "embedding_text": _embed_resume_kw("role_devops_engineer", "Observability", "Prometheus & Grafana Observability", "Deployed Prometheus Operator and Grafana dashboards tracking Golden Signals and automated Slack alerts.")},

    # DATA SCIENTIST
    {"keyword_id": "kw_ds_001", "role_id": "role_data_scientist", "category": "Machine Learning", "keyword": "Supervised Learning (XGBoost / LightGBM)", "importance_weight": 1.0, "frequency_in_job_postings": "92%",
     "action_verbs": "Modeled, Predicted, Trained, Evaluated", "bullet_context_example": "Trained gradient boosted decision tree models (XGBoost/LightGBM) with Optuna hyperparameter tuning, achieving 0.91 ROC-AUC score.",
     "related_skill_ids": "skill_supervised_learning;skill_scikit_learn;skill_model_evaluation", "embedding_text": _embed_resume_kw("role_data_scientist", "Machine Learning", "Supervised Learning (XGBoost / LightGBM)", "Trained gradient boosted models with Optuna tuning achieving 0.91 ROC-AUC score.")},

    {"keyword_id": "kw_ds_002", "role_id": "role_data_scientist", "category": "MLOps", "keyword": "MLflow & Model Tracking", "importance_weight": 0.9, "frequency_in_job_postings": "80%",
     "action_verbs": "Tracked, Registered, Versioned, Monitored", "bullet_context_example": "Instrumented MLflow experiment tracking and model registry, ensuring 100% reproducibility and tracking production data drift with Evidently AI.",
     "related_skill_ids": "skill_mlops;skill_model_deployment", "embedding_text": _embed_resume_kw("role_data_scientist", "MLOps", "MLflow & Model Tracking", "Instrumented MLflow experiment tracking and model registry tracking production data drift with Evidently AI.")}
]

def get_resume_keywords():
    return RESUME_KEYWORDS

def get_resume_keywords_headers():
    return [
        "keyword_id", "role_id", "category", "keyword", "importance_weight",
        "frequency_in_job_postings", "action_verbs", "bullet_context_example",
        "related_skill_ids", "embedding_text"
    ]
