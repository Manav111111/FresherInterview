import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from app.services.kb_loader import kb_loader

logger = logging.getLogger("fresherai.skill_gap")

# Canonical synonym dictionary mapping common informal variations to official KB skill names
SKILL_SYNONYMS = {
    # Frontend
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next js": "Next.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "html5": "HTML",
    "html": "HTML",
    "css3": "CSS",
    "css": "CSS",
    "tailwind": "TailwindCSS",
    "tailwindcss": "TailwindCSS",
    "tailwind css": "TailwindCSS",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "redux toolkit": "State Management",
    "redux": "State Management",
    "zustand": "State Management",

    # Backend
    "py": "Python",
    "python3": "Python",
    "python": "Python",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "express": "Express",
    "expressjs": "Express",
    "express.js": "Express",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "restful": "REST APIs",
    "rest apis": "REST APIs",
    "api design": "API Design",
    "graphql": "GraphQL",

    # Databases
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "supabase": "Supabase",
    "redis": "Redis",
    "caching": "Caching",

    # DevOps & Cloud
    "docker": "Docker",
    "container": "Docker",
    "containers": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "CI/CD",
    "linux": "Linux",
    "git": "Git",
    "github": "Git",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "terraform": "Terraform",

    # AI & ML
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "retrieval-augmented generation": "RAG",
    "embeddings": "Embeddings",
    "embedding": "Embeddings",
    "vector search": "Vector Search",
    "vector db": "Vector Search",
    "vector database": "Vector Search",
    "qdrant": "Qdrant",
    "llm": "LLM Fundamentals",
    "llms": "LLM Fundamentals",
    "genai": "LLM Fundamentals",
    "generative ai": "LLM Fundamentals",
    "prompt engineering": "Prompt Engineering",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "ai agents": "AI Agents",
    "agents": "AI Agents",
    "agentic workflows": "AI Agents",
    "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "mlops": "MLOps",
}


class SkillGapEngine:
    """
    Evaluates candidate skills against canonical Knowledge Base role requirements.
    Normalizes candidate skills, matches canonical KB skills, identifies strong and
    missing skills, and orders missing skills respecting pedagogical prerequisites.
    """

    def __init__(self):
        self._canonical_skills = kb_loader.get_canonical_skills()
        self._canonical_roles = kb_loader.get_canonical_roles()

    def normalize_skill_name(self, raw_name: str) -> str:
        """
        Normalizes variations of skill names (e.g. 'ReactJS' -> 'React')
        to canonical names found in fresher_ai_kb.
        """
        if not raw_name:
            return ""

        cleaned = raw_name.strip()
        lower_clean = re.sub(r"[^\w\.\-\+\#]", " ", cleaned.lower()).strip()
        lower_clean = re.sub(r"\s+", " ", lower_clean)

        # 1. Direct synonym match
        if lower_clean in SKILL_SYNONYMS:
            return SKILL_SYNONYMS[lower_clean]

        # 2. Match against KB canonical names (case-insensitive)
        for s_id, s_data in self._canonical_skills.items():
            canonical_name = s_data["name"]
            if canonical_name.lower() == lower_clean:
                return canonical_name

        # 3. Substring match for compound strings
        for syn_key, syn_val in SKILL_SYNONYMS.items():
            if f" {syn_key} " in f" {lower_clean} ":
                return syn_val

        return cleaned

    def normalize_skills_list(self, skills: List[str]) -> List[str]:
        """Normalizes a list of candidate skill strings and removes duplicates."""
        normalized_set = set()
        for s in skills:
            norm = self.normalize_skill_name(s)
            if norm:
                normalized_set.add(norm)
        return sorted(list(normalized_set))

    def calculate_skill_gap(
        self,
        target_role: str,
        candidate_skills: List[str],
    ) -> Dict[str, Any]:
        """
        Compares candidate skills against target role required skills from fresher_ai_kb.
        Returns:
        - target_role_id
        - target_role_name
        - candidate_skills (normalized)
        - strong_skills
        - missing_skills (ordered by priority & prerequisites)
        - gap_percentage
        - readiness_score
        """
        role_data = kb_loader.match_role(target_role)
        if not role_data:
            # Fallback to AI Engineer if not matched
            role_data = kb_loader.get_canonical_roles().get("role_ai_engineer", {
                "role_id": "role_ai_engineer",
                "role_name": "AI Engineer",
                "core_skill_ids": [
                    "skill_python", "skill_llm_fundamentals", "skill_prompt_engineering",
                    "skill_embeddings", "skill_vector_search", "skill_rag", "skill_ai_agents",
                    "skill_langgraph", "skill_fastapi", "skill_docker"
                ]
            })

        role_id = role_data.get("role_id", "role_ai_engineer")
        role_name = role_data.get("role_name", target_role)

        # Retrieve core skills for this role
        core_skill_ids = role_data.get("core_skill_ids", [])
        if isinstance(core_skill_ids, str):
            core_skill_ids = [x.strip() for x in core_skill_ids.split(";") if x.strip()]

        required_skills: List[Dict[str, Any]] = []
        for s_id in core_skill_ids:
            if s_id in self._canonical_skills:
                required_skills.append(self._canonical_skills[s_id])
            else:
                # Basic representation
                name = s_id.replace("skill_", "").replace("_", " ").title()
                required_skills.append({
                    "skill_id": s_id,
                    "name": name,
                    "priority": "high",
                    "difficulty": "intermediate",
                    "prerequisites": "",
                })

        normalized_candidate = self.normalize_skills_list(candidate_skills)
        cand_lower_set = {s.lower() for s in normalized_candidate}

        strong_skills: List[Dict[str, Any]] = []
        partial_skills: List[Dict[str, Any]] = []
        missing_skills: List[Dict[str, Any]] = []

        # Related family map for partial detection (e.g. SQL -> PostgreSQL)
        related_families = {
            "postgresql": ["sql", "database", "relational database", "mysql"],
            "mongodb": ["nosql", "database", "document db"],
            "redis": ["caching", "cache", "in-memory"],
            "react": ["javascript", "js", "html", "css", "frontend"],
            "next.js": ["react", "javascript", "typescript"],
            "fastapi": ["python", "apis", "rest apis"],
            "docker": ["linux", "containers", "cli"],
            "kubernetes": ["docker", "containers", "devops"],
            "langchain": ["python", "llm fundamentals", "rag"],
            "langgraph": ["langchain", "python", "ai agents"],
            "rag": ["embeddings", "vector search", "python"],
        }

        for req in required_skills:
            req_name = req["name"]
            req_name_lower = req_name.lower()
            priority_val = str(req.get("priority", "high")).lower()

            # 1. Exact or direct match -> strong
            matched = False
            for cand in cand_lower_set:
                if cand == req_name_lower or cand in req_name_lower or req_name_lower in cand:
                    matched = True
                    break

            if matched:
                strong_skills.append({
                    "skill_id": req.get("skill_id", ""),
                    "name": req_name,
                    "status": "strong",
                    "priority": req.get("priority", "high"),
                })
            else:
                # 2. Check if partial match based on related family or prerequisites
                is_partial = False
                rel_keys = related_families.get(req_name_lower, [])
                for rk in rel_keys:
                    if any(cand == rk or rk in cand for cand in cand_lower_set):
                        is_partial = True
                        break

                prereq_str = str(req.get("prerequisites", "")).lower()
                if not is_partial and prereq_str:
                    if any(cand in prereq_str for cand in cand_lower_set):
                        is_partial = True

                item = {
                    "skill_id": req.get("skill_id", ""),
                    "name": req_name,
                    "priority": req.get("priority", "high"),
                    "difficulty": req.get("difficulty", "intermediate"),
                    "prerequisites": req.get("prerequisites", ""),
                    "what_to_learn": req.get("what_to_learn", ""),
                }

                if is_partial:
                    item["status"] = "partial"
                    partial_skills.append(item)
                else:
                    item["status"] = "missing"
                    missing_skills.append(item)

        # Sort missing and partial skills: beginner prerequisites first, high priority first
        priority_weights = {"critical": 4, "very_high": 3, "high": 2, "medium": 1, "low": 0}
        difficulty_weights = {"beginner": 0, "intermediate": 1, "advanced": 2, "production": 3, "all": 1}

        missing_skills.sort(
            key=lambda x: (
                difficulty_weights.get(x["difficulty"], 1),
                -priority_weights.get(x["priority"], 2),
            )
        )
        partial_skills.sort(
            key=lambda x: (
                difficulty_weights.get(x["difficulty"], 1),
                -priority_weights.get(x["priority"], 2),
            )
        )

        # Priority list = high/critical missing or partial skills
        priority_skills = [
            s for s in (missing_skills + partial_skills)
            if priority_weights.get(str(s.get("priority", "")).lower(), 0) >= 2
        ][:5]

        total_req = len(required_skills) or 1
        matched_score = len(strong_skills) + (0.5 * len(partial_skills))
        readiness_score = min(100, max(10, int((matched_score / total_req) * 100)))
        gap_percentage = 100 - readiness_score

        return {
            "target_role_id": role_id,
            "target_role_name": role_name,
            "candidate_skills": normalized_candidate,
            "strong_skills": strong_skills,
            "partial_skills": partial_skills,
            "missing_skills": missing_skills,
            "priority_skills": priority_skills,
            "skills": {
                "strong": [s["name"] for s in strong_skills],
                "partial": [s["name"] for s in partial_skills],
                "missing": [s["name"] for s in missing_skills],
                "priority": [s["name"] for s in priority_skills],
            },
            "total_required_skills": total_req,
            "readiness_score": readiness_score,
            "gap_percentage": gap_percentage,
        }


# Global singleton instance
skill_gap_engine = SkillGapEngine()
