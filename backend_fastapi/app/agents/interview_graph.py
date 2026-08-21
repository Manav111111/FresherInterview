import json
import re
import logging
from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from app.ai.provider_router import ai_router
from app.ai.schemas import (
    TaskType,
    AIRequest,
    AnswerEvaluationSchema,
    InterviewReportSchema,
)

logger = logging.getLogger("fresherai.interview_graph")


class InterviewState(TypedDict, total=False):
    action: str  # 'start' or 'feedback'
    role: str
    type: str  # 'hr' or 'technical'
    useResume: bool
    resume: Dict[str, Any]
    questions: List[Dict[str, Any]]
    question: str
    answer: str
    difficulty: str
    completed: bool
    feedback: Dict[str, Any]
    report: Dict[str, Any]
    skills_tested: List[str]
    skills_to_test: List[str]
    strengths_detected: List[str]
    weaknesses_detected: List[str]


# ==========================================
# PROMPTS
# ==========================================

def get_hr_interview_prompt(role: str, use_resume: bool, resume: Dict[str, Any]) -> str:
    resume_context = ""
    if use_resume and resume:
        skills = ", ".join(resume.get("skills", []) if isinstance(resume.get("skills"), list) else [str(resume.get("skills", ""))])
        raw_projects = resume.get("projects", [])
        project_names = [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in raw_projects] if isinstance(raw_projects, list) else [str(raw_projects)]
        projects = ", ".join(project_names)
        resume_context = f"""
Resume Summary: {resume.get('summary', '')}
Skills: {skills}
Projects: {projects}
"""
    return f"""
You are a Senior HR Interviewer & Talent Partner with 15+ years of experience.
Generate 6 realistic, adaptive HR / Behavioral interview questions for the role: {role}
Resume Available: {"YES" if use_resume else "NO"}
{resume_context}

RULES:
1. Generate EXACTLY 6 questions.
2. Structure progression:
   - Q1: Introductions, career motivation, and cultural fit (easy)
   - Q2: Team collaboration and communication (easy)
   - Q3: Conflict resolution and overcoming adversity (medium)
   - Q4: Ownership, project delivery under pressure, and STAR methodology (hard)
   - Q5: Strategic decision-making and cross-functional leadership (hard)
   - Q6: Career goals and long-term vision (hard)
3. Each question object must contain ONLY: "question", "difficulty" (easy/medium/hard), "timer" (integer seconds 60-180), and "topic".
4. Return ONLY valid JSON array.
"""


def get_technical_interview_prompt(role: str, use_resume: bool, resume: Dict[str, Any]) -> str:
    resume_context = ""
    if use_resume and resume:
        skills = ", ".join(resume.get("skills", []) if isinstance(resume.get("skills"), list) else [str(resume.get("skills", ""))])
        raw_projects = resume.get("projects", [])
        project_names = [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in raw_projects] if isinstance(raw_projects, list) else [str(raw_projects)]
        projects = ", ".join(project_names)
        resume_context = f"""
Candidate Verified Skills: {skills}
Candidate Projects: {projects}
"""

    return f"""
You are an Elite Domain Expert & Senior Principal Hiring Bar-Raiser with 15+ years of experience.
Generate 6 realistic, highly tailored technical interview questions specifically for: {role}
Resume Available: {"YES" if use_resume else "NO"}
{resume_context}

RULES:
1. Generate EXACTLY 6 questions covering:
   - Q1: Core fundamentals and tool ecosystem (easy)
   - Q2: Practical development workflow and API/module design (easy)
   - Q3: Debugging, profiling, and performance bottlenecks (medium)
   - Q4: Distributed architecture, data consistency, or high-throughput scaling (hard)
   - Q5: Real-world production outage / refactoring case study (hard)
   - Q6: Security, automated testing, and CI/CD reliability (hard)
2. Each object must contain: "question", "difficulty" (easy/medium/hard), "timer" (integer seconds 60-180), and "topic".
3. Return ONLY valid JSON array.
"""


def get_feedback_prompt(question: str, answer: str, difficulty: str) -> str:
    return f"""
You are an Elite Technical and HR Hiring Bar-Raiser Interviewer with 15+ years of experience.
Critically, accurately, and thoroughly evaluate the candidate's answer for the question below.

Question: {question}
Candidate Answer: {answer}
Difficulty: {difficulty}

EVALUATION CRITERIA:
1. "score" (0-100): Score based strictly on technical correctness, conceptual depth, completeness, and accuracy.
2. "correctness" (0-100): Accuracy of technical claims and logic.
3. "clarity" (0-100): How clearly and concisely the candidate structured their thoughts.
4. "relevance" (0-100): How directly the answer addresses what was asked.
5. "detail" (0-100): Technical depth and nuance.
6. "efficiency" (0-100): Directness, avoiding unnecessary fluff.
7. "communication" (0-100): Articulation and professional tone.
8. "problemSolving" (0-100): Structured problem-solving mindset and trade-offs.
9. "creativity" (0-100): Edge cases, optimizations, or alternative solutions.
10. "idealAnswer": Detailed, professional model answer (4-6 sentences).
11. "keyPointsCovered": Array of 2-4 bullet points noting points the candidate successfully mentioned.
12. "keyPointsMissed": Array of 2-4 bullet points noting crucial concepts omitted.
13. "feedback": Direct, constructive critique (2-3 sentences).
14. "improvements": Exactly 3 actionable bullet points to improve the answer.

Return ONLY valid JSON.
"""


def get_summary_prompt(role: str, interview_type: str, questions: List[Dict[str, Any]]) -> str:
    return f"""
You are a Principal Hiring Manager and Talent Evaluation Director.
Analyze the complete interview session and generate a comprehensive final performance report using deep reasoning.

Role: {role}
Type: {interview_type}
Interview Transcripts & Evaluations:
{json.dumps(questions, indent=2)}

RULES:
1. "overallScore" (0-100): Weighted average of candidate answers.
2. "technicalScore" (0-100): Technical accuracy and depth.
3. "communicationScore" (0-100): Clarity, conciseness, and structure.
4. "summary": 80-120 words summarizing performance, key strengths, and growth areas.
5. "strengths": 3-5 specific bullet points derived from actual answers.
6. "weaknesses": 3-5 specific areas needing improvement.
7. "recommendations": Exactly 5 actionable next steps for the candidate.
8. "hiringRecommendation": Strong Hire / Hire / Lean Hire / Do Not Hire.

Return ONLY valid JSON.
"""


# ==========================================
# FALLBACK HEURISTICS
# ==========================================

def _fallback_questions(role: str, interview_type: str) -> List[Dict[str, Any]]:
    role_lower = role.lower()
    if interview_type.lower() == "hr":
        return [
            {"question": f"Can you introduce yourself and explain what motivates you to excel as a {role}?", "difficulty": "easy", "timer": 90, "topic": "Introductions"},
            {"question": f"What are your greatest professional strengths, and how do they help you succeed as a {role}?", "difficulty": "easy", "timer": 90, "topic": "Strengths"},
            {"question": "Describe a difficult challenge or roadblock you encountered on a project and how you resolved it.", "difficulty": "medium", "timer": 120, "topic": "Problem Solving"},
            {"question": "How do you manage competing deadlines and prioritize tasks when working under high pressure?", "difficulty": "hard", "timer": 120, "topic": "Time Management"},
            {"question": "Tell me about a time you had a disagreement with a team member or stakeholder and how you handled it constructively.", "difficulty": "hard", "timer": 150, "topic": "Conflict Resolution"},
            {"question": "Where do you see your career advancing in the next 3 to 5 years, and how does this role fit your vision?", "difficulty": "hard", "timer": 120, "topic": "Career Vision"},
        ]

    return [
        {"question": f"Explain the core architectural concepts and best practices required when building scalable systems as a {role}.", "difficulty": "easy", "timer": 90, "topic": "Core Fundamentals"},
        {"question": f"What tools, libraries, and frameworks do you consider essential in your modern {role} development workflow?", "difficulty": "easy", "timer": 90, "topic": "Tooling & Ecosystem"},
        {"question": "How do you approach debugging, performance optimization, and profiling when resolving complex production issues?", "difficulty": "medium", "timer": 120, "topic": "Debugging & Profiling"},
        {"question": "How do you design systems with high availability, fault tolerance, and secure data handling?", "difficulty": "hard", "timer": 150, "topic": "System Design"},
        {"question": "Describe a scenario where you had to refactor a legacy module or optimize an inefficient workflow under tight deadlines.", "difficulty": "hard", "timer": 150, "topic": "Refactoring"},
        {"question": "How do you ensure thorough automated testing, CI/CD reliability, and production observability in your projects?", "difficulty": "hard", "timer": 150, "topic": "Reliability & Observability"},
    ]


def _fallback_feedback(question: str, answer: str) -> Dict[str, Any]:
    ans_clean = (answer or "").strip()
    words = ans_clean.split()
    word_count = len(words)

    if word_count < 5 or any(phrase in ans_clean.lower() for phrase in ["don't know", "dont know", "no idea", "skip", "idk", "no answer"]):
        return {
            "score": 25,
            "correctness": 20,
            "clarity": 30,
            "relevance": 25,
            "detail": 15,
            "efficiency": 40,
            "communication": 30,
            "problemSolving": 20,
            "creativity": 20,
            "idealAnswer": f"An ideal answer for '{question}' directly explains the fundamental concepts, practical patterns, and trade-offs involved.",
            "keyPointsCovered": [],
            "keyPointsMissed": [
                "Did not explain foundational concepts",
                "Omitted technical details and trade-offs"
            ],
            "feedback": "The response was brief or incomplete. Attempt every question by structuring your thoughts and explaining core principles.",
            "improvements": [
                "Break down the question into clear sub-topics before answering.",
                "Provide concrete examples or architectural trade-offs.",
                "Structure your response with clear bullet points or steps."
            ]
        }

    tech_keywords = ["database", "cache", "redis", "scale", "api", "async", "index", "performance", "security", "token", "query", "service", "queue", "architecture"]
    matches = sum(1 for kw in tech_keywords if kw in ans_clean.lower())
    base_score = min(92, max(55, 60 + matches * 5 + min(15, word_count // 6)))

    return {
        "score": base_score,
        "correctness": min(95, base_score + 3),
        "clarity": min(95, base_score + 1),
        "relevance": min(95, base_score + 4),
        "detail": min(95, base_score - 2),
        "efficiency": base_score,
        "communication": min(95, base_score + 2),
        "problemSolving": base_score,
        "creativity": min(95, base_score - 3),
        "idealAnswer": f"To master '{question}', an exceptional candidate outlines the architecture, explains the core mechanism, and discusses scalability and security trade-offs.",
        "keyPointsCovered": [
            "Addressed the core premise of the question",
            "Demonstrated practical understanding"
        ],
        "keyPointsMissed": [
            "Could elaborate further on edge cases and metrics"
        ],
        "feedback": "Solid conceptual understanding. To elevate your response, discuss real-world edge cases and concrete performance benchmarks.",
        "improvements": [
            "Mention production monitoring and performance metrics.",
            "Discuss scalability and resilience trade-offs.",
            "Structure behavioral responses using the STAR method."
        ]
    }


# ==========================================
# ASYNC GRAPH NODES POWERED BY AI ROUTER
# ==========================================

async def generate_questions_node(state: InterviewState) -> Dict[str, Any]:
    """Generates structured interview questions using AI Provider Router (Groq fast primary, Gemini fallback)."""
    role = state.get("role", "Software Engineer")
    itype = state.get("type", "technical")
    use_resume = state.get("useResume", False)
    resume = state.get("resume", {})

    prompt = get_hr_interview_prompt(role, use_resume, resume) if itype.lower() == "hr" else get_technical_interview_prompt(role, use_resume, resume)

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FAST_INTERVIEW_QUESTION,
            prompt=prompt,
            system_prompt="You are a principal technical recruiter and hiring bar-raiser.",
            json_mode=True,
            temperature=0.2,
        ))

        questions = None
        if ai_res.success and ai_res.parsed_json:
            if isinstance(ai_res.parsed_json, list):
                questions = ai_res.parsed_json
            elif isinstance(ai_res.parsed_json, dict):
                questions = ai_res.parsed_json.get("questions", None) or list(ai_res.parsed_json.values())[0]

        if not questions or not isinstance(questions, list) or len(questions) < 3:
            raw = ai_res.content
            match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", raw)
            if match:
                questions = json.loads(match.group(0))

        if questions and isinstance(questions, list):
            # Normalize schema
            normalized = []
            for q in questions[:6]:
                if isinstance(q, str):
                    normalized.append({
                        "question": q,
                        "difficulty": "medium",
                        "timer": 90,
                        "topic": "General",
                    })
                elif isinstance(q, dict):
                    normalized.append({
                        "question": q.get("question", "Explain your technical approach."),
                        "difficulty": q.get("difficulty", "medium"),
                        "timer": int(q.get("timer", 90)),
                        "topic": q.get("topic", "General"),
                    })
            if normalized:
                return {"questions": normalized}


    except Exception as e:
        logger.warning(f"AI question generation notice ({e}), applying resilient fallback.")

    return {"questions": _fallback_questions(role, itype)}


async def evaluate_answer_node(state: InterviewState) -> Dict[str, Any]:
    """Evaluates candidate answer using AI Provider Router (Groq fast primary, Gemini fallback)."""
    question = state.get("question", "")
    answer = state.get("answer", "")
    difficulty = state.get("difficulty", "medium")

    prompt = get_feedback_prompt(question, answer, difficulty)

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FAST_EVALUATION,
            prompt=prompt,
            system_prompt="You are an expert hiring bar-raiser evaluating interview answers.",
            json_mode=True,
            temperature=0.1,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            # Guarantee required fields
            return {
                "feedback": {
                    "score": int(parsed.get("score", 75)),
                    "correctness": int(parsed.get("correctness", 75)),
                    "clarity": int(parsed.get("clarity", 75)),
                    "relevance": int(parsed.get("relevance", 75)),
                    "detail": int(parsed.get("detail", 70)),
                    "efficiency": int(parsed.get("efficiency", 75)),
                    "communication": int(parsed.get("communication", 80)),
                    "problemSolving": int(parsed.get("problemSolving", 75)),
                    "creativity": int(parsed.get("creativity", 70)),
                    "idealAnswer": str(parsed.get("idealAnswer", "")),
                    "keyPointsCovered": parsed.get("keyPointsCovered", []),
                    "keyPointsMissed": parsed.get("keyPointsMissed", []),
                    "feedback": str(parsed.get("feedback", "Answer recorded.")),
                    "improvements": parsed.get("improvements", []),
                }
            }
    except Exception as e:
        logger.warning(f"AI answer evaluation notice ({e}), applying heuristic evaluation.")

    return {"feedback": _fallback_feedback(question, answer)}


async def generate_summary_node(state: InterviewState) -> Dict[str, Any]:
    """Generates comprehensive final report using Gemini deep reasoning with Groq fallback."""
    role = state.get("role", "Software Engineer")
    itype = state.get("type", "technical")
    questions = state.get("questions", [])

    prompt = get_summary_prompt(role, itype, questions)

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FINAL_REPORT,
            prompt=prompt,
            system_prompt="You are an executive talent director writing a comprehensive candidate evaluation report.",
            json_mode=True,
            temperature=0.2,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            return {"report": ai_res.parsed_json}
    except Exception as e:
        logger.warning(f"AI summary report notice ({e}), generating fallback summary.")

    # Fallback summary calculation
    scores = [q.get("score", 75) for q in questions if "score" in q]
    avg_score = round(sum(scores) / len(scores)) if scores else 75
    return {
        "report": {
            "overallScore": avg_score,
            "summary": f"The candidate completed the {role} interview with an overall score of {avg_score}%. They demonstrated good communication and foundational principles, with opportunities for deeper optimization.",
            "strengths": [
                "Good communication and structured thinking",
                "Demonstrated understanding of core domain principles",
                "Positive engagement with questions"
            ],
            "weaknesses": [
                "Could provide deeper quantifiable production metrics",
                "Opportunity to expand on edge case handling"
            ],
            "recommendations": [
                "Practice system design and architecture drills",
                "Review core performance profiling and caching patterns",
                "Structure situational answers using the STAR format",
                "Prepare quantifiable impact metrics for past projects",
                "Deep-dive into database scaling and query optimization"
            ],
            "hiringRecommendation": "Hire" if avg_score >= 75 else "Lean Hire"
        }
    }


# ==========================================
# GRAPH ASSEMBLY
# ==========================================

workflow = StateGraph(InterviewState)

workflow.add_node("generate_questions", generate_questions_node)
workflow.add_node("evaluate_answer", evaluate_answer_node)
workflow.add_node("generate_summary", generate_summary_node)

def route_action(state: InterviewState):
    action = state.get("action", "start")
    if action == "start":
        return "generate_questions"
    elif action == "feedback":
        return "evaluate_answer"
    elif action == "summary":
        return "generate_summary"
    return "generate_questions"

workflow.add_conditional_edges(
    START,
    route_action,
    {
        "generate_questions": "generate_questions",
        "evaluate_answer": "evaluate_answer",
        "generate_summary": "generate_summary",
    }
)

workflow.add_edge("generate_questions", END)
workflow.add_edge("evaluate_answer", END)
workflow.add_edge("generate_summary", END)

interview_graph = workflow.compile()
