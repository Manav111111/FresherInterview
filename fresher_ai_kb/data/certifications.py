"""
Fresher.AI Knowledge Base — Certifications Data Module
Industry-recognized certifications mapped to roles and career stages.
"""

def _embed_cert(name, issuer, role, diff, cost, value):
    return (
        f"Certification: {name}\n"
        f"Issuer: {issuer}\n"
        f"Target Role: {role}\n"
        f"Difficulty: {diff}\n"
        f"Exam Cost: {cost}\n"
        f"Career / Resume Value: {value}"
    )

CERTIFICATIONS = [
    {
        "cert_id": "cert_aws_saa",
        "title": "AWS Certified Solutions Architect – Associate (SAA-C03)",
        "issuer": "Amazon Web Services",
        "applicable_role_ids": "role_devops_engineer;role_cloud_engineer;role_backend_developer;role_solutions_architect;role_ai_engineer",
        "skill_ids": "skill_aws;skill_system_design;skill_networking_fundamentals;skill_security_fundamentals",
        "difficulty": "intermediate",
        "exam_cost_usd": 150,
        "validity_years": 3,
        "prerequisites_recommended": "6+ months AWS hands-on experience or completion of AWS Cloud Practitioner",
        "key_topics_tested": "Resilient architectures, high-performing architectures, secure applications, cost-optimized architectures (VPC, EC2, S3, RDS, Lambda, IAM)",
        "industry_recognition": "Gold standard for cloud infrastructure; universally recognized by top enterprise recruiters and tech companies.",
        "fresher_roi_score": 9.5,
        "official_url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
        "embedding_text": _embed_cert("AWS Certified Solutions Architect – Associate", "Amazon Web Services", "DevOps, Cloud, Backend, Solutions Architect", "Intermediate", "$150", "Gold standard cloud certification; highly recognized by enterprise recruiters.")
    },
    {
        "cert_id": "cert_k8s_cka",
        "title": "Certified Kubernetes Administrator (CKA)",
        "issuer": "Linux Foundation & CNCF",
        "applicable_role_ids": "role_devops_engineer;role_cloud_engineer;role_platform_engineer",
        "skill_ids": "skill_kubernetes;skill_docker;skill_linux;skill_networking_fundamentals",
        "difficulty": "hard",
        "exam_cost_usd": 395,
        "validity_years": 2,
        "prerequisites_recommended": "Strong Linux CLI proficiency and 6+ months working with containerized applications and Kubernetes clusters",
        "key_topics_tested": "100% hands-on performance-based exam: Cluster architecture, installation, configuration, workloads & scheduling, services & networking, storage, troubleshooting",
        "industry_recognition": "Highest tier DevOps practical credential. Verifies real hands-on command-line ability to build and troubleshoot Kubernetes clusters.",
        "fresher_roi_score": 9.0,
        "official_url": "https://www.cncf.io/certification/cka/",
        "embedding_text": _embed_cert("Certified Kubernetes Administrator (CKA)", "Linux Foundation / CNCF", "DevOps, Cloud, Platform Engineer", "Hard", "$395", "100% hands-on performance exam; top-tier validation of practical Kubernetes administration.")
    },
    {
        "cert_id": "cert_hashi_terraform",
        "title": "HashiCorp Certified: Terraform Associate (003)",
        "issuer": "HashiCorp",
        "applicable_role_ids": "role_devops_engineer;role_cloud_engineer;role_platform_engineer;role_devsecops_engineer",
        "skill_ids": "skill_terraform;skill_infrastructure_as_code",
        "difficulty": "medium",
        "exam_cost_usd": 70,
        "validity_years": 2,
        "prerequisites_recommended": "Basic cloud infrastructure understanding and hands-on Terraform workflow experience",
        "key_topics_tested": "IaC concepts, Terraform basics, Terraform CLI, modules, state management, Terraform Cloud capabilities",
        "industry_recognition": "Very high return on investment; strongly demonstrates infrastructure-as-code competence for entry/junior DevOps candidates.",
        "fresher_roi_score": 9.2,
        "official_url": "https://www.hashicorp.com/certification/terraform-associate",
        "embedding_text": _embed_cert("HashiCorp Certified: Terraform Associate", "HashiCorp", "DevOps, Cloud, Platform Engineer", "Medium", "$70", "High ROI certification demonstrating Infrastructure as Code and Terraform state mastery.")
    },
    {
        "cert_id": "cert_deeplearning_genai",
        "title": "Generative AI with Large Language Models Certificate",
        "issuer": "DeepLearning.AI & AWS (Coursera)",
        "applicable_role_ids": "role_ai_engineer;role_ml_engineer;role_data_scientist",
        "skill_ids": "skill_llm_fundamentals;skill_rag;skill_prompt_engineering;skill_fine_tuning",
        "difficulty": "intermediate",
        "exam_cost_usd": 49,
        "validity_years": 0,
        "prerequisites_recommended": "Python proficiency and foundational machine learning concepts",
        "key_topics_tested": "LLM lifecycle, pre-training, fine-tuning (PEFT, LoRA), RLHF, RAG architecture, LLM evaluation, agentic architectures",
        "industry_recognition": "Leading foundational credential for AI Engineers transitioning into production Generative AI applications.",
        "fresher_roi_score": 8.8,
        "official_url": "https://www.deeplearning.ai/courses/generative-ai-with-llms/",
        "embedding_text": _embed_cert("Generative AI with Large Language Models", "DeepLearning.AI / AWS", "AI Engineer, ML Engineer", "Intermediate", "$49/mo", "Leading foundational Generative AI credential covering LLM lifecycle, PEFT, LoRA, and RAG.")
    },
    {
        "cert_id": "cert_comptia_secplus",
        "title": "CompTIA Security+ (SY0-701)",
        "issuer": "CompTIA",
        "applicable_role_ids": "role_cybersecurity_engineer;role_devsecops_engineer;role_network_engineer",
        "skill_ids": "skill_security_fundamentals;skill_network_security;skill_cryptography;skill_owasp",
        "difficulty": "medium",
        "exam_cost_usd": 392,
        "validity_years": 3,
        "prerequisites_recommended": "CompTIA Network+ or 2 years equivalent networking/security experience",
        "key_topics_tested": "General security concepts, threats/vulnerabilities/mitigations, security architecture, security operations, security program management",
        "industry_recognition": "Industry baseline certification for entry-level cybersecurity and government / defense compliance roles.",
        "fresher_roi_score": 8.5,
        "official_url": "https://www.comptia.org/certifications/security",
        "embedding_text": _embed_cert("CompTIA Security+", "CompTIA", "Cybersecurity, DevSecOps, Network Engineer", "Medium", "$392", "Universal baseline security certification required by many enterprise and security operations teams.")
    }
]

def get_certifications():
    return CERTIFICATIONS

def get_certifications_headers():
    return [
        "cert_id", "title", "issuer", "applicable_role_ids", "skill_ids",
        "difficulty", "exam_cost_usd", "validity_years",
        "prerequisites_recommended", "key_topics_tested",
        "industry_recognition", "fresher_roi_score", "official_url",
        "embedding_text"
    ]
