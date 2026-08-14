import json
import re
import logging
from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from app.core.llm import get_llm
from app.config import settings

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


# ==========================================
# PROMPTS
# ==========================================

def get_hr_interview_prompt(role: str, use_resume: bool, resume: Dict[str, Any]) -> str:
    resume_context = ""
    if use_resume and resume:
        skills = ", ".join(resume.get("skills", []))
        projects = ", ".join(resume.get("projects", []))
        strengths = ", ".join(resume.get("strengths", []))
        weaknesses = ", ".join(resume.get("weaknesses", []))
        resume_context = f"""
Resume Summary: {resume.get('summary', '')}
Skills: {skills}
Projects: {projects}
Strengths: {strengths}
Weaknesses: {weaknesses}
"""
    return f"""
You are a Senior HR Interviewer with 15+ years of experience.
Generate realistic HR interview questions for the role: {role}
Resume Available: {"YES" if use_resume else "NO"}
{resume_context}

RULES:
1. Generate EXACTLY 6 questions.
2. Each question object must contain ONLY: "question", "difficulty" (easy/medium/hard), and "timer" (integer seconds 60-180).
3. Difficulty order: Q1->easy, Q2->easy, Q3->medium, Q4->hard, Q5->hard, Q6->hard.
4. Return ONLY valid JSON array. No markdown, no extra text.

Example format:
[
  {{"question": "Tell me about yourself and what interests you about this role.", "difficulty": "easy", "timer": 90}},
  {{"question": "Describe a challenging conflict you faced in a team and how you resolved it.", "difficulty": "medium", "timer": 120}}
]
"""


def get_technical_interview_prompt(role: str, use_resume: bool, resume: Dict[str, Any]) -> str:
    resume_context = ""
    if use_resume and resume:
        skills = ", ".join(resume.get("skills", []))
        projects = ", ".join(resume.get("projects", []))
        resume_context = f"""
Candidate Skills: {skills}
Candidate Projects: {projects}
"""
    return f"""
You are a Senior Technical Interviewer.
Generate realistic technical interview questions for the role: {role}
Resume Available: {"YES" if use_resume else "NO"}
{resume_context}

RULES:
1. Generate EXACTLY 6 technical questions testing fundamentals, system design, coding problem-solving, and architecture.
2. Each object must contain ONLY: "question", "difficulty" (easy/medium/hard), "timer" (integer seconds 60-180).
3. Difficulty order: Q1->easy, Q2->easy, Q3->medium, Q4->hard, Q5->hard, Q6->hard.
4. Return ONLY valid JSON array. No markdown, no extra text.

Example format:
[
  {{"question": "Explain the difference between synchronous and asynchronous execution.", "difficulty": "easy", "timer": 90}},
  {{"question": "How would you optimize database queries under heavy read loads?", "difficulty": "medium", "timer": 120}}
]
"""


def get_feedback_prompt(question: str, answer: str, difficulty: str) -> str:
    return f"""
You are a Senior Interviewer with 15+ years of experience.
Evaluate the candidate's answer naturally, honestly, and professionally like a real live interviewer.

Question: {question}
Candidate Answer: {answer}
Difficulty: {difficulty}

Evaluate criteria on a 0-100 scale:
- correctness, clarity, relevance, detail, efficiency, communication, problemSolving, creativity, score (overall)
- feedback (1-2 sentences maximum, natural human tone, no robotic language)
- improvements (exactly 3 short actionable bullet points, < 10 words each)

Return ONLY valid JSON.
Example format:
{{
  "score": 85,
  "correctness": 88,
  "clarity": 85,
  "relevance": 90,
  "detail": 80,
  "efficiency": 82,
  "communication": 86,
  "problemSolving": 84,
  "creativity": 78,
  "feedback": "Great explanation with clear fundamentals. Adding a concrete production example would make it stand out.",
  "improvements": [
    "Include real-world examples.",
    "Mention performance trade-offs.",
    "Be slightly more structured."
  ]
}}
"""


def get_summary_prompt(role: str, interview_type: str, questions: List[Dict[str, Any]]) -> str:
    return f"""
You are an expert technical interviewer and hiring manager.
Analyze the complete interview session and generate a final comprehensive report.

Role: {role}
Type: {interview_type}
Questions & Answers:
{json.dumps(questions, indent=2)}

RULES:
1. Overall score between 0-100.
2. Summary: 80-120 words summarizing performance, strengths, and areas for growth.
3. Strengths: 3-5 bullet points.
4. Weaknesses: 3-5 bullet points.
5. Recommendations: exactly 5 actionable improvement recommendations.
6. Return ONLY valid JSON. No markdown.

Example format:
{{
  "overallScore": 82,
  "summary": "The candidate demonstrated solid software engineering fundamentals with clear communication across questions. They showed strong technical clarity but need deeper preparation on distributed systems architecture.",
  "strengths": [
    "Clear conceptual articulation",
    "Strong understanding of core REST and database concepts",
    "Positive problem-solving attitude"
  ],
  "weaknesses": [
    "Lacked depth in distributed caching edge cases",
    "Could provide more quantified examples"
  ],
  "recommendations": [
    "Practice system design for large-scale architectures",
    "Deep-dive into caching strategies and invalidation",
    "Review concurrency and multithreading concepts",
    "Solve algorithmic problems under timed conditions",
    "Structure answers with the STAR method"
  ]
}}
"""


# ==========================================
# FALLBACK HEURISTICS (For Offline / Test Mode)
# ==========================================

def _fallback_questions(role: str, interview_type: str) -> List[Dict[str, Any]]:
    if interview_type.lower() == "hr":
        return [
            {"question": f"Can you introduce yourself and explain why you want to work as a {role}?", "difficulty": "easy", "timer": 90},
            {"question": "What are your greatest technical and professional strengths?", "difficulty": "easy", "timer": 90},
            {"question": "Describe a difficult challenge you encountered on a project and how you solved it.", "difficulty": "medium", "timer": 120},
            {"question": "How do you manage deadlines and prioritize tasks under high pressure?", "difficulty": "hard", "timer": 120},
            {"question": "Tell me about a time you had a disagreement with a team member and how you handled it.", "difficulty": "hard", "timer": 150},
            {"question": "Where do you see your career advancing in the next 3 to 5 years?", "difficulty": "hard", "timer": 120},
        ]
    else:
        return [
            {"question": f"Explain the core architectural concepts of building scalable applications as a {role}.", "difficulty": "easy", "timer": 90},
            {"question": "What is the difference between SQL and NoSQL databases, and when would you choose each?", "difficulty": "easy", "timer": 90},
            {"question": "How do you handle API authentication, rate limiting, and session security?", "difficulty": "medium", "timer": 120},
            {"question": "Explain how caching (e.g., Redis) improves system performance and how you handle cache invalidation.", "difficulty": "hard", "timer": 150},
            {"question": "How would you design a resilient microservice system with asynchronous background job processing?", "difficulty": "hard", "timer": 180},
            {"question": "Describe your strategy for debugging a production latency spike and identifying bottlenecks.", "difficulty": "hard", "timer": 150},
        ]


def _fallback_feedback(question: str, answer: str) -> Dict[str, Any]:
    length_bonus = min(20, len(answer.split()) // 3)
    base_score = min(92, max(60, 70 + length_bonus))
    return {
        "score": base_score,
        "correctness": min(95, base_score + 2),
        "clarity": min(95, base_score + 1),
        "relevance": min(95, base_score + 3),
        "detail": base_score - 2,
        "efficiency": base_score,
        "communication": min(95, base_score + 2),
        "problemSolving": base_score,
        "creativity": base_score - 4,
        "feedback": "Solid answer with good technical grounding. Adding specific real-world metrics would make it even more compelling.",
        "improvements": [
            "Provide concrete examples from past projects.",
            "Discuss potential trade-offs and edge cases.",
            "Maintain a structured, concise response flow."
        ]
    }


def _fallback_summary(role: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores = [q.get("feedback", {}).get("score", 75) for q in questions if q.get("feedback")]
    avg_score = int(sum(scores) / len(scores)) if scores else 80
    return {
        "overallScore": avg_score,
        "summary": f"The candidate demonstrated strong capability and domain understanding for the {role} position. Communication was clear throughout the interview turns with good conceptual grasp.",
        "strengths": [
            "Clear technical explanations and good communication",
            "Strong understanding of core fundamentals",
            "Logical step-by-step problem-solving method"
        ],
        "weaknesses": [
            "Could elaborate further on performance trade-offs",
            "Add more production-scale examples"
        ],
        "recommendations": [
            "Practice structuring answers using the STAR method",
            "Deep-dive into distributed systems concepts",
            "Review edge-case error handling and testing",
            "Participate in timed mock interview drills",
            "Highlight measurable impact and business value"
        ]
    }


# ==========================================
# AGENT NODES
# ==========================================

async def interview_node(state: InterviewState) -> Dict[str, Any]:
    """Node: Generates interview questions."""
    role = state.get("role", "Software Engineer")
    interview_type = state.get("type", "technical")
    use_resume = state.get("useResume", False)
    resume = state.get("resume", {})

    api_key = settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        return {"questions": _fallback_questions(role, interview_type)}

    try:
        llm = get_llm()
        prompt = (
            get_hr_interview_prompt(role, use_resume, resume)
            if interview_type.lower() == "hr"
            else get_technical_interview_prompt(role, use_resume, resume)
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = re.sub(r"^```(?:json)?\n?", "", response.content.strip(), flags=re.MULTILINE)
        content = re.sub(r"\n?```$", "", content, flags=re.MULTILINE).strip()
        questions = json.loads(content)
        return {"questions": questions}
    except Exception as e:
        logger.error(f"Error in interview_node: {e}")
        return {"questions": _fallback_questions(role, interview_type)}


async def feedback_node(state: InterviewState) -> Dict[str, Any]:
    """Node: Evaluates user's answer to the current question."""
    question = state.get("question", "")
    answer = state.get("answer", "")
    difficulty = state.get("difficulty", "medium")

    api_key = settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        return {"feedback": _fallback_feedback(question, answer)}

    try:
        llm = get_llm()
        prompt = get_feedback_prompt(question, answer, difficulty)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = re.sub(r"^```(?:json)?\n?", "", response.content.strip(), flags=re.MULTILINE)
        content = re.sub(r"\n?```$", "", content, flags=re.MULTILINE).strip()
        feedback = json.loads(content)
        return {"feedback": feedback}
    except Exception as e:
        logger.error(f"Error in feedback_node: {e}")
        return {"feedback": _fallback_feedback(question, answer)}


async def summary_node(state: InterviewState) -> Dict[str, Any]:
    """Node: Generates overall interview report."""
    role = state.get("role", "Software Engineer")
    interview_type = state.get("type", "technical")
    questions = state.get("questions", [])

    api_key = settings.GROQ_API_KEY
    if not api_key or "placeholder" in api_key:
        return {"report": _fallback_summary(role, questions)}

    try:
        llm = get_llm()
        prompt = get_summary_prompt(role, interview_type, questions)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = re.sub(r"^```(?:json)?\n?", "", response.content.strip(), flags=re.MULTILINE)
        content = re.sub(r"\n?```$", "", content, flags=re.MULTILINE).strip()
        report = json.loads(content)
        return {"report": report}
    except Exception as e:
        logger.error(f"Error in summary_node: {e}")
        return {"report": _fallback_summary(role, questions)}


# ==========================================
# ROUTER & GRAPH
# ==========================================

def start_router(state: InterviewState) -> str:
    action = state.get("action", "start")
    if action == "start":
        return "interviewAgent"
    elif action == "feedback":
        return "feedbackAgent"
    return END


def feedback_router(state: InterviewState) -> str:
    if state.get("completed", False):
        return "summaryAgent"
    return END


def create_interview_graph():
    builder = StateGraph(InterviewState)

    builder.add_node("interviewAgent", interview_node)
    builder.add_node("feedbackAgent", feedback_node)
    builder.add_node("summaryAgent", summary_node)

    builder.add_conditional_edges(
        START,
        start_router,
        {
            "interviewAgent": "interviewAgent",
            "feedbackAgent": "feedbackAgent",
        },
    )

    builder.add_edge("interviewAgent", END)

    builder.add_conditional_edges(
        "feedbackAgent",
        feedback_router,
        {
            "summaryAgent": "summaryAgent",
            END: END,
        },
    )

    builder.add_edge("summaryAgent", END)

    return builder.compile()


# Singleton compiled graph
interview_graph = create_interview_graph()
