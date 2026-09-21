import json
import logging
from collections import Counter
from typing import Any, Dict, List, Optional
from app.config import settings
from app.core.redis import get_cache, set_cache
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.kb_loader import kb_loader
from app.services.reranker_service import reranker_service

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
        import time
        from app.core.telemetry import telemetry

        # 1. Check Redis cache
        cached = await get_cache(cache_key)
        if cached:
            try:
                parsed = json.loads(cached)
                telemetry.log_retrieval_event(
                    operation="search_cached",
                    latency_ms=0.5,
                    top_k=top_k,
                    result_count=len(parsed),
                    cached=True,
                )
                return parsed
            except Exception:
                pass

        # 2. Compute query vector
        query_vec = await self._embedding.get_embedding(query_text)

        # 3. Query Qdrant (retrieve broader candidate pool for reranking if enabled)
        qdrant_start = time.perf_counter()
        candidate_count = max(top_k * 3, settings.RERANK_TOP_N) if settings.RERANKING_ENABLED else top_k
        raw_results = self._qdrant.search(
            query_vector=query_vec,
            top_k=candidate_count,
            entity_type=entity_type,
            role_id=role_id,
            skill_id=skill_id,
            difficulty=difficulty,
            score_threshold=score_threshold,
        )
        qdrant_latency = (time.perf_counter() - qdrant_start) * 1000.0
        telemetry.log_retrieval_event(
            operation="qdrant_vector_search",
            latency_ms=qdrant_latency,
            top_k=candidate_count,
            result_count=len(raw_results),
            cached=False,
        )

        # 4. Two-Stage Reranking
        if settings.RERANKING_ENABLED and raw_results:
            results = reranker_service.rerank(
                query=query_text,
                candidates=raw_results,
                top_k=top_k,
                operation="rag_retrieval_rerank",
            )
        else:
            results = raw_results[:top_k]

        # 5. Cache in Redis
        try:
            await set_cache(cache_key, json.dumps(results), ttl=settings.RAG_CACHE_TTL)
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
        Returns a list of curated YouTube CHANNELS tailored to the candidate's
        target role and skill gaps.

        Output schema per channel:
        {
            "channel_id":       str,   # stable registry ID
            "name":             str,   # display name
            "channel_url":      str,   # verified channel URL
            "avatar_initials":  str,   # fallback text avatar (2-3 chars)
            "avatar_color":     str,   # hex background colour for fallback
            "topics":           list[str],   # canonical topic tags
            "best_for":         str,   # one-sentence description
        }

        NOTE: Playlists, subscriber counts, and verification badges are
        intentionally excluded from this response.
        """
        try:
            from data.channel_registry import get_channel_registry
        except ImportError:
            from fresher_ai_kb.data.channel_registry import get_channel_registry

        role_lower = (role or "").lower()
        missing = [s.lower() for s in (missing_skills or [])]

        # ── 1. Role → priority channel IDs ──────────────────────────────────
        if any(k in role_lower for k in ["ai engineer", "genai", "machine learning", "ml", "data science", "llm"]):
            priority_ids = ["campusx", "krish_naik", "codebasics"]
        elif any(k in role_lower for k in ["devops", "cloud", "sre", "kubernetes", "infrastructure"]):
            priority_ids = ["abhishek_veeramalla", "techworld_nana", "kunal_kushwaha", "gate_smashers"]
        elif any(k in role_lower for k in ["system design", "architect"]):
            priority_ids = ["gaurav_sen", "take_u_forward", "kunal_kushwaha"]
        elif any(k in role_lower for k in ["dsa", "algorithm", "competitive", "placement"]):
            priority_ids = ["take_u_forward", "codehelp", "kunal_kushwaha", "apna_college", "codewithharry"]
        elif "backend" in role_lower:
            priority_ids = ["chai_aur_code", "codewithharry", "thapa_technical", "sheryians", "apna_college"]
        else:
            # Full stack / frontend default
            priority_ids = ["apna_college", "codewithharry", "chai_aur_code", "sheryians", "thapa_technical"]

        registry = get_channel_registry()

        # ── 2. Score every channel ───────────────────────────────────────────
        scored: List[tuple] = []
        for ch in registry:
            if not ch.get("verified", False):
                continue
            ch_id = ch["channel_id"]

            # Base priority from role mapping (higher = earlier in priority list)
            if ch_id in priority_ids:
                base = float((len(priority_ids) - priority_ids.index(ch_id)) * 20)
            else:
                base = 0.0

            # Skill-gap boost — lift channels whose topics cover what the candidate is missing
            ch_topic_str = " ".join(ch.get("topics", []) + ch.get("skills", [])).lower()
            for ms in missing:
                if ms.replace("_", " ") in ch_topic_str or ms.replace(" ", "_") in ch_topic_str:
                    base += 8.0

            scored.append((base, ch))

        # Sort by score descending; stable sort preserves registry ordering for ties
        scored.sort(key=lambda x: x[0], reverse=True)

        # ── 3. Format output (both flat fields for frontend and channel/playlists for test & deep consumers) ──
        try:
            from data.youtube_channels import get_playlists
        except ImportError:
            try:
                from fresher_ai_kb.data.youtube_channels import get_playlists
            except ImportError:
                get_playlists = lambda: []

        all_playlists = get_playlists()
        result: List[Dict[str, Any]] = []

        for _, ch in scored[:top_k_creators]:
            ch_id = ch["channel_id"]

            # Filter verified playlists for this channel
            ch_pls = [
                p for p in all_playlists
                if p.get("channel_id") == ch_id and p.get("verified") is True
            ]

            # Score playlists for missing skills if provided
            if missing:
                def _score_pl(pl):
                    text = f"{pl.get('skill_area', '')} {pl.get('playlist_name', '')} {' '.join(pl.get('tags', []))}".lower()
                    score = 0
                    for m in missing:
                        if m in text:
                            score += 10
                    # Prioritize advanced/RAG/LangGraph if requested
                    return (score, pl.get("priority", 0))
                ch_pls.sort(key=_score_pl, reverse=True)
            else:
                ch_pls.sort(key=lambda p: p.get("priority", 0), reverse=True)

            formatted_pls = []
            for p in ch_pls[:max_playlists_per_creator]:
                formatted_pls.append({
                    "playlist_id": p.get("playlist_id", ""),
                    "title": p.get("playlist_name", ""),
                    "url": p.get("url", ""),
                    "verified": p.get("verified", True),
                    "video_count": p.get("video_count", ""),
                    "skill_area": p.get("skill_area", ""),
                })

            result.append({
                # Flat properties consumed by new frontend components
                "channel_id":      ch_id,
                "name":            ch["name"],
                "channel_url":     ch["channel_url"],
                "avatar_initials": ch["avatar_initials"],
                "avatar_color":    ch["avatar_color"],
                "topics":          ch["topics"][:5],
                "best_for":        ch["best_for"],
                # Nested channel and playlists structure for backward compatibility & rich consumers
                "channel": {
                    "id":          ch_id,
                    "name":        ch["name"],
                    "url":         ch["channel_url"],
                    "tags":        ch.get("topics", []),
                    "best_for":    ch.get("best_for", ""),
                },
                "playlists": formatted_pls,
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
        skill_gaps: Optional[List[str]] = None,
        domain: Optional[str] = None,
        subcategory: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        resume_topics: Optional[List[str]] = None,
        excluded_question_ids: Optional[List[str]] = None,
        excluded_recent_concepts: Optional[List[str]] = None,
        top_k: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves grounded interview question candidates from Qdrant RAG pool
        with comprehensive multi-dimensional filtering, skill-gap boosting,
        deduplication, and resilient in-memory fallback to the 760-question bank.
        """
        excluded_ids = set(excluded_question_ids or [])
        recent_concepts = set(c.lower() for c in (excluded_recent_concepts or []))
        role_lower = (role or "").lower()
        gaps_lower = set(g.lower() for g in (skill_gaps or []))
        resume_lower = set(t.lower() for t in (resume_topics or []))
        target_diff = (difficulty or "").lower()

        # 1. Load canonical candidates from 760-question bank
        try:
            from data.interview_question_bank_v2 import get_interview_question_bank
        except ImportError:
            try:
                from fresher_ai_kb.data.interview_question_bank_v2 import get_interview_question_bank
            except ImportError:
                get_interview_question_bank = lambda: []

        all_bank_questions = get_interview_question_bank()

        # 2. Attempt Qdrant semantic search
        query_text = f"{domain or role} {subcategory or ''} {skill or ''} interview question {difficulty or ''}"
        cache_key = f"rag:interview_v2:{role}:{domain or 'all'}:{subcategory or 'all'}:{difficulty or 'all'}:{top_k}"

        qdrant_hits = []
        try:
            qdrant_hits = await self._search_with_cache(
                cache_key=cache_key,
                query_text=query_text,
                entity_type=["Interview_Questions", "interview_prep"],
                difficulty=difficulty,
                top_k=max(25, top_k * 2),
            )
        except Exception as e:
            logger.debug(f"Qdrant interview query notice (fallback available): {e}")

        # Map Qdrant hits to IDs
        qdrant_id_map = {}
        for h in qdrant_hits:
            p = h.get("payload", {})
            qid = p.get("question_id") or str(h.get("id"))
            if qid:
                qdrant_id_map[qid] = h.get("score", 0.7)

        # 3. Score candidates from the full bank
        scored_candidates = []
        for q in all_bank_questions:
            qid = q.get("question_id", "")
            if qid in excluded_ids:
                continue

            q_domain = q.get("domain", "")
            q_subcat = q.get("subcategory", "")
            q_diff = q.get("difficulty", "medium").lower()
            q_type = q.get("question_type", "conceptual").lower()
            q_roles = [r.lower() for r in q.get("roles", [])]
            q_concepts = [c.lower() for c in q.get("key_concepts", [])]

            # Base score: Qdrant semantic score if present, else 50.0
            score = qdrant_id_map.get(qid, 50.0)

            # Domain alignment boost
            if domain and q_domain.lower() == domain.lower():
                score += 25.0

            # Role alignment boost
            if any(r in role_lower or role_lower in r for r in q_roles):
                score += 20.0

            # Skill gap priority boost (lift questions testing what candidate is missing)
            gap_overlap = sum(1 for g in gaps_lower if any(g in c or c in g for c in q_concepts))
            if gap_overlap > 0:
                score += 15.0 * gap_overlap

            # Resume topic alignment boost
            resume_overlap = sum(1 for r in resume_lower if any(r in c or c in r for c in q_concepts))
            if resume_overlap > 0:
                score += 10.0 * resume_overlap

            # Difficulty alignment
            if target_diff:
                if q_diff == target_diff:
                    score += 10.0
                elif (target_diff == "hard" and q_diff == "medium") or (target_diff == "easy" and q_diff == "medium"):
                    score += 5.0

            # Question type alignment
            if question_type and q_type == question_type.lower():
                score += 8.0

            # Subcategory alignment
            if subcategory and q_subcat.lower() == subcategory.lower():
                score += 15.0

            # Penalty for recently tested concepts (avoid repetitive questions)
            concept_overlap = sum(1 for c in q_concepts if c in recent_concepts)
            if concept_overlap > 0:
                score -= 12.0 * concept_overlap

            scored_candidates.append((score, q))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # 4. Diversity selection: ensure varied subcategories
        selected: List[Dict[str, Any]] = []
        seen_subcats = Counter()

        for score, q in scored_candidates:
            sub = q.get("subcategory", "General")
            if seen_subcats[sub] >= 2 and len(selected) < top_k:
                continue

            seen_subcats[sub] += 1
            selected.append({
                "question_id": q.get("question_id"),
                "domain": q.get("domain"),
                "subcategory": q.get("subcategory"),
                "question_type": q.get("question_type"),
                "difficulty": q.get("difficulty"),
                "question": q.get("question"),
                "roles": q.get("roles", []),
                "key_concepts": q.get("key_concepts", []),
                "ideal_answer": q.get("ideal_answer", ""),
                "key_concepts_to_look_for": q.get("key_concepts_to_look_for", ""),
                "strong_answer_indicators": q.get("strong_answer_indicators", []),
                "partial_answer_indicators": q.get("partial_answer_indicators", []),
                "weak_answer_indicators": q.get("weak_answer_indicators", []),
                "common_mistakes": q.get("common_mistakes", []),
                "evaluation_rubric": q.get("evaluation_rubric", {}),
                "follow_up_topics": q.get("follow_up_topics", []),
                "related_question_ids": q.get("related_question_ids", []),
                "retrieval_score": round(score, 2),
            })

            if len(selected) >= top_k:
                break

        return selected


# Global singleton instance
retrieval_service = RetrievalService()
