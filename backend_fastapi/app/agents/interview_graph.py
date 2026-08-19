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
You are an Elite Technical and HR Hiring Bar-Raiser Interviewer with 15+ years of experience.
Critically, accurately, and thoroughly evaluate the candidate's answer for the question below.

Question: {question}
Candidate Answer: {answer}
Difficulty: {difficulty}

EVALUATION CRITERIA:
1. "score" (0-100): Score based strictly on technical correctness, conceptual depth, completeness, and accuracy.
   - Blank, nonsensical, or "I don't know" answers: 0 to 25.
   - Vague or incomplete surface-level answers: 40 to 65.
   - Solid, mostly accurate answers: 70 to 82.
   - Comprehensive, senior-level, structured answers with nuance and edge cases: 85 to 98.
2. "correctness" (0-100): Accuracy of technical claims, logic, and factual statements.
3. "clarity" (0-100): How clearly, concisely, and effectively the candidate structured their thoughts.
4. "relevance" (0-100): How directly the answer addresses what was asked.
5. "detail" (0-100): Technical depth, specific terminology, and nuance.
6. "efficiency" (0-100): Directness, avoiding unnecessary fluff.
7. "communication" (0-100): Articulation, clarity, and professional tone.
8. "problemSolving" (0-100): Structured problem-solving mindset and trade-off considerations.
9. "creativity" (0-100): Insightful edge-cases, optimization insights, or alternative solutions.
10. "idealAnswer": Detailed, professional, comprehensive model answer (4-6 sentences or code snippet) demonstrating what an ideal candidate should answer.
11. "keyPointsCovered": Array of strings (2-4 bullet points) noting specific concepts or points the candidate successfully mentioned.
12. "keyPointsMissed": Array of strings (2-4 bullet points) noting crucial concepts, edge cases, or architecture details the candidate omitted.
13. "feedback": Direct, honest, and constructive critique (2-3 sentences).
14. "improvements": Exactly 3 actionable bullet points to improve the answer.

Return ONLY valid JSON (no markdown fences, no extra text).
Example format:
{{
  "score": 82,
  "correctness": 85,
  "clarity": 84,
  "relevance": 88,
  "detail": 80,
  "efficiency": 82,
  "communication": 85,
  "problemSolving": 83,
  "creativity": 78,
  "idealAnswer": "To optimize database queries under heavy read loads, we should first implement database indexing on frequently queried columns, set up read replicas to distribute query traffic, utilize caching layers like Redis with appropriate TTLs, and use database connection pooling alongside query profiling with EXPLAIN ANALYZE.",
  "keyPointsCovered": [
    "Mentioned database indexing on key lookup fields",
    "Suggested caching frequently accessed results"
  ],
  "keyPointsMissed": [
    "Did not mention read replica distribution or connection pooling",
    "Omitted database query profiling and execution plan analysis"
  ],
  "feedback": "Good fundamental understanding of caching and indexing. To demonstrate senior-level mastery, discuss read replication architecture, cache invalidation strategies, and connection pooling.",
  "improvements": [
    "Discuss read replica distribution for scaling high-throughput query loads.",
    "Explain cache invalidation mechanisms (e.g. Cache-Aside or Write-Through).",
    "Use EXPLAIN ANALYZE to identify slow table scans and optimize indexes."
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
1. Overall score between 0-100 based on the average quality and depth of answers.
2. Summary: 80-120 words summarizing performance, strengths, and areas for growth.
3. Strengths: 3-5 bullet points.
4. Weaknesses: 3-5 bullet points.
5. Recommendations: exactly 5 actionable improvement recommendations.
6. Return ONLY valid JSON. No markdown.

Example format:
{{
  "overallScore": 82,
  "summary": "The candidate demonstrated solid software engineering fundamentals with clear communication across questions. They showed strong technical clarity but need deeper preparation on distributed systems architecture and system resilience.",
  "strengths": [
    "Clear conceptual articulation and structured thinking",
    "Solid understanding of core REST APIs and database patterns",
    "Positive problem-solving approach"
  ],
  "weaknesses": [
    "Lacked depth in distributed caching and query optimization",
    "Could provide more quantified production metrics"
  ],
  "recommendations": [
    "Practice system design for large-scale distributed architectures",
    "Deep-dive into caching strategies and cache invalidation patterns",
    "Review concurrency, database isolation levels, and transactions",
    "Solve algorithmic problem-solving drills under timed constraints",
    "Structure behavioral answers using the STAR method"
  ]
}}
"""


# ==========================================
# FALLBACK HEURISTICS (For Offline / Test Mode)
# ==========================================

def _fallback_questions(role: str, interview_type: str) -> List[Dict[str, Any]]:
    if interview_type.lower() == "hr":
        return [
            {"question": f"Can you introduce yourself and explain what motivates you to excel as a {role}?", "difficulty": "easy", "timer": 90},
            {"question": "What are your greatest technical and professional strengths, and how have they helped you in past projects?", "difficulty": "easy", "timer": 90},
            {"question": "Describe a difficult challenge or bug you encountered on a project and how you systematically solved it.", "difficulty": "medium", "timer": 120},
            {"question": "How do you manage competing deadlines and prioritize tasks when working under high pressure?", "difficulty": "hard", "timer": 120},
            {"question": "Tell me about a time you had a technical disagreement with a team member and how you resolved it constructively.", "difficulty": "hard", "timer": 150},
            {"question": "Where do you see your career advancing in the next 3 to 5 years, and how does this role fit your vision?", "difficulty": "hard", "timer": 120},
        ]
    else:
        return [
            {"question": f"Explain the core architectural concepts of building scalable, fault-tolerant web applications as a {role}.", "difficulty": "easy", "timer": 90},
            {"question": "What is the difference between SQL and NoSQL databases, and what criteria do you use to choose between them?", "difficulty": "easy", "timer": 90},
            {"question": "How do you implement secure API authentication, session management, and rate limiting in production?", "difficulty": "medium", "timer": 120},
            {"question": "Explain how caching (e.g., Redis) improves system latency and what strategies you use for cache invalidation.", "difficulty": "hard", "timer": 150},
            {"question": "How would you design a resilient microservice system with asynchronous background job processing and message queues?", "difficulty": "hard", "timer": 180},
            {"question": "Describe your step-by-step strategy for debugging a production latency spike and identifying bottlenecks.", "difficulty": "hard", "timer": 150},
        ]


def _fallback_feedback(question: str, answer: str) -> Dict[str, Any]:
    ans_clean = (answer or "").strip()
    words = ans_clean.split()
    word_count = len(words)

    # Detect blank or non-answers
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
            "idealAnswer": f"An ideal answer for this question directly explains the key technical principles, architecture patterns, and practical trade-offs involved in '{question}'. It provides specific examples, explains 'why' a particular solution is chosen, and mentions performance/security implications.",
            "keyPointsCovered": [],
            "keyPointsMissed": [
                "Did not provide an explanation of core concepts",
                "Omitted technical details and architecture patterns",
                "Lacked concrete examples or trade-offs"
            ],
            "feedback": "The response was incomplete or did not address the core question. Make sure to attempt every question by structuring your thoughts and explaining fundamental concepts even if you are unsure of the advanced details.",
            "improvements": [
                "Break down the question into key components before answering.",
                "Explain the theoretical fundamentals if you don't know the exact syntax.",
                "Use the STAR method to structure your response."
            ]
        }

    # Evaluate answer content
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
        "idealAnswer": f"To master '{question}', an exceptional candidate outlines the high-level architecture, explains the core mechanism clearly, provides a concrete implementation example, and discusses trade-offs such as latency vs throughput, security constraints, and caching strategies.",
        "keyPointsCovered": [
            "Addressed the core premise of the question",
            "Demonstrated foundational understanding of the concept"
        ],
        "keyPointsMissed": [
            "Could expand on edge cases and failure handling",
            "Omitted performance benchmarking metrics"
        ],
        "feedback": "Solid answer with good technical grounding. Adding specific real-world metrics, architecture trade-offs, and failure recovery examples will make your response even stronger.",
        "improvements": [
            "Quantify your results with specific metrics (e.g. 'reduced latency by 35%').",
            "Discuss potential trade-offs and edge-case handling.",
            "Structure your technical answers with clear step-by-step logic."
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
