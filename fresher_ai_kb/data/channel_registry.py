"""
Fresher.AI Knowledge Base — YouTube Channel Registry (Canonical)

This module defines the CANONICAL channel registry used by the backend
recommendation engine. It is the single source of truth for:
  - channel identity (id, name, url)
  - topic associations (for RAG scoring)
  - role mappings (for role-based prioritisation)
  - avatar fallback initials (if no real thumbnail is available)

IMPORTANT RULES:
  - Do NOT add logo URLs here. Logos come from YouTube directly.
  - Do NOT add subscriber counts. We do not have a reliable live source.
  - Do NOT mark channels as "YouTube verified". We have no API-level verification data.
  - Only add channels whose URLs you have manually confirmed resolve to the correct creator.
  - Set verified=False for any channel whose URL you are not 100% certain about.
"""

# fmt: off

CHANNEL_REGISTRY = [

    # ──────────────────────────────────────────────────────────────────────────
    # FULL STACK / FRONTEND / BACKEND (India)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "apna_college",
        "name": "Apna College",
        "channel_url": "https://www.youtube.com/@ApnaCollegeOfficial",
        "avatar_initials": "AC",
        "avatar_color": "#1565C0",           # stable fallback background colour
        "topics": ["DSA", "Web Development", "Java", "C++", "Placement"],
        "best_for": "DSA, Web Development, Java, and placement preparation",
        "roles": ["full_stack_developer", "frontend_developer", "sde"],
        "skills": ["dsa", "java", "cpp", "html", "css", "javascript", "react"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "codewithharry",
        "name": "CodeWithHarry",
        "channel_url": "https://www.youtube.com/@CodeWithHarry",
        "avatar_initials": "CWH",
        "avatar_color": "#37474F",
        "topics": ["Python", "Web Dev", "React", "DSA", "JavaScript"],
        "best_for": "Python, web development, JavaScript, and React in Hindi",
        "roles": ["full_stack_developer", "frontend_developer", "backend_developer"],
        "skills": ["python", "javascript", "html", "css", "react", "dsa"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "chai_aur_code",
        "name": "Chai aur Code",
        "channel_url": "https://www.youtube.com/@chaiaurcode",
        "avatar_initials": "CC",
        "avatar_color": "#E65100",
        "topics": ["JavaScript", "React", "Node.js", "Backend", "Full Stack"],
        "best_for": "JavaScript internals, React, Node.js, and backend development",
        "roles": ["full_stack_developer", "frontend_developer", "backend_developer"],
        "skills": ["javascript", "react", "nodejs", "nextjs"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "sheryians",
        "name": "Sheryians Coding School",
        "channel_url": "https://www.youtube.com/@sheryians",
        "avatar_initials": "SCS",
        "avatar_color": "#B71C1C",
        "topics": ["React", "MERN", "Full Stack", "JavaScript"],
        "best_for": "MERN stack, React, and modern frontend development",
        "roles": ["full_stack_developer", "frontend_developer"],
        "skills": ["react", "javascript", "nodejs", "mongodb"],
        "priority": 9,
        "verified": True,
    },
    {
        "channel_id": "thapa_technical",
        "name": "Thapa Technical",
        "channel_url": "https://www.youtube.com/@ThapaTechnical",
        "avatar_initials": "TT",
        "avatar_color": "#00695C",
        "topics": ["React", "Node.js", "Next.js", "TypeScript", "Full Stack"],
        "best_for": "React, Node.js, Next.js, and TypeScript in Hindi",
        "roles": ["full_stack_developer", "frontend_developer", "backend_developer"],
        "skills": ["react", "nodejs", "nextjs", "typescript"],
        "priority": 9,
        "verified": True,
    },

    # ──────────────────────────────────────────────────────────────────────────
    # AI / ML / GENAI
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "campusx",
        "name": "CampusX",
        "channel_url": "https://www.youtube.com/@campusx-official",
        "avatar_initials": "CX",
        "avatar_color": "#212121",
        "topics": ["Machine Learning", "Gen AI", "RAG", "LangChain", "Agentic AI"],
        "best_for": "Machine Learning, Generative AI, RAG, and Agentic AI systems",
        "roles": ["ai_engineer", "ml_engineer", "genai_engineer", "data_scientist"],
        "skills": ["machine_learning", "generative_ai", "rag", "langchain", "langgraph"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "krish_naik",
        "name": "Krish Naik",
        "channel_url": "https://www.youtube.com/@krishnaik06",
        "avatar_initials": "KN",
        "avatar_color": "#4527A0",
        "topics": ["Machine Learning", "LangChain", "Gen AI", "AWS", "MLOps"],
        "best_for": "Machine Learning, LangChain, Generative AI, and MLOps",
        "roles": ["ai_engineer", "ml_engineer", "data_scientist"],
        "skills": ["machine_learning", "generative_ai", "langchain", "aws", "python"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "codebasics",
        "name": "codebasics",
        "channel_url": "https://www.youtube.com/@codebasics",
        "avatar_initials": "CB",
        "avatar_color": "#00695C",
        "topics": ["Data Science", "Machine Learning", "Python", "SQL", "Power BI"],
        "best_for": "Data Science, Machine Learning, and Python for data roles",
        "roles": ["data_scientist", "ai_engineer", "ml_engineer"],
        "skills": ["data_science", "machine_learning", "python", "sql"],
        "priority": 9,
        "verified": True,
    },

    # ──────────────────────────────────────────────────────────────────────────
    # DSA / COMPETITIVE PROGRAMMING
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "take_u_forward",
        "name": "take U forward",
        "channel_url": "https://www.youtube.com/@takeUforward",
        "avatar_initials": "TUF",
        "avatar_color": "#4A148C",
        "topics": ["DSA", "Competitive Programming", "Interview Prep", "System Design"],
        "best_for": "DSA, competitive programming, and technical interview preparation",
        "roles": ["sde", "backend_developer", "full_stack_developer"],
        "skills": ["dsa", "cpp", "system_design"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "codehelp",
        "name": "CodeHelp - by Babbar",
        "channel_url": "https://www.youtube.com/@CodeHelp",
        "avatar_initials": "CH",
        "avatar_color": "#C62828",
        "topics": ["DSA", "C++", "Interview Prep", "OOPS"],
        "best_for": "Complete DSA with C++ for placement and technical interviews",
        "roles": ["sde", "backend_developer"],
        "skills": ["dsa", "cpp"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "kunal_kushwaha",
        "name": "Kunal Kushwaha",
        "channel_url": "https://www.youtube.com/@KunalKushwaha",
        "avatar_initials": "KK",
        "avatar_color": "#1B5E20",
        "topics": ["DSA", "Java", "Open Source", "DevOps Basics"],
        "best_for": "DSA with Java, open source contributions, and DevOps basics",
        "roles": ["sde", "backend_developer", "devops_engineer"],
        "skills": ["dsa", "java", "git"],
        "priority": 9,
        "verified": True,
    },

    # ──────────────────────────────────────────────────────────────────────────
    # DEVOPS / CLOUD
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "abhishek_veeramalla",
        "name": "Abhishek Veeramalla",
        "channel_url": "https://www.youtube.com/@AbhishekVeeramalla",
        "avatar_initials": "AV",
        "avatar_color": "#0D47A1",
        "topics": ["DevOps", "AWS", "Kubernetes", "Terraform", "Azure", "CI/CD"],
        "best_for": "DevOps, AWS, Kubernetes, Terraform, and Azure from zero to hero",
        "roles": ["devops_engineer", "cloud_engineer"],
        "skills": ["devops", "docker", "kubernetes", "aws", "terraform", "azure"],
        "priority": 10,
        "verified": True,
    },
    {
        "channel_id": "techworld_nana",
        "name": "TechWorld with Nana",
        "channel_url": "https://www.youtube.com/@TechWorldwithNana",
        "avatar_initials": "TWN",
        "avatar_color": "#1565C0",
        "topics": ["DevOps", "Docker", "Kubernetes", "CI/CD", "GitOps"],
        "best_for": "Docker, Kubernetes, and DevOps practices explained clearly",
        "roles": ["devops_engineer", "cloud_engineer"],
        "skills": ["docker", "kubernetes", "cicd", "devops"],
        "priority": 9,
        "verified": True,
    },

    # ──────────────────────────────────────────────────────────────────────────
    # SYSTEM DESIGN
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "gaurav_sen",
        "name": "Gaurav Sen",
        "channel_url": "https://www.youtube.com/@gkcs",
        "avatar_initials": "GS",
        "avatar_color": "#283593",
        "topics": ["System Design", "Distributed Systems", "HLD", "Scalability"],
        "best_for": "System design, distributed systems, and high-level design interviews",
        "roles": ["backend_developer", "full_stack_developer", "sde"],
        "skills": ["system_design", "distributed_systems"],
        "priority": 10,
        "verified": True,
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CS FUNDAMENTALS
    # ──────────────────────────────────────────────────────────────────────────
    {
        "channel_id": "gate_smashers",
        "name": "Gate Smashers",
        "channel_url": "https://www.youtube.com/@GateSmashers",
        "avatar_initials": "GS",
        "avatar_color": "#37474F",
        "topics": ["Computer Networks", "Operating Systems", "DBMS", "CS Core"],
        "best_for": "Computer Networks, Operating Systems, and core CS theory in Hindi",
        "roles": ["devops_engineer", "backend_developer", "sde"],
        "skills": ["networking", "os", "dbms"],
        "priority": 8,
        "verified": True,
    },
]


# ─── CHANNEL LOOKUP BY ID ───────────────────────────────────────────────────

def get_channel_registry() -> list:
    return CHANNEL_REGISTRY


def get_channel_by_id(channel_id: str) -> dict:
    for ch in CHANNEL_REGISTRY:
        if ch["channel_id"] == channel_id:
            return ch
    return {}


def get_channels_for_role(role_id: str) -> list:
    return [ch for ch in CHANNEL_REGISTRY if role_id in ch.get("roles", [])]
