"""
Fresher.AI Knowledge Base — Common Mistakes & Anti-Patterns Data Module
Real-world engineering pitfalls, junior developer traps, and how to avoid them.
"""

def _embed_mistake(title, role, cat, problem, fix):
    return (
        f"Mistake / Pitfall: {title}\n"
        f"Role: {role}\n"
        f"Category: {cat}\n"
        f"Why it Happens: {problem}\n"
        f"Correct Approach: {fix}"
    )

COMMON_MISTAKES = [
    # AI ENGINEERING MISTAKES
    {
        "mistake_id": "mistake_ai_001",
        "role_id": "role_ai_engineer",
        "category": "RAG Architecture",
        "mistake_title": "Naive Fixed-Character Chunking Without Context Overlap",
        "symptom": "RAG system returns fragmented, nonsensical answers or misses key context spanning sentence boundaries.",
        "why_it_happens": "Junior developers use arbitrary chunk size (e.g. 500 characters) without token overlap or document structure awareness, splitting sentences in half and severing semantic relationships.",
        "correct_approach": "Use RecursiveCharacterTextSplitter or Semantic Chunking with a 10-20% token overlap. For structured documents (Markdown/HTML), split along headers and paragraphs to preserve semantic units.",
        "interview_trap": "Interviewer asks: 'How do you choose chunk size for your RAG system?' Trap: Giving an arbitrary number like '500 words' without explaining embedding model token limits, semantic coherence, or overlap.",
        "embedding_text": _embed_mistake("Naive Fixed-Character Chunking", "AI Engineer", "RAG Architecture", "Arbitrary chunk sizes without overlap slice sentences in half destroying context.", "Use recursive character or semantic chunking with 15% token overlap respecting document structure.")
    },
    {
        "mistake_id": "mistake_ai_002",
        "role_id": "role_ai_engineer",
        "category": "Prompt Engineering & Security",
        "mistake_title": "Concatenating Untrusted User Input Directly into System Prompts",
        "symptom": "System gets hacked via simple prompt injections, ignores guidelines, leaks confidential system prompts or instructions.",
        "why_it_happens": "Treating user input as trustworthy text and using raw f-strings (f'System: You are an assistant. User said: {user_input}') instead of structured message roles.",
        "correct_approach": "Always separate system instructions into the 'system' message role and user input into the 'user' role. Enforce input guardrails, regex sanitization, and output moderation filters.",
        "interview_trap": "Interviewer asks: 'How do you secure your LLM API endpoints against prompt injection?' Trap: Saying 'I told the LLM in the prompt to never reveal its instructions.'",
        "embedding_text": _embed_mistake("Concatenating User Input into System Prompts", "AI Engineer", "AI Security", "Raw f-strings enable direct prompt injection and instruction override.", "Separate system and user message roles, apply input guardrails and validation layers.")
    },
    {
        "mistake_id": "mistake_ai_003",
        "role_id": "role_ai_engineer",
        "category": "Production Engineering",
        "mistake_title": "Lack of Quantitative RAG Evaluation (Relying on 'Vibe Checks')",
        "symptom": "Changing a prompt or chunking strategy silently breaks answers for 30% of user queries without anyone noticing.",
        "why_it_happens": "Evaluating AI systems by manually testing 3 favorite queries in the chat window instead of maintaining an automated test dataset with ground truth.",
        "correct_approach": "Build a Golden Dataset of 50-100 real question-context-answer triples and run automated evaluation with RAGAS (Faithfulness, Precision, Recall) on every pull request in CI/CD.",
        "interview_trap": "Interviewer asks: 'How do you know when your RAG system is ready for production?' Trap: Saying 'We tested it and the answers looked really good.'",
        "embedding_text": _embed_mistake("Lack of Quantitative Evaluation (Vibe Checks)", "AI Engineer", "Evaluation", "Manual testing of 3 queries fails to catch 30% regressions across edge cases.", "Maintain Golden Datasets and automated RAGAS CI/CD evaluation pipelines measuring Faithfulness and Recall.")
    },

    # BACKEND / FULL STACK MISTAKES
    {
        "mistake_id": "mistake_fs_001",
        "role_id": "role_full_stack_developer",
        "category": "Database Performance",
        "mistake_title": "The N+1 Query Problem in ORMs (Prisma / SQLAlchemy)",
        "symptom": "Database latency explodes from 20ms to 4000ms as record counts grow; database CPU spikes to 100%.",
        "why_it_happens": "Fetching a list of N parents (e.g. 100 users) and looping over them to fetch each child record (e.g. user orders) individually, triggering 1 + 100 = 101 separate SQL queries.",
        "correct_approach": "Use eager loading (e.g., Prisma 'include', SQLAlchemy 'joinedload', or SQL JOINs) to fetch all related records in a single query or two batch queries.",
        "interview_trap": "Interviewer presents an ORM code snippet looping over user objects to print order counts and asks why it's slow.",
        "embedding_text": _embed_mistake("The N+1 Query Problem in ORMs", "Full Stack / Backend", "Database Performance", "Looping over parent records to query children causes 100+ separate SQL calls.", "Use eager loading (include / joinedload) to batch fetch relationships in 1 SQL query.")
    },
    {
        "mistake_id": "mistake_fs_002",
        "role_id": "role_full_stack_developer",
        "category": "Security & Authentication",
        "mistake_title": "Storing JWT Access Tokens in Browser LocalStorage",
        "symptom": "User accounts get compromised via Cross-Site Scripting (XSS) attacks stealing tokens.",
        "why_it_happens": "LocalStorage is accessible by any JavaScript running on the page (including third-party scripts, analytics, or injected XSS payloads).",
        "correct_approach": "Store JWT tokens in HTTP-only, Secure, SameSite cookies which are completely inaccessible to client-side JavaScript. Implement short-lived access tokens with rotating refresh tokens.",
        "interview_trap": "Interviewer asks: 'Where do you store authentication tokens on the frontend?' Trap: Saying 'localStorage because it's easy to read with JavaScript.'",
        "embedding_text": _embed_mistake("Storing JWTs in LocalStorage", "Full Stack Developer", "Security", "LocalStorage is vulnerable to XSS token theft from malicious scripts.", "Store JWTs in HTTP-only, Secure, SameSite cookies with refresh token rotation.")
    },

    # DEVOPS MISTAKES
    {
        "mistake_id": "mistake_devops_001",
        "role_id": "role_devops_engineer",
        "category": "Containerization",
        "mistake_title": "Running Docker Containers as the Root User",
        "symptom": "Container breakout vulnerabilities allow attackers to gain root access to the host VM operating system.",
        "why_it_happens": "Docker defaults to running processes as root inside containers unless explicitly configured otherwise.",
        "correct_approach": "Always create a non-privileged user and group in your Dockerfile (e.g. USER appuser) and run application processes with minimal permissions.",
        "interview_trap": "Interviewer reviews a Dockerfile candidate provided and checks whether 'USER' instruction is present.",
        "embedding_text": _embed_mistake("Running Containers as Root", "DevOps Engineer", "Container Security", "Default root execution allows container escape exploits to compromise the host.", "Create non-root users in Dockerfiles (USER appuser) and enforce read-only filesystems.")
    }
]

def get_common_mistakes():
    return COMMON_MISTAKES

def get_common_mistakes_headers():
    return [
        "mistake_id", "role_id", "category", "mistake_title", "symptom",
        "why_it_happens", "correct_approach", "interview_trap", "embedding_text"
    ]
