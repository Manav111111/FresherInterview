import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fresherai.kb_loader")

# Path to fresher_ai_kb
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
KB_DIR = os.path.join(BASE_DIR, "fresher_ai_kb")
KB_DATA_DIR = os.path.join(KB_DIR, "data")
KB_JSON_DIR = os.path.join(KB_DIR, "json_export")

# Add KB_DIR to sys.path if not present
if KB_DIR not in sys.path:
    sys.path.insert(0, KB_DIR)


class KnowledgeBaseLoader:
    """
    Single source of truth loader for Fresher.AI Knowledge Base.
    Loads and normalizes all canonical career data from fresher_ai_kb
    for ingestion into Qdrant, skill normalization, and RAG retrieval.
    """

    def __init__(self):
        self._payloads_cache: Optional[List[Dict[str, Any]]] = None
        self._skills_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._roles_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._resources_cache: Optional[List[Dict[str, Any]]] = None
        self._playlists_cache: Optional[List[Dict[str, Any]]] = None
        self._projects_cache: Optional[List[Dict[str, Any]]] = None
        self._roadmaps_cache: Optional[List[Dict[str, Any]]] = None

    def load_ingestion_payloads(self) -> List[Dict[str, Any]]:
        """
        Loads all structured records ready for Qdrant embedding and upsert.
        Uses fresher_ai_kb/json_export/qdrant_ingestion_payloads.json if present,
        or dynamically generates from fresher_ai_kb.data modules.
        """
        if self._payloads_cache is not None:
            return self._payloads_cache

        payloads_file = os.path.join(KB_JSON_DIR, "qdrant_ingestion_payloads.json")
        if os.path.exists(payloads_file):
            try:
                with open(payloads_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                logger.info(f"Loaded {len(records)} pre-exported records from {payloads_file}")
                self._payloads_cache = self._normalize_payloads(records)
                return self._payloads_cache
            except Exception as e:
                logger.warning(f"Failed loading json_export/qdrant_ingestion_payloads.json ({e}). Generating dynamically.")

        # Dynamic fallback from data package
        records = self._generate_from_data_modules()
        self._payloads_cache = self._normalize_payloads(records)
        return self._payloads_cache

    def _generate_from_data_modules(self) -> List[Dict[str, Any]]:
        """Generates ingestion points directly from fresher_ai_kb data modules."""
        records = []
        try:
            from data import SHEETS_REGISTRY, get_playlists

            for sheet in SHEETS_REGISTRY:
                sheet_name = sheet["name"]
                data = sheet["data_fn"]()
                for item in data:
                    point_id = (
                        item.get("role_id")
                        or item.get("skill_id")
                        or item.get("roadmap_id")
                        or item.get("project_id")
                        or item.get("resource_id")
                        or item.get("channel_id")
                        or item.get("question_id")
                        or item.get("keyword_id")
                        or item.get("matrix_id")
                        or item.get("signal_id")
                        or item.get("cert_id")
                        or item.get("tool_id")
                        or item.get("mistake_id")
                        or item.get("transition_id")
                        or item.get("schema_id")
                    )
                    emb_text = item.get("embedding_text", "")
                    payload = dict(item)
                    if "embedding_text" in payload:
                        del payload["embedding_text"]

                    records.append({
                        "id": point_id,
                        "entity_type": sheet_name,
                        "payload": payload,
                        "embedding_text": emb_text,
                    })

            # Add playlists
            for pl in get_playlists():
                records.append({
                    "id": pl.get("playlist_id"),
                    "entity_type": "Playlist",
                    "payload": pl,
                    "embedding_text": f"Playlist: {pl.get('playlist_name')}\nChannel: {pl.get('channel_name')}\nSkill: {pl.get('skill_area')}\nRole: {pl.get('role_area')}",
                })
        except Exception as e:
            logger.error(f"Error generating records from KB data modules: {e}")

        return records

    def _normalize_payloads(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizes fields across all KB records for consistent Qdrant indexing."""
        normalized = []
        for r in raw_records:
            pid = str(r.get("id") or "")
            entity_type = r.get("entity_type") or "Knowledge"
            payload = dict(r.get("payload") or {})
            emb_text = r.get("embedding_text") or ""

            # Ensure role_ids is a clean list of strings
            raw_roles = payload.get("role_ids") or payload.get("applicable_role_ids") or []
            if isinstance(raw_roles, str):
                role_ids = [x.strip() for x in raw_roles.split(";") if x.strip()]
            elif isinstance(raw_roles, list):
                role_ids = [str(x).strip() for x in raw_roles if str(x).strip()]
            else:
                role_ids = []
            if payload.get("role_id"):
                role_ids.append(str(payload.get("role_id")).strip())
            payload["role_ids"] = list(set(role_ids))

            # Ensure skill_ids is a clean list of strings
            raw_skills = payload.get("skill_ids") or payload.get("core_skill_ids") or []
            if isinstance(raw_skills, str):
                skill_ids = [x.strip() for x in raw_skills.split(";") if x.strip()]
            elif isinstance(raw_skills, list):
                skill_ids = [str(x).strip() for x in raw_skills if str(x).strip()]
            else:
                skill_ids = []
            if payload.get("skill_id"):
                skill_ids.append(str(payload.get("skill_id")).strip())
            payload["skill_ids"] = list(set(skill_ids))

            # Normalize difficulty
            difficulty = (
                payload.get("difficulty")
                or payload.get("recommended_level")
                or payload.get("level")
                or "all"
            )
            payload["difficulty"] = str(difficulty).lower().strip()

            # Ensure canonical logo_key in metadata (NO SVG or image data)
            raw_name = (
                payload.get("name")
                or payload.get("tool_name")
                or payload.get("skill_name")
                or payload.get("channel_name")
                or payload.get("platform_name")
                or payload.get("title")
                or pid
            )
            existing_logo_key = payload.get("logo_key") or payload.get("icon_key")
            payload["logo_key"] = KnowledgeBaseLoader.extract_canonical_logo_key(existing_logo_key or raw_name)

            # Ensure common lookup keys
            payload["record_id"] = pid
            payload["entity_type"] = entity_type

            # Ensure meaningful embedding text (pure semantic knowledge, no image data or logo URLs)
            if not emb_text:
                title = payload.get("title") or payload.get("name") or payload.get("skill_name") or payload.get("role_name") or pid
                desc = payload.get("description") or payload.get("weekly_goal") or payload.get("best_for") or ""
                emb_text = f"Entity: {entity_type}\nTitle: {title}\nDescription: {desc}"

            normalized.append({
                "id": pid,
                "entity_type": entity_type,
                "payload": payload,
                "embedding_text": emb_text,
            })

        return normalized

    @staticmethod
    def extract_canonical_logo_key(name_or_key: str) -> str:
        """Determines canonical logo key for UI resolution without storing image URLs."""
        if not name_or_key:
            return "generic"
        k = "".join(c for c in str(name_or_key).lower() if c.isalnum())
        if "langgraph" in k: return "langgraph"
        if "fastmcp" in k or "mcp" in k: return "fastmcp"
        if "groq" in k: return "groq"
        if "qdrant" in k: return "qdrant"
        if "langchain" in k: return "langchain"
        if "gemini" in k: return "gemini"
        if "openai" in k or "chatgpt" in k: return "openai"
        if "claude" in k or "anthropic" in k: return "claude"
        if "huggingface" in k or "hf" in k: return "huggingface"
        if "pytorch" in k: return "pytorch"
        if "tensorflow" in k or "tf" in k: return "tensorflow"
        if "scikitlearn" in k or "sklearn" in k: return "scikitlearn"
        if "colab" in k: return "colab"
        if "python" in k: return "python"
        if "typescript" in k or k == "ts": return "typescript"
        if "javascript" in k or k == "js": return "javascript"
        if "fastapi" in k: return "fastapi"
        if "flask" in k: return "flask"
        if "django" in k: return "django"
        if "nextjs" in k or k == "next": return "nextjs"
        if "react" in k: return "react"
        if "nodejs" in k or "node" in k: return "nodejs"
        if "express" in k: return "express"
        if "tailwind" in k: return "tailwind"
        if "vite" in k: return "vite"
        if "flutter" in k: return "flutter"
        if "expo" in k: return "expo"
        if "android" in k: return "android"
        if "postgres" in k or "psql" in k or "sql" in k: return "postgresql"
        if "mongodb" in k or "mongo" in k: return "mongodb"
        if "supabase" in k: return "supabase"
        if "firebase" in k: return "firebase"
        if "redis" in k: return "redis"
        if "prisma" in k: return "prisma"
        if "docker" in k: return "docker"
        if "kubernetes" in k or "k8s" in k: return "kubernetes"
        if "aws" in k or "amazon" in k: return "aws"
        if "vercel" in k: return "vercel"
        if "github" in k: return "github"
        if "git" in k: return "git"
        if "linux" in k or "ubuntu" in k: return "linux"
        if "postman" in k: return "postman"
        if "figma" in k: return "figma"
        if "pydantic" in k: return "pydantic"
        if "logfire" in k: return "logfire"
        if "stripe" in k: return "stripe"
        if "razorpay" in k: return "razorpay"
        if "kaggle" in k: return "kaggle"
        if "linkedin" in k: return "linkedin"
        if "wellfound" in k or "angellist" in k: return "wellfound"
        if "geeksforgeeks" in k or k == "gfg": return "geeksforgeeks"
        if "leetcode" in k: return "leetcode"
        if "youtube" in k: return "youtube"
        if "freecodecamp" in k: return "freecodecamp"
        if "deeplearningai" in k or "coursera" in k: return "deeplearningai"
        return k or "generic"

    def get_canonical_skills(self) -> Dict[str, Dict[str, Any]]:
        """Returns mapping of skill_id -> skill metadata for all canonical skills."""
        if self._skills_cache is not None:
            return self._skills_cache

        skills_map = {}
        for r in self.load_ingestion_payloads():
            if r["entity_type"] in ("Skills", "Foundation"):
                payload = r["payload"]
                skill_id = payload.get("skill_id") or r["id"]
                name = payload.get("skill_name") or payload.get("name")
                if name:
                    skills_map[skill_id] = {
                        "skill_id": skill_id,
                        "name": name,
                        "category": payload.get("category", "General"),
                        "priority": payload.get("priority", "high"),
                        "difficulty": payload.get("difficulty", "beginner"),
                        "prerequisites": payload.get("prerequisites", ""),
                        "what_to_learn": payload.get("what_to_learn", ""),
                        "tools": payload.get("tools", ""),
                        "applicable_role_ids": payload.get("role_ids", []),
                        "source": payload.get("source", ""),
                    }
        self._skills_cache = skills_map
        return self._skills_cache

    def get_canonical_roles(self) -> Dict[str, Dict[str, Any]]:
        """Returns mapping of role_id -> role metadata for all canonical roles."""
        if self._roles_cache is not None:
            return self._roles_cache

        roles_map = {}
        for r in self.load_ingestion_payloads():
            if r["entity_type"] == "Roles":
                payload = r["payload"]
                role_id = payload.get("role_id") or r["id"]
                name = payload.get("role_name")
                if name:
                    roles_map[role_id] = {
                        "role_id": role_id,
                        "role_name": name,
                        "category": payload.get("category", ""),
                        "description": payload.get("description", ""),
                        "core_skill_ids": payload.get("skill_ids", []),
                        "interview_focus": payload.get("interview_focus", ""),
                        "resume_focus": payload.get("resume_focus", ""),
                    }
        self._roles_cache = roles_map
        return self._roles_cache

    def match_role(self, role_query: str) -> Optional[Dict[str, Any]]:
        """Finds closest canonical role by name or alias."""
        roles = self.get_canonical_roles()
        q = role_query.lower().strip()

        # 1. Exact or substring match
        for r_id, r_data in roles.items():
            name = r_data["role_name"].lower()
            if q == name or q in name or name in q:
                return r_data

        # 2. Common role synonyms
        synonyms = {
            "ai": "role_ai_engineer",
            "genai": "role_ai_engineer",
            "ai engineer": "role_ai_engineer",
            "generative ai": "role_ai_engineer",
            "full stack": "role_full_stack_developer",
            "fullstack": "role_full_stack_developer",
            "frontend": "role_frontend_developer",
            "front end": "role_frontend_developer",
            "backend": "role_backend_developer",
            "back end": "role_backend_developer",
            "devops": "role_devops_engineer",
            "data scientist": "role_data_scientist",
            "data science": "role_data_scientist",
            "ml": "role_ml_engineer",
            "machine learning": "role_ml_engineer",
            "cloud": "role_cloud_engineer",
        }
        for syn, target_id in synonyms.items():
            if syn in q and target_id in roles:
                return roles[target_id]

        return None


# Global singleton instance
kb_loader = KnowledgeBaseLoader()
