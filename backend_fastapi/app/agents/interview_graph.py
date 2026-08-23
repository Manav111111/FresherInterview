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
    TechnicalRubric,
    HRRubric,
    QuestionReviewItem,
    TopicAccuracyItem,
    StandardizedInterviewReport,
)

logger = logging.getLogger("fresherai.interview_graph")


class InterviewState(TypedDict, total=False):
    action: str  # 'start', 'feedback', or 'summary'
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
# 1. QUESTION GENERATION PROMPTS
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
3. For resume-based questions, tag source as "resume" and reference the specific project/role.
4. Each question object must contain: "question", "difficulty" ("easy", "medium", or "hard"), "timer" (90-150), "topic", "source" ("standard" or "resume"), "resume_reference" (string or null).
5. Return ONLY valid JSON array.
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
You are an Elite Technical Domain Expert & Senior Principal Hiring Bar-Raiser with 15+ years of experience.
Generate 6 realistic, highly tailored technical interview questions specifically for: {role}
Resume Available: {"YES" if use_resume else "NO"}
{resume_context}

RULES:
1. Generate EXACTLY 6 questions covering:
   - Q1: Core fundamentals and tool ecosystem (easy)
   - Q2: Practical development workflow and API/module design (easy)
   - Q3: Debugging, profiling, and performance bottlenecks (medium)
   - Q4: Distributed architecture, data consistency, or scaling (hard)
   - Q5: Real-world production outage or refactoring case study (hard)
   - Q6: Security, automated testing, and CI/CD reliability (hard)
2. For resume-based questions, reference candidate's actual projects or tools.
3. Each question object must contain: "question", "difficulty" ("easy", "medium", or "hard"), "timer" (90-150), "topic", "source" ("standard" or "resume"), "resume_reference" (string or null).
4. Return ONLY valid JSON array.
"""


# ==========================================
# 2. STANDARDIZED PER-QUESTION EVALUATION PROMPTS
# ==========================================

def get_technical_feedback_prompt(question: str, answer: str, difficulty: str, topic: str = "Technical") -> str:
    return f"""
You are a Principal Engineering Bar-Raiser assessing a candidate's answer using a STANDARDIZED TECHNICAL RUBRIC.

Question: {question}
Topic: {topic}
Difficulty: {difficulty}
Candidate's Submitted Answer: {answer}

STANDARDIZED 100-POINT TECHNICAL RUBRIC:
1. "correctness" (0-40): Accuracy of technical claims, architecture, syntax, and logic. (Max 40)
2. "completeness" (0-20): Breadth of essential concepts, edge cases, and layers addressed. (Max 20)
3. "reasoning" (0-15): Problem-solving logic, architectural trade-offs, and scalability choices. (Max 15)
4. "communication" (0-15): Clarity, structured explanation, and professional terminology. (Max 15)
5. "relevance" (0-10): Directness, addressing the core question without irrelevant filler. (Max 10)

TOTAL OVERALL SCORE = correctness + completeness + reasoning + communication + relevance (0 to 100).

CLASSIFICATION CRITERIA ("result"):
- "correct": score >= 75 (Major concepts accurate, no major errors)
- "partially_correct": 50 <= score < 75 (Partial understanding, key details missing or incomplete)
- "incorrect": score < 50 (Factually wrong, critical misconceptions, or irrelevant)
- "insufficient": answer < 5 words, empty, or stating "I don't know"

RULES:
1. "strengths": 2-3 specific bullet points quoting or referencing what the candidate stated well.
2. "missing_points": 2-3 specific technical omissions or omitted best practices.
3. "incorrect_points": 0-2 factual errors or misconceptions in the candidate's answer.
4. "what_you_should_understand": If incorrect/partial, provide 1-2 clarifying sentences explaining the correct technical principle.
5. "ideal_answer_summary": Concise 3-4 sentence high-caliber model answer.
6. "approach_guidance": 3-4 step structured roadmap on how to answer this question.

Return ONLY valid JSON matching this schema:
{{
  "overall_score": 75,
  "result": "partially_correct",
  "technical_rubric": {{
    "correctness": 30,
    "completeness": 14,
    "reasoning": 12,
    "communication": 11,
    "relevance": 8
  }},
  "strengths": ["..."],
  "missing_points": ["..."],
  "incorrect_points": ["..."],
  "what_you_should_understand": "...",
  "ideal_answer_summary": "...",
  "approach_guidance": ["1. ...", "2. ...", "3. ..."],
  "feedback": "Concise 2-sentence summary."
}}
"""


def get_hr_feedback_prompt(question: str, answer: str, difficulty: str, topic: str = "HR & Behavioral") -> str:
    return f"""
You are a Senior Talent Partner evaluating a candidate's answer using a STANDARDIZED HR / BEHAVIORAL RUBRIC.

Question: {question}
Topic: {topic}
Difficulty: {difficulty}
Candidate's Submitted Answer: {answer}

STANDARDIZED 100-POINT HR RUBRIC:
1. "relevance" (0-25): How directly the response answers the specific behavioral prompt. (Max 25)
2. "communication" (0-25): Clarity, articulation, and professional tone. (Max 25)
3. "structure" (0-20): Structured framework (e.g., STAR: Situation, Task, Action, Result). (Max 20)
4. "examples" (0-15): Concrete real-world instances, metrics, or personal contributions. (Max 15)
5. "confidence" (0-15): Professionalism, self-awareness, and emotional intelligence. (Max 15)

TOTAL OVERALL SCORE = relevance + communication + structure + examples + confidence (0 to 100).

CLASSIFICATION CRITERIA ("result"):
- "correct": score >= 75 (Well-structured, convincing, strong examples)
- "partially_correct": 50 <= score < 75 (Good intent but lacks concrete results or structure)
- "incorrect": score < 50 (Unprofessional, unrelated, or counterproductive)
- "insufficient": answer < 5 words, empty, or "don't know"

Return ONLY valid JSON matching this schema:
{{
  "overall_score": 75,
  "result": "partially_correct",
  "hr_rubric": {{
    "relevance": 20,
    "communication": 20,
    "structure": 15,
    "examples": 10,
    "confidence": 10
  }},
  "strengths": ["..."],
  "missing_points": ["..."],
  "incorrect_points": ["..."],
  "what_you_should_understand": "...",
  "ideal_answer_summary": "...",
  "approach_guidance": ["1. Situation", "2. Task", "3. Action", "4. Result"],
  "feedback": "Concise 2-sentence summary."
}}
"""


# ==========================================
# 3. DETERMINISTIC SCORE AGGREGATOR ENGINE
# ==========================================

DIFFICULTY_WEIGHTS = {
    "easy": 0.8,
    "medium": 1.0,
    "hard": 1.2
}


def classify_score_result(score: int, answer: str) -> str:
    """Classifies answer outcome deterministically based on score and content length."""
    ans_clean = (answer or "").strip()
    words = ans_clean.split()
    if len(words) < 3 or any(phrase in ans_clean.lower() for phrase in ["don't know", "dont know", "no idea", "skip", "idk", "no answer"]):
        return "insufficient"
    if score >= 75:
        return "correct"
    if score >= 50:
        return "partially_correct"
    return "incorrect"



def get_readiness_classification(overall_score: int) -> tuple[str, str]:
    """Maps standardized score to verified hiring readiness tier."""
    if overall_score >= 90:
        return "Excellent / Interview Ready", "Demonstrated exceptional domain mastery, architectural depth, and crisp communication."
    if overall_score >= 75:
        return "Strong / Nearly Ready", "Solid conceptual and practical foundation. Ready for mid-level technical rounds with minor refinement."
    if overall_score >= 60:
        return "Developing / Needs Practice", "Demonstrated basic understanding of core concepts with important gaps in scaling, trade-offs, or depth."
    if overall_score >= 40:
        return "Significant Improvement Needed", "Partial conceptual awareness. Requires targeted revision on system mechanics and structured answering."
    return "Fundamentals Need Attention", "Foundational domain principles require dedicated study before attending technical interviews."


def calculate_deterministic_report(
    role: str,
    interview_type: str,
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    MATHEMATICAL DETERMINISTIC SCORE AGGREGATOR.
    Calculates final score, difficulty weights, category scores, topic accuracy,
    and review breakdowns directly from per-question evaluation data.
    """
    if not questions:
        readiness_lbl, readiness_desc = get_readiness_classification(75)
        return {
            "overallScore": 75,
            "readiness": readiness_lbl,
            "readinessDescription": readiness_desc,
            "questionsCount": 0,
            "correctCount": 0,
            "partialCount": 0,
            "incorrectCount": 0,
            "insufficientCount": 0,
            "averageScore": 75,
            "categoryScores": {},
            "topicAccuracy": [],
            "questionReviews": [],
            "topStrengths": [],
            "priorityImprovements": [],
        }

    is_technical = interview_type.lower() != "hr"
    
    total_weighted_score = 0.0
    total_weight = 0.0
    scores_list = []
    
    correct_count = 0
    partial_count = 0
    incorrect_count = 0
    insufficient_count = 0

    # Category accumulator dictionaries
    tech_categories = {"Technical Correctness": [], "Completeness": [], "Problem Solving": [], "Communication": [], "Relevance": []}
    hr_categories = {"Relevance to Question": [], "Communication & Clarity": [], "Answer Structure (STAR)": [], "Specific Examples": [], "Professional Confidence": []}

    topic_tracker: Dict[str, Dict[str, Any]] = {}
    question_reviews: List[Dict[str, Any]] = []
    all_strengths: List[str] = []
    all_missing: List[str] = []

    for idx, q in enumerate(questions):
        q_text = q.get("question", f"Question {idx+1}")
        u_ans = q.get("userAnswer", "")
        difficulty = (q.get("difficulty") or "medium").lower()
        diff_weight = DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
        topic = q.get("topic") or ("Technical" if is_technical else "Behavioral")
        
        fb = q.get("feedback") or {}
        raw_score = fb.get("score") if fb.get("score") is not None else q.get("score", 70)
        score = max(0, min(100, int(raw_score)))
        
        # Result classification
        result = fb.get("result")
        if not result or result not in ["correct", "partially_correct", "incorrect", "insufficient"]:
            result = classify_score_result(score, u_ans)

        if result == "correct":
            correct_count += 1
        elif result == "partially_correct":
            partial_count += 1
        elif result == "insufficient":
            insufficient_count += 1
        else:
            incorrect_count += 1

        total_weighted_score += score * diff_weight
        total_weight += diff_weight
        scores_list.append(score)

        # Collect category sub-scores
        if is_technical:
            rubric = fb.get("technical_rubric") or {}
            c_score = rubric.get("correctness") if rubric.get("correctness") is not None else fb.get("correctness", score * 0.4)
            comp_score = rubric.get("completeness") if rubric.get("completeness") is not None else fb.get("detail", score * 0.2)
            prob_score = rubric.get("reasoning") if rubric.get("reasoning") is not None else fb.get("problemSolving", score * 0.15)
            comm_score = rubric.get("communication") if rubric.get("communication") is not None else fb.get("communication", score * 0.15)
            rel_score = rubric.get("relevance") if rubric.get("relevance") is not None else fb.get("relevance", score * 0.10)

            # Normalize each subcategory to 0-100 percentage for reporting
            tech_categories["Technical Correctness"].append(min(100, round((c_score / 40.0) * 100 if c_score <= 40 else c_score)))
            tech_categories["Completeness"].append(min(100, round((comp_score / 20.0) * 100 if comp_score <= 20 else comp_score)))
            tech_categories["Problem Solving"].append(min(100, round((prob_score / 15.0) * 100 if prob_score <= 15 else prob_score)))
            tech_categories["Communication"].append(min(100, round((comm_score / 15.0) * 100 if comm_score <= 15 else comm_score)))
            tech_categories["Relevance"].append(min(100, round((rel_score / 10.0) * 100 if rel_score <= 10 else rel_score)))
        else:
            rubric = fb.get("hr_rubric") or {}
            rel_score = rubric.get("relevance") if rubric.get("relevance") is not None else fb.get("relevance", score * 0.25)
            comm_score = rubric.get("communication") if rubric.get("communication") is not None else fb.get("communication", score * 0.25)
            struct_score = rubric.get("structure") if rubric.get("structure") is not None else fb.get("clarity", score * 0.20)
            ex_score = rubric.get("examples") if rubric.get("examples") is not None else fb.get("detail", score * 0.15)
            conf_score = rubric.get("confidence") if rubric.get("confidence") is not None else fb.get("efficiency", score * 0.15)

            hr_categories["Relevance to Question"].append(min(100, round((rel_score / 25.0) * 100 if rel_score <= 25 else rel_score)))
            hr_categories["Communication & Clarity"].append(min(100, round((comm_score / 25.0) * 100 if comm_score <= 25 else comm_score)))
            hr_categories["Answer Structure (STAR)"].append(min(100, round((struct_score / 20.0) * 100 if struct_score <= 20 else struct_score)))
            hr_categories["Specific Examples"].append(min(100, round((ex_score / 15.0) * 100 if ex_score <= 15 else ex_score)))
            hr_categories["Professional Confidence"].append(min(100, round((conf_score / 15.0) * 100 if conf_score <= 15 else conf_score)))

        # Track topic accuracy
        if topic not in topic_tracker:
            topic_tracker[topic] = {"total_score": 0, "count": 0, "correct": 0}
        topic_tracker[topic]["total_score"] += score
        topic_tracker[topic]["count"] += 1
        if result == "correct":
            topic_tracker[topic]["correct"] += 1

        # Strengths & improvements
        q_strengths = fb.get("strengths") or fb.get("keyPointsCovered") or []
        q_missing = fb.get("missing_points") or fb.get("keyPointsMissed") or []
        all_strengths.extend(q_strengths)
        all_missing.extend(q_missing)

        # Question review entry
        question_reviews.append({
            "questionIndex": idx + 1,
            "question": q_text,
            "userAnswer": u_ans or "No answer submitted.",
            "difficulty": difficulty.capitalize(),
            "topic": topic,
            "score": score,
            "result": result,
            "strengths": q_strengths,
            "missingPoints": q_missing,
            "incorrectPoints": fb.get("incorrect_points", []),
            "whatYouShouldUnderstand": fb.get("what_you_should_understand"),
            "approachGuidance": fb.get("approach_guidance") or fb.get("improvements") or [],
            "idealAnswer": fb.get("ideal_answer_summary") or fb.get("idealAnswer") or "",
            "source": q.get("source", "standard"),
            "resumeReference": q.get("resume_reference"),
        })

    # Final overall score calculation with difficulty weights
    overall_score = round(total_weighted_score / total_weight) if total_weight > 0 else 75
    overall_score = max(0, min(100, overall_score))
    avg_score = round(sum(scores_list) / len(scores_list)) if scores_list else overall_score

    readiness_lbl, readiness_desc = get_readiness_classification(overall_score)

    # Category averages
    target_categories = tech_categories if is_technical else hr_categories
    aggregated_category_scores = {}
    for cat_name, val_list in target_categories.items():
        if val_list:
            aggregated_category_scores[cat_name] = round(sum(val_list) / len(val_list))
        else:
            aggregated_category_scores[cat_name] = overall_score

    # Topic accuracy list
    topic_accuracy_list = []
    for top_name, t_data in topic_tracker.items():
        top_avg = round(t_data["total_score"] / t_data["count"]) if t_data["count"] > 0 else overall_score
        topic_accuracy_list.append({
            "topic": top_name,
            "score": top_avg,
            "questionsCount": t_data["count"],
            "correctCount": t_data["correct"],
        })

    # Deduplicate top strengths & priority improvements
    top_strengths = list(dict.fromkeys(all_strengths))[:4]
    if not top_strengths:
        top_strengths = [
            f"Demonstrated foundational understanding of {role} concepts.",
            "Maintained active engagement and professional tone throughout the session.",
            "Attempted complex scenario questions with structured reasoning."
        ]

    priority_improvements = list(dict.fromkeys(all_missing))[:4]
    if not priority_improvements:
        priority_improvements = [
            "Incorporate concrete production metrics and quantifiable impact in technical explanations.",
            "Deepen coverage of edge-cases, system resilience, and architectural trade-offs.",
            "Structure situational responses consistently using the STAR methodology."
        ]

    return {
        "overallScore": overall_score,
        "readiness": readiness_lbl,
        "readinessDescription": readiness_desc,
        "questionsCount": len(questions),
        "correctCount": correct_count,
        "partialCount": partial_count,
        "incorrectCount": incorrect_count,
        "insufficientCount": insufficient_count,
        "averageScore": avg_score,
        "categoryScores": aggregated_category_scores,
        "topicAccuracy": topic_accuracy_list,
        "topStrengths": top_strengths,
        "priorityImprovements": priority_improvements,
        "questionReviews": question_reviews,
    }


# ==========================================
# 4. SUMMARY AI SYNTHESIS PROMPT
# ==========================================

def get_summary_prompt(
    role: str,
    interview_type: str,
    deterministic_data: Dict[str, Any]
) -> str:
    return f"""
You are an Executive Talent Director and Principal Bar-Raiser synthesizing a candidate's final interview report.

The candidate's scores have ALREADY been deterministically calculated using an evidence-based rubric:
- Overall Score: {deterministic_data.get('overallScore')}/100
- Hiring Readiness: {deterministic_data.get('readiness')}
- Questions Answered: {deterministic_data.get('questionsCount')} (Correct: {deterministic_data.get('correctCount')}, Partially Correct: {deterministic_data.get('partialCount')}, Incorrect: {deterministic_data.get('incorrectCount')})
- Average Score: {deterministic_data.get('averageScore')}/100
- Category Scores: {json.dumps(deterministic_data.get('categoryScores', {}))}
- Topic Accuracy: {json.dumps(deterministic_data.get('topicAccuracy', []))}

CRITICAL RULES:
1. DO NOT change or invent any scores. The overallScore must remain EXACTLY {deterministic_data.get('overallScore')}.
2. Write a comprehensive, personalized 100-140 word executive summary ("summary") synthesizing the candidate's performance, technical depth, and growth trajectory for the role: {role}.
3. Provide exactly 5 prioritized, high-impact action recommendations ("recommendations") for the candidate's career progression.
4. "hiringRecommendation": "{deterministic_data.get('readiness')}".

Return ONLY valid JSON matching this schema:
{{
  "summary": "Executive performance synthesis...",
  "recommendations": [
    "1. ...",
    "2. ...",
    "3. ...",
    "4. ...",
    "5. ..."
  ],
  "hiringRecommendation": "{deterministic_data.get('readiness')}"
}}
"""


# ==========================================
# 5. FALLBACK HEURISTICS
# ==========================================

def _fallback_questions(role: str, interview_type: str) -> List[Dict[str, Any]]:
    if interview_type.lower() == "hr":
        return [
            {"question": f"Can you introduce yourself and explain what motivates you to excel as a {role}?", "difficulty": "easy", "timer": 90, "topic": "Introductions", "source": "standard"},
            {"question": f"What are your greatest professional strengths, and how do they help you succeed as a {role}?", "difficulty": "easy", "timer": 90, "topic": "Strengths", "source": "standard"},
            {"question": "Describe a difficult challenge or roadblock you encountered on a project and how you resolved it.", "difficulty": "medium", "timer": 120, "topic": "Problem Solving", "source": "standard"},
            {"question": "How do you manage competing deadlines and prioritize tasks when working under high pressure?", "difficulty": "hard", "timer": 120, "topic": "Time Management", "source": "standard"},
            {"question": "Tell me about a time you had a disagreement with a team member or stakeholder and how you handled it constructively.", "difficulty": "hard", "timer": 150, "topic": "Conflict Resolution", "source": "standard"},
            {"question": "Where do you see your career advancing in the next 3 to 5 years, and how does this role fit your vision?", "difficulty": "hard", "timer": 120, "topic": "Career Vision", "source": "standard"},
        ]

    return [
        {"question": f"Explain the core architectural concepts and best practices required when building scalable systems as a {role}.", "difficulty": "easy", "timer": 90, "topic": "Core Fundamentals", "source": "standard"},
        {"question": f"What tools, libraries, and frameworks do you consider essential in your modern {role} development workflow?", "difficulty": "easy", "timer": 90, "topic": "Tooling & Ecosystem", "source": "standard"},
        {"question": "How do you approach debugging, performance optimization, and profiling when resolving complex production issues?", "difficulty": "medium", "timer": 120, "topic": "Debugging & Profiling", "source": "standard"},
        {"question": "How do you design systems with high availability, fault tolerance, and secure data handling?", "difficulty": "hard", "timer": 150, "topic": "System Design", "source": "standard"},
        {"question": "Describe a scenario where you had to refactor a legacy module or optimize an inefficient workflow under tight deadlines.", "difficulty": "hard", "timer": 150, "topic": "Refactoring", "source": "standard"},
        {"question": "How do you ensure thorough automated testing, CI/CD reliability, and production observability in your projects?", "difficulty": "hard", "timer": 150, "topic": "Reliability & Observability", "source": "standard"},
    ]


def _fallback_feedback(question: str, answer: str, is_technical: bool = True) -> Dict[str, Any]:
    ans_clean = (answer or "").strip()
    words = ans_clean.split()
    word_count = len(words)

    if word_count < 5 or any(phrase in ans_clean.lower() for phrase in ["don't know", "dont know", "no idea", "skip", "idk", "no answer"]):
        return {
            "score": 25,
            "result": "insufficient",
            "technical_rubric": {"correctness": 10, "completeness": 5, "reasoning": 4, "communication": 4, "relevance": 2},
            "hr_rubric": {"relevance": 6, "communication": 6, "structure": 5, "examples": 4, "confidence": 4},
            "strengths": [],
            "missing_points": ["Did not articulate core concepts or foundational mechanics.", "Omitted practical context and implementation examples."],
            "incorrect_points": [],
            "what_you_should_understand": "Attempt every question by breaking down definitions, core mechanics, and real-world examples.",
            "ideal_answer_summary": f"A strong answer for '{question}' defines the core concept, explains the underlying mechanism, and shares concrete trade-offs.",
            "approach_guidance": ["1. State the concise definition.", "2. Detail key architectural components.", "3. Give a practical production example."],
            "feedback": "The response was brief or incomplete. Review foundational principles to construct comprehensive answers.",
            "improvements": ["Structure your thoughts into clear components.", "Provide practical examples and trade-offs."]
        }

    tech_keywords = ["database", "cache", "redis", "scale", "api", "async", "index", "performance", "security", "token", "query", "service", "queue", "architecture"]
    matches = sum(1 for kw in tech_keywords if kw in ans_clean.lower())
    base_score = min(92, max(58, 62 + matches * 4 + min(12, word_count // 7)))

    result = classify_score_result(base_score, ans_clean)

    return {
        "score": base_score,
        "result": result,
        "technical_rubric": {
            "correctness": round(base_score * 0.40),
            "completeness": round(base_score * 0.20),
            "reasoning": round(base_score * 0.15),
            "communication": round(base_score * 0.15),
            "relevance": round(base_score * 0.10)
        },
        "hr_rubric": {
            "relevance": round(base_score * 0.25),
            "communication": round(base_score * 0.25),
            "structure": round(base_score * 0.20),
            "examples": round(base_score * 0.15),
            "confidence": round(base_score * 0.15)
        },
        "strengths": [
            "Addressed the primary premise of the question with clear intent.",
            "Demonstrated practical understanding of core domain principles."
        ],
        "missing_points": [
            "Could expand further on concrete performance benchmarks and edge-cases."
        ],
        "incorrect_points": [],
        "what_you_should_understand": "Connect foundational definitions directly with real-world scalability constraints.",
        "ideal_answer_summary": f"An exemplary response for '{question}' details architectural flow, explains security and fault-tolerance, and presents quantifiable metrics.",
        "approach_guidance": [
            "1. Define the primary concept clearly.",
            "2. Detail the internal mechanics.",
            "3. Discuss trade-offs and edge-case mitigations."
        ],
        "feedback": "Solid conceptual understanding. Expand on edge cases and concrete performance benchmarks for an exceptional answer.",
        "improvements": [
            "Discuss quantifiable impact and performance metrics.",
            "Mention failure recovery and resilience strategies."
        ]
    }


# ==========================================
# 6. ASYNC GRAPH NODES POWERED BY AI ROUTER
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
            normalized = []
            for q in questions[:6]:
                if isinstance(q, str):
                    normalized.append({
                        "question": q,
                        "difficulty": "medium",
                        "timer": 90,
                        "topic": "General",
                        "source": "standard",
                    })
                elif isinstance(q, dict):
                    normalized.append({
                        "question": q.get("question", "Explain your technical approach."),
                        "difficulty": q.get("difficulty", "medium"),
                        "timer": int(q.get("timer", 90)),
                        "topic": q.get("topic", "General"),
                        "source": q.get("source", "standard"),
                        "resume_reference": q.get("resume_reference"),
                    })
            if normalized:
                return {"questions": normalized}
    except Exception as e:
        logger.warning(f"AI question generation notice ({e}), applying resilient fallback.")

    return {"questions": _fallback_questions(role, itype)}


async def evaluate_answer_node(state: InterviewState) -> Dict[str, Any]:
    """Evaluates candidate answer using standardized rubric via AI Provider Router."""
    question = state.get("question", "")
    answer = state.get("answer", "")
    difficulty = state.get("difficulty", "medium")
    itype = state.get("type", "technical")
    is_technical = itype.lower() != "hr"

    prompt = get_technical_feedback_prompt(question, answer, difficulty) if is_technical else get_hr_feedback_prompt(question, answer, difficulty)

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FAST_EVALUATION,
            prompt=prompt,
            system_prompt="You are an expert hiring bar-raiser evaluating interview answers against a strict rubric.",
            json_mode=True,
            temperature=0.1,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            raw_score = parsed.get("overall_score", parsed.get("score", 75))
            score = max(0, min(100, int(raw_score)))

            result = parsed.get("result")
            if not result or result not in ["correct", "partially_correct", "incorrect", "insufficient"]:
                result = classify_score_result(score, answer)

            return {
                "feedback": {
                    "score": score,
                    "overall_score": score,
                    "result": result,
                    "technical_rubric": parsed.get("technical_rubric"),
                    "hr_rubric": parsed.get("hr_rubric"),
                    "strengths": parsed.get("strengths", []),
                    "missing_points": parsed.get("missing_points", parsed.get("keyPointsMissed", [])),
                    "incorrect_points": parsed.get("incorrect_points", []),
                    "what_you_should_understand": parsed.get("what_you_should_understand"),
                    "ideal_answer_summary": parsed.get("ideal_answer_summary", parsed.get("idealAnswer", "")),
                    "idealAnswer": parsed.get("ideal_answer_summary", parsed.get("idealAnswer", "")),
                    "approach_guidance": parsed.get("approach_guidance", parsed.get("improvements", [])),
                    "improvements": parsed.get("approach_guidance", parsed.get("improvements", [])),
                    "feedback": str(parsed.get("feedback", "Answer evaluated.")),
                    "keyPointsCovered": parsed.get("strengths", []),
                    "keyPointsMissed": parsed.get("missing_points", parsed.get("keyPointsMissed", [])),
                }
            }
    except Exception as e:
        logger.warning(f"AI answer evaluation notice ({e}), applying heuristic evaluation.")

    return {"feedback": _fallback_feedback(question, answer, is_technical)}


async def generate_summary_node(state: InterviewState) -> Dict[str, Any]:
    """
    Generates deterministic mathematical report and enriches with Gemini AI summary.
    The mathematical scores and categories are GROUND TRUTH and cannot be overridden by the LLM.
    """
    role = state.get("role", "Software Engineer")
    itype = state.get("type", "technical")
    questions = state.get("questions", [])

    # 1. Deterministic mathematical calculation
    det_report = calculate_deterministic_report(role, itype, questions)

    # 2. Feed deterministic data to LLM for personalized summary synthesis
    prompt = get_summary_prompt(role, itype, det_report)

    ai_summary = ""
    recommendations = []

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=TaskType.FINAL_REPORT,
            prompt=prompt,
            system_prompt="You are an executive talent director synthesizing a candidate evaluation report.",
            json_mode=True,
            temperature=0.2,
        ))

        if ai_res.success and ai_res.parsed_json and isinstance(ai_res.parsed_json, dict):
            parsed = ai_res.parsed_json
            ai_summary = parsed.get("summary", "")
            recommendations = parsed.get("recommendations", [])
    except Exception as e:
        logger.warning(f"AI summary report notice ({e}), using deterministic synthesis.")

    if not ai_summary:
        ai_summary = f"The candidate completed the {role} interview with a verified overall score of {det_report['overallScore']}/100 ({det_report['readiness']}). {det_report['readinessDescription']}"

    if not recommendations:
        recommendations = [
            f"Focus on deep dive drills in topics scoring below 70%: {', '.join([t['topic'] for t in det_report['topicAccuracy'] if t['score'] < 70]) or 'advanced scaling and design'}.",
            "Practice structuring situational technical answers with trade-offs and edge-case mitigations.",
            "Review caching strategies, indexing optimizations, and query profiling.",
            "Incorporate quantifiable business impact metrics into your project reviews.",
            "Re-attempt mock interviews to build consistent timed delivery confidence."
        ]

    # Combine deterministic math + AI synthesis
    final_report = {
        **det_report,
        "summary": ai_summary,
        "recommendations": recommendations,
        "hiringRecommendation": det_report["readiness"],
    }

    return {"report": final_report}


# ==========================================
# 7. GRAPH ASSEMBLY
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
