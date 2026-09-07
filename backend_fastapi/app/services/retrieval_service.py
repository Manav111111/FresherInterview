import json
import logging
from typing import Any, Dict, List, Optional
from app.config import settings
from app.core.redis import get_cache, set_cache
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.kb_loader import kb_loader

logger = logging.getLogger("fresherai.retrieval")


class RetrievalService:
    """
    RAG Retrieval Layer for Fresher.AI.
    Combines semantic embedding similarity with precise metadata filtering across Qdrant
    and integrates Redis caching for low-latency recommendations.
    """

    def __init__(self):
        self._qdrant = qdrant_service
        self._embedding = embedding_service

    async def _search_with_cache(
        self,
        cache_key: str,
        query_text: str,
        entity_type: Optional[Any] = None,
        role_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        # 1. Check Redis cache
        cached = await get_cache(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        # 2. Compute query vector
        query_vec = await self._embedding.get_embedding(query_text)

        # 3. Query Qdrant
        results = self._qdrant.search(
            query_vector=query_vec,
            top_k=top_k,
            entity_type=entity_type,
            role_id=role_id,
            skill_id=skill_id,
            difficulty=difficulty,
            score_threshold=score_threshold,
        )

        # 4. Cache in Redis
        try:
            await set_cache(cache_key, json.dumps(results), ex=settings.RAG_CACHE_TTL)
        except Exception as cache_err:
            logger.debug(f"Redis cache save notice: {cache_err}")

        return results

    async def search_resources(
        self,
        skill: str,
        role: Optional[str] = None,
        difficulty: Optional[str] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Retrieves verified documentation and learning resources for a given skill and role."""
        role_id = None
        if role:
            matched = kb_loader.match_role(role)
            if matched:
                role_id = matched.get("role_id")

        cache_key = f"rag:res:{role or 'all'}:{skill}:{difficulty or 'all'}:{top_k}"
        query_text = f"Skill: {skill} documentation tutorials courses guides"

        hits = await self._search_with_cache(
            cache_key=cache_key,
            query_text=query_text,
            entity_type=["Resources", "resources"],
            role_id=role_id,
            difficulty=difficulty.lower() if difficulty else None,
            top_k=top_k,
        )

        resources = []
        for h in hits:
            p = h.get("payload", {})
            title = p.get("title") or p.get("resource_name") or p.get("name")
            url = p.get("url") or p.get("link")
            if title and url:
                resources.append({
                    "title": title,
                    "name": title,
                    "url": url,
                    "type": p.get("resource_type") or p.get("type", "Documentation"),
                    "difficulty": p.get("difficulty", "all"),
                    "source": p.get("source", "Official Docs"),
                    "is_free": p.get("is_free", True),
                    "logo_key": p.get("logo_key") or kb_loader.extract_canonical_logo_key(title),
                    "score": h.get("score", 0.0),
                })

        # Enrich from KB resources module if needed
        if len(resources) < top_k:
            try:
                from data.resources import get_resources
                clean_r = (role or "").lower()
                clean_s = (skill or "").lower()
                for r in get_resources():
                    r_text = str(r.get("embedding_text", "")).lower()
                    r_roles = str(r.get("applicable_role_ids", "")).lower()
                    if (role_id and role_id.lower() in r_roles) or (clean_r and clean_r in r_text) or (clean_s and clean_s in r_text):
                        u = r.get("url")
                        t = r.get("title")
                        if u and t and not any(x["url"] == u for x in resources):
                            resources.append({
                                "title": t,
                                "name": t,
                                "url": u,
                                "type": r.get("resource_type") or r.get("type", "Documentation"),
                                "difficulty": r.get("difficulty", "all"),
                                "source": r.get("source", "Official Docs"),
                                "is_free": r.get("is_free", True),
                                "logo_key": kb_loader.extract_canonical_logo_key(t),
                                "score": 1.0,
                            })
                            if len(resources) >= top_k:
                                break
            except Exception as e:
                logger.debug(f"Direct resources enrichment notice: {e}")

        return resources

    async def search_youtube(
        self,
        skill: str,
        role: Optional[str] = None,
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """Retrieves verified YouTube channels and playlists for a given skill and role."""
        role_id = None
        if role:
            matched = kb_loader.match_role(role)
            if matched:
                role_id = matched.get("role_id")

        cache_key = f"rag:yt:{role or 'all'}:{skill}:{top_k}"
        query_text = f"YouTube channel playlist video tutorials for {skill} {role or ''}"

        hits = []
        try:
            hits = await self._search_with_cache(
                cache_key=cache_key,
                query_text=query_text,
                entity_type=["YouTube_Channels", "Playlist", "playlists"],
                role_id=role_id,
                top_k=top_k,
            )
        except Exception as q_err:
            logger.debug(f"Qdrant search_youtube notice ({q_err}). Using KB data directly.")

        yt_items = []
        for h in hits:
            p = h.get("payload", {})
            channel = p.get("channel_name") or p.get("name")
            playlist = p.get("playlist_name")
            url = p.get("url") or p.get("playlist_recommendation")

            title = playlist if playlist else channel
            if title and url:
                yt_items.append({
                    "channel_name": channel or title,
                    "title": title,
                    "handle": p.get("handle", ""),
                    "url": url,
                    "language": p.get("language", "English"),
                    "best_for": p.get("best_for", ""),
                    "recommended_topics": p.get("recommended_topics", ""),
                    "logo_key": kb_loader.extract_canonical_logo_key(channel or title or "youtube"),
                    "score": h.get("score", 0.0),
                })

        # Enrich and guarantee all curated channels and playlists from KB
        try:
            from data.youtube_channels import get_youtube_channels, get_playlists
            clean_role_lower = (role or "").lower()
            clean_skill_lower = (skill or "").lower()

            # 1. Add matching curated playlists
            for pl in get_playlists():
                pl_role = str(pl.get("role_area", "")).lower()
                pl_skill = str(pl.get("skill_area", "")).lower()
                if (clean_role_lower and clean_role_lower in pl_role) or \
                   (clean_skill_lower and clean_skill_lower in pl_skill) or \
                   (clean_role_lower and clean_role_lower in pl_skill) or \
                   ("ai" in clean_role_lower and "ai" in pl_role):
                    u = pl.get("url")
                    if u and not any(x["url"] == u for x in yt_items):
                        yt_items.append({
                            "channel_name": pl.get("channel_name", "Curated Channel"),
                            "title": pl.get("playlist_name", "Master Playlist"),
                            "handle": "",
                            "url": u,
                            "language": pl.get("language", "English"),
                            "best_for": f"{pl.get('skill_area', 'Role')} master curriculum playlist",
                            "recommended_topics": pl.get("skill_area", ""),
                            "logo_key": kb_loader.extract_canonical_logo_key(pl.get("channel_name", "youtube")),
                            "score": 1.0,
                        })

            # 2. Add matching curated channels
            for ch in get_youtube_channels():
                ch_roles = str(ch.get("role_ids", "")).lower()
                ch_skills = str(ch.get("skill_ids", "")).lower()
                ch_embed = str(ch.get("embedding_text", "")).lower()
                if (role_id and role_id.lower() in ch_roles) or \
                   (clean_role_lower and clean_role_lower in ch_embed) or \
                   (clean_role_lower and clean_role_lower in ch_roles) or \
                   (clean_skill_lower and clean_skill_lower in ch_skills) or \
                   ("ai" in clean_role_lower and ("genai" in ch_embed or "machine learning" in ch_embed or "langgraph" in ch_embed)):
                    u = ch.get("playlist_recommendation") or ch.get("url")
                    ch_name = ch.get("channel_name")
                    if u and ch_name and not any(x.get("channel_name") == ch_name for x in yt_items):
                        yt_items.append({
                            "channel_name": ch_name,
                            "title": ch_name,
                            "handle": ch.get("handle", ""),
                            "url": u,
                            "language": ch.get("language", "English"),
                            "best_for": ch.get("best_for", ""),
                            "recommended_topics": ch.get("recommended_topics", ""),
                            "logo_key": kb_loader.extract_canonical_logo_key(ch_name),
                            "score": 1.0,
                        })
        except Exception as e:
            logger.debug(f"Direct youtube enrichment notice: {e}")

        return yt_items

    async def search_youtube_creators(
        self,
        role: str,
        skill: Optional[str] = None,
        missing_skills: Optional[List[str]] = None,
        strong_skills: Optional[List[str]] = None,
        top_k_creators: int = 5,
        max_playlists_per_creator: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves curated YouTube creators and their handpicked playlists tailored
        to the candidate's target role and skill gaps.
        Returns up to top_k_creators (default 5), with 2-3 verified playlists per creator.
        Strictly excludes unverified or pending resources.
        """
        try:
            from data.youtube_channels import get_playlists
        except ImportError:
            from fresher_ai_kb.data.youtube_channels import get_playlists

        role_lower = (role or "").lower()
        missing = [s.lower() for s in (missing_skills or [])]
        strong = [s.lower() for s in (strong_skills or [])]

        # 1. Determine role domain priority
        role_priority_channels: List[str] = []
        if any(k in role_lower for k in ["ai", "genai", "machine learning", "ml", "data science"]):
            # AI Engineer priority: CampusX -> Krish Naik -> Codebasics
            role_priority_channels = ["campusx", "krish_naik", "codebasics"]
        elif any(k in role_lower for k in ["devops", "cloud", "sre", "kubernetes", "infrastructure"]):
            # DevOps priority: Abhishek Veeramalla -> Gate Smashers
            role_priority_channels = ["abhishek_veeramalla", "gate_smashers"]
        elif any(k in role_lower for k in ["system design", "architect"]):
            # System Design priority: Gaurav Sen
            role_priority_channels = ["gaurav_sen"]
        elif any(k in role_lower for k in ["dsa", "algorithm", "competitive", "placement"]):
            # DSA / Placement priority: Take U Forward -> CodeHelp -> Kunal Kushwaha -> Apna College -> CodeWithHarry
            role_priority_channels = ["take_u_forward", "codehelp", "kunal_kushwaha", "apna_college", "codewithharry"]
        elif "backend" in role_lower:
            # Backend priority: Chai aur Code -> CodeWithHarry -> Thapa Technical -> Sheryians -> Apna College
            role_priority_channels = ["chai_aur_code", "codewithharry", "thapa_technical", "sheryians", "apna_college"]
        else:
            # Full Stack / Frontend default: Apna College -> CodeWithHarry -> Chai aur Code -> Sheryians -> Thapa Technical
            role_priority_channels = ["apna_college", "codewithharry", "chai_aur_code", "sheryians", "thapa_technical"]

        # 2. Filter verified playlists from registry
        all_playlists = get_playlists()
        verified_playlists = [
            pl for pl in all_playlists
            if pl.get("verified") is True and pl.get("verification_status") == "verified"
        ]

        # 3. Group playlists by creator and score each playlist based on candidate profile
        creators_dict: Dict[str, Dict[str, Any]] = {}

        for pl in verified_playlists:
            ch_id = pl.get("channel_id")
            if not ch_id:
                continue

            # Initialize creator profile if new
            if ch_id not in creators_dict:
                creators_dict[ch_id] = {
                    "channel": {
                        "id": ch_id,
                        "name": pl.get("channel_name", "Creator"),
                        "url": pl.get("channel_url", f"https://www.youtube.com/@{ch_id}"),
                        "logo_key": pl.get("logo_key") or ch_id,
                        "subscribers": pl.get("subscribers", "Verified Creator"),
                        "tags": pl.get("tags", [])[:3],
                    },
                    "scored_playlists": [],
                }

            # Score individual playlist based on relevance & skill gaps
            base_priority = pl.get("priority", 5)
            score = float(base_priority)

            pl_text = f"{pl.get('playlist_name', '')} {pl.get('skill_area', '')} {pl.get('skill_ids', '')}".lower()
            pl_role_area = str(pl.get("role_area", "")).lower()

            # Boost if playlist matches target role
            if any(k in pl_role_area or k in pl_text for k in role_lower.split()):
                score += 4.0

            # Missing skills get maximum boost
            for ms in missing:
                if ms in pl_text:
                    score += 6.0

            # If candidate already has strong mastery of the skill, demote beginner tutorials (e.g. Python basics)
            for ss in strong:
                if ss in pl_text and ("beginner" in pl_text or "crash course" in pl_text or "fundamentals" in pl_text):
                    score -= 5.0

            creators_dict[ch_id]["scored_playlists"].append((score, pl))

        # 4. Filter creators that have relevant playlists for this role or are in priority list
        candidate_creators = []
        for ch_id, data in creators_dict.items():
            playlists_with_scores = data["scored_playlists"]
            if not playlists_with_scores:
                continue

            # Channel base rank score
            channel_score = 0.0
            if ch_id in role_priority_channels:
                idx = role_priority_channels.index(ch_id)
                channel_score = 100.0 - (idx * 10.0)
            else:
                # Secondary matching based on top playlist scores
                top_p_score = max(s for s, _ in playlists_with_scores)
                channel_score = top_p_score

            candidate_creators.append((channel_score, ch_id, data))

        # Sort creators by channel score descending
        candidate_creators.sort(key=lambda x: x[0], reverse=True)

        # 5. Format top creators with their top 2-3 playlists
        result: List[Dict[str, Any]] = []
        for _, ch_id, data in candidate_creators[:top_k_creators]:
            # Sort this creator's playlists by score descending
            data["scored_playlists"].sort(key=lambda x: x[0], reverse=True)
            top_pls = [pl for _, pl in data["scored_playlists"][:max_playlists_per_creator]]

            formatted_playlists = []
            for pl in top_pls:
                # Clean up skills array
                skill_raw = pl.get("skill_ids", "")
                skill_list = [s.replace("skill_", "") for s in skill_raw.split(";") if s]

                formatted_playlists.append({
                    "resource_id": pl.get("playlist_id"),
                    "title": pl.get("playlist_name"),
                    "url": pl.get("url"),
                    "language": pl.get("language", "Hindi"),
                    "video_count": pl.get("video_count", ""),
                    "skills": skill_list,
                    "verified": True,
                })

            result.append({
                "channel": data["channel"],
                "playlists": formatted_playlists,
            })

        return result


    async def search_projects(
        self,
        skill: str,
        role: Optional[str] = None,
        difficulty: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieves practical portfolio projects from fresher_ai_kb."""
        role_id = None
        if role:
            matched = kb_loader.match_role(role)
            if matched:
                role_id = matched.get("role_id")

        cache_key = f"rag:proj:{role or 'all'}:{skill}:{difficulty or 'all'}:{top_k}"
        query_text = f"Portfolio project implementing {skill}"

        hits = await self._search_with_cache(
            cache_key=cache_key,
            query_text=query_text,
            entity_type=["Projects", "projects"],
            role_id=role_id,
            difficulty=difficulty.lower() if difficulty else None,
            top_k=top_k,
        )

        projects = []
        for h in hits:
            p = h.get("payload", {})
            title = p.get("project_title") or p.get("title") or p.get("name")
            if title:
                projects.append({
                    "title": title,
                    "description": p.get("description", ""),
                    "architecture": p.get("architecture", ""),
                    "difficulty": p.get("difficulty", "intermediate"),
                    "skills": p.get("skill_ids", []),
                    "score": h.get("score", 0.0),
                })
        return projects

    async def search_weekly_roadmap(
        self,
        role: str,
        week: Optional[int] = None,
        top_k: int = 12,
    ) -> List[Dict[str, Any]]:
        """Retrieves weekly progressive roadmaps defined in fresher_ai_kb for target role."""
        matched = kb_loader.match_role(role)
        role_id = matched.get("role_id") if matched else "role_ai_engineer"

        cache_key = f"rag:roadmap:{role_id}:{week or 'all'}"
        query_text = f"Weekly roadmap breakdown for {role} week {week or 'progression'}"

        hits = await self._search_with_cache(
            cache_key=cache_key,
            query_text=query_text,
            entity_type=["Weekly_Roadmaps", "roadmaps"],
            role_id=role_id,
            top_k=top_k,
        )

        weeks = []
        for h in hits:
            p = h.get("payload", {})
            w_num = p.get("week_number")
            if week is None or w_num == week:
                weeks.append({
                    "week_number": w_num,
                    "phase_name": p.get("phase_name", "Core Phase"),
                    "weekly_goal": p.get("weekly_goal", ""),
                    "topics_covered": p.get("topics_covered", ""),
                    "deliverable": p.get("hands_on_deliverable", ""),
                    "practice_tasks": p.get("practice_tasks", ""),
                    "interview_topics": p.get("interview_topics", ""),
                    "difficulty": p.get("difficulty", "intermediate"),
                })

        weeks.sort(key=lambda x: x.get("week_number") or 0)
        return weeks

    async def search_tools(
        self,
        role: Optional[str] = None,
        top_k: int = 12,
    ) -> List[Dict[str, Any]]:
        """Retrieves essential tools and platforms for target role from fresher_ai_kb."""
        role_id = None
        if role:
            matched = kb_loader.match_role(role)
            if matched:
                role_id = matched.get("role_id")

        cache_key = f"rag:tools:{role or 'all'}:{top_k}"
        query_text = f"Essential tools platforms databases for {role or 'developer'}"

        hits = []
        try:
            hits = await self._search_with_cache(
                cache_key=cache_key,
                query_text=query_text,
                entity_type=["Tools_Platforms", "tools"],
                role_id=role_id,
                top_k=top_k,
            )
        except Exception as e:
            logger.debug(f"Tools Qdrant query notice: {e}")

        tools = []
        for h in hits:
            p = h.get("payload", {})
            name = p.get("tool_name") or p.get("name")
            url = p.get("official_url") or p.get("url") or p.get("website")
            if name:
                tools.append({
                    "name": name,
                    "url": url or f"https://www.{name.lower().replace(' ', '')}.com",
                    "category": p.get("category", "Developer Tool"),
                    "description": p.get("description", f"Essential tool for modern {role or 'software'} engineering."),
                    "tag": p.get("pricing_model") or "Essential",
                    "logo_key": p.get("logo_key") or kb_loader.extract_canonical_logo_key(name),
                })

        # Enrich from KB tools module if needed
        try:
            from data.tools_platforms import get_tools_platforms
            clean_r = (role or "").lower()
            for t in get_tools_platforms():
                t_roles = str(t.get("primary_role_ids", "")).lower()
                t_text = str(t.get("embedding_text", "")).lower()
                if t.get("is_universal") or (role_id and role_id.lower() in t_roles) or (clean_r and clean_r in t_text):
                    name = t.get("tool_name")
                    url = t.get("official_url") or t.get("url")
                    if name and url and not any(x["name"].lower() == name.lower() for x in tools):
                        tools.append({
                            "name": name,
                            "url": url,
                            "category": t.get("category", "Developer Tool"),
                            "description": t.get("purpose") or f"Essential tool for modern {role or 'software'} engineering.",
                            "tag": t.get("pricing_model") or "Essential",
                            "logo_key": kb_loader.extract_canonical_logo_key(name),
                        })
                        if len(tools) >= top_k:
                            break
        except Exception as e:
            logger.debug(f"Direct tools enrichment notice: {e}")

        return tools

    async def search_official_docs(
        self,
        role: Optional[str] = None,
        skill: Optional[str] = None,
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """Retrieves official documentation references for role and skills."""
        docs_list = []
        try:
            from data.resources import get_resources
            role_id = None
            if role:
                matched = kb_loader.match_role(role)
                if matched:
                    role_id = matched.get("role_id")

            clean_r = (role or "").lower()
            clean_s = (skill or "").lower()

            for r in get_resources():
                is_doc = r.get("resource_type") == "official_docs" or r.get("is_documentation") or "doc" in str(r.get("resource_purpose", "")).lower()
                if not is_doc:
                    continue

                r_roles = str(r.get("role_ids", "")).lower()
                r_skills = str(r.get("skill_ids", "")).lower()
                r_text = str(r.get("embedding_text", "")).lower()

                if (role_id and role_id.lower() in r_roles) or (clean_r and clean_r in r_text) or (clean_s and clean_s in r_skills) or r.get("is_core"):
                    t = r.get("title")
                    u = r.get("url")
                    if t and u and not any(x["url"] == u for x in docs_list):
                        docs_list.append({
                            "title": t,
                            "name": t,
                            "category": r.get("category", "Official Documentation"),
                            "url": u,
                            "source": r.get("source", "Official Docs"),
                            "difficulty": r.get("difficulty", "beginner"),
                            "logo_key": kb_loader.extract_canonical_logo_key(t),
                        })
                        if len(docs_list) >= top_k:
                            break
        except Exception as e:
            logger.debug(f"Direct official docs error: {e}")

        return docs_list

    async def search_career_resources(
        self,
        role: Optional[str] = None,
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        """Retrieves career and practice platforms from KB (LeetCode, Kaggle, Hugging Face, GitHub, LinkedIn, etc.)."""
        career_list = []
        try:
            from data.resources import get_resources
            for r in get_resources():
                if r.get("resource_type") in ("career_platform", "practice_platform") or r.get("is_career_resource") or r.get("is_practice_resource"):
                    t = r.get("title")
                    u = r.get("url")
                    if t and u and not any(x["url"] == u for x in career_list):
                        career_list.append({
                            "title": t,
                            "name": t,
                            "category": "Career & Practice",
                            "purpose": r.get("best_for") or r.get("description") or "Practice & Projects",
                            "url": u,
                            "logo_key": kb_loader.extract_canonical_logo_key(t),
                            "type": r.get("resource_type", "career_platform"),
                        })
                        if len(career_list) >= top_k:
                            break
        except Exception as e:
            logger.debug(f"Direct career resources error: {e}")

        return career_list

    async def search_interview_topics(
        self,
        role: str,
        skill: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieves verified interview topics and practice questions for role/skill."""
        cache_key = f"rag:interview:{role}:{skill or 'all'}:{top_k}"
        query_text = f"Interview questions and answers for {role} {skill or ''}"

        hits = await self._search_with_cache(
            cache_key=cache_key,
            query_text=query_text,
            entity_type=["Interview_Questions", "interview_prep"],
            top_k=top_k,
        )

        questions = []
        for h in hits:
            p = h.get("payload", {})
            q_text = p.get("question") or p.get("topic")
            if q_text:
                questions.append({
                    "question": q_text,
                    "answer_outline": p.get("answer_outline") or p.get("ideal_answer", ""),
                    "difficulty": p.get("difficulty", "medium"),
                    "importance": p.get("importance", "High"),
                })
        return questions


# Global singleton instance
retrieval_service = RetrievalService()
