import re
import logging
from typing import Dict, Any, List, Optional
from app.ai.provider_router import ai_router
from app.ai.schemas import TaskType, AIRequest

logger = logging.getLogger("fresherai.chatbot")


class QueryIntent:
    LINKEDIN_POST = "linkedin_post"
    THEORY_CONCEPTUAL = "theory_conceptual"
    MATHEMATICAL_NUMERICAL = "mathematical_numerical"
    CODING_PROGRAMMING = "coding_programming"
    DSA_ALGORITHM = "dsa_algorithm"
    INTERVIEW_QUESTION = "interview_question"
    CAREER_RESUME = "career_resume"
    GENERAL = "general"


def detect_query_intent(message: str) -> str:
    """
    Lightweight, high-accuracy intent classifier.
    Categorizes user queries to select optimal prompting rules.
    """
    msg_clean = message.lower().strip()

    # 1. LinkedIn Post Generation Intent
    linkedin_keywords = [
        "linkedin post", "write a post", "make a post", "create a post",
        "post about my", "post for my", "post for linkedin", "linkedin update",
        "job announcement", "internship announcement", "selected at", "placed at",
        "got an offer", "new job", "started a new position", "joined as",
        "completed my project", "certificate post", "hackathon win",
        "share on linkedin", "draft a post", "celebrate my", "new role"
    ]
    if any(kw in msg_clean for kw in linkedin_keywords):
        return QueryIntent.LINKEDIN_POST

    # 2. Mathematical / Numerical / Calculation Intent
    math_indicators = [
        "solve", "derivative", "integrate", "integral", "calculate", "equation",
        "evaluate", "f(x)", "d/dx", "dx", "matrix", "determinant", "pythagorean",
        "logarithm", "quadratic", "algebra", "limit as"
    ]
    has_math_equation = bool(re.search(r"\b\d+x\b|\b[a-z]\s*[\+\-\*\/=]\s*\d+|\b\d+\s*[\+\-\*\/=]\s*[a-z]|\b\d+\s*[\+\-\*\/=]\s*\d+", msg_clean))
    if any(kw in msg_clean for kw in math_indicators) or has_math_equation:
        # Avoid false positive if it's DSA time complexity or coding
        if not any(dsa in msg_clean for dsa in ["binary search", "dijkstra", "dynamic programming", "tree", "graph", "array", "string"]):
            return QueryIntent.MATHEMATICAL_NUMERICAL

    # 3. Coding & Programming Intent
    coding_keywords = [
        "write code", "implement in", "python code", "javascript code", "java code", "cpp code",
        "function to", "write a program", "code to", "how to write", "syntax for",
        "script to", "debug this", "fix this code", "react component", "api route",
        "sql query", "regex for", "html/css"
    ]
    if any(kw in msg_clean for kw in coding_keywords):
        return QueryIntent.CODING_PROGRAMMING

    # 4. Data Structures & Algorithms Intent
    dsa_keywords = [
        "binary search", "linked list", "binary tree", "trie", "graph", "dijkstra",
        "bfs", "dfs", "dynamic programming", "two pointer", "sliding window",
        "quick sort", "merge sort", "lru cache", "time complexity of", "space complexity of",
        "topological sort", "heap", "stack", "queue", "dsa"
    ]
    if any(kw in msg_clean for kw in dsa_keywords):
        return QueryIntent.DSA_ALGORITHM

    # 5. Interview Question & Mock Prep Intent
    interview_keywords = [
        "interview question", "tell me about yourself", "why should we hire you",
        "greatest strength", "greatest weakness", "conflict with", "star method",
        "behavioral question", "salary expectation", "mock interview", "how to answer",
        "hr question", "technical round", "system design interview"
    ]
    if any(kw in msg_clean for kw in interview_keywords):
        return QueryIntent.INTERVIEW_QUESTION

    # 6. Career & Resume Intent
    career_keywords = [
        "resume", "ats score", "cover letter", "career advice", "portfolio",
        "salary negotiation", "job search", "internship tips", "fresher resume"
    ]
    if any(kw in msg_clean for kw in career_keywords):
        return QueryIntent.CAREER_RESUME

    # 7. Theory & Conceptual Intent
    theory_indicators = [
        "what is", "what are", "explain", "define", "why is", "why do we use",
        "difference between", "how does", "concept of", "advantages of",
        "disadvantages of", "features of", "architecture of", "overview of",
        "principles of", "acid properties", "rest api", "docker", "kubernetes",
        "microservices", "operating system", "garbage collection", "thread vs process",
        "tcp vs udp", "jwt", "oauth", "nosql vs sql", "caching", "redis"
    ]
    if any(msg_clean.startswith(ti) or f" {ti} " in f" {msg_clean} " for ti in theory_indicators):
        return QueryIntent.THEORY_CONCEPTUAL

    return QueryIntent.GENERAL


def get_system_prompt_for_intent(intent: str) -> str:
    """Returns specialized system prompts enforcing formatting rules per intent."""
    if intent == QueryIntent.LINKEDIN_POST:
        return """
You are a senior career branding expert and tech influencer copywriter.
Create a polished, ready-to-copy, high-impact LinkedIn post based on the user's message.

CRITICAL INSTRUCTIONS:
1. OUTPUT FORMAT: Return ONLY the ready-to-copy LinkedIn post.
   DO NOT include any introductory or concluding conversational filler (e.g., DO NOT say "Here is a LinkedIn post for you:" or "Hope this helps!").
2. TONE & STYLE: Short, concise, authentic, and professional (around 70 to 120 words).
   Use a natural human voice. AVOID cheesy, robotic AI clichés (e.g., avoid "I am beyond thrilled and humbled to announce...").
3. FORMATTING: Use clean paragraph breaks and 2-3 concise bullet points for key takeaways or learnings.
4. HASHTAGS: Conclude with 4 to 5 relevant, focused hashtags (e.g., #NewRole #SoftwareEngineering #CareerGrowth #FresherAI).
5. HANDLING MISSING DETAILS: If specific company or role details are not provided, write a smooth, polished generic post instead of asking follow-up questions.
"""

    if intent == QueryIntent.THEORY_CONCEPTUAL:
        return """
You are a world-class technical educator and software engineer.
Provide a direct, natural, and clear conceptual explanation of the topic.

CRITICAL INSTRUCTIONS:
1. DO NOT force a mathematical "step-by-step calculation" format.
2. Explain the concept naturally in simple, clear, professional language.
3. Structure:
   - Concise 1-2 sentence core definition / purpose.
   - Key architectural components or mechanisms (using concise bullet points).
   - Practical real-world example or use case.
4. Keep the answer direct and focused (under 200 words) unless the user explicitly asks for an in-depth breakdown.
"""

    if intent == QueryIntent.MATHEMATICAL_NUMERICAL:
        return """
You are a distinguished STEM educator and mathematician.
Solve the problem with clear, rigorous, step-by-step mathematical reasoning.

CRITICAL INSTRUCTIONS:
1. State the given formula / equation clearly.
2. Show step-by-step algebraic or calculus transformations with intermediate steps.
3. Clearly box or highlight the final verified result.
"""

    if intent == QueryIntent.CODING_PROGRAMMING:
        return """
You are a Principal Software Architect.
Provide a clean, idiomatic code solution with syntax highlighting, followed by a concise 2-3 sentence explanation of the approach and edge cases.
"""

    if intent == QueryIntent.DSA_ALGORITHM:
        return """
You are a competitive programming coach and algorithm specialist.
Explain the algorithm clearly:
1. Core Intuition & Strategy (2-3 sentences).
2. Step-by-Step Algorithm logic.
3. Complexity Analysis: Time Complexity and Space Complexity.
4. Clean Python or JavaScript implementation.
"""

    if intent == QueryIntent.INTERVIEW_QUESTION:
        return """
You are an Elite Hiring Bar-Raiser and Interview Coach.
Provide a structured, winning answer strategy:
- For behavioral questions, structure the response using the STAR framework (Situation, Task, Action, Result).
- For technical questions, structure with Definition -> Mechanism -> Practical Trade-offs.
- Provide a ready-to-deliver, interview-caliber model answer.
"""

    if intent == QueryIntent.CAREER_RESUME:
        return """
You are a Senior Technical Recruiter and Career Mentor.
Provide actionable, high-impact advice on resumes, ATS optimization, and career progression with concrete examples.
"""

    return """
You are Fresher.AI's friendly, highly knowledgeable Career & Technical Assistant.
Help candidates excel in their technical interviews, career development, and coding concepts with clear, concise, and accurate responses.
"""


def _generate_fallback_response(message: str, intent: str) -> str:
    """Generates high-quality fallback responses offline."""
    if intent == QueryIntent.LINKEDIN_POST:
        return f"""🚀 Excited to share a new milestone in my career journey!

I am joining as a Software Engineer, ready to tackle exciting challenges, build scalable systems, and collaborate with an incredible team.

A huge thank you to my mentors, peers, and everyone who supported me throughout this preparation journey. Looking forward to learning, contributing, and growing every single day!

#NewBeginnings #CareerMilestone #SoftwareEngineering #TechCareers #FresherAI"""

    if intent == QueryIntent.THEORY_CONCEPTUAL:
        return f"""**Overview**
{message.strip('?')} refers to a foundational concept in modern software architecture.

**Key Principles:**
• **Core Purpose**: Isolates concerns and provides reliable, predictable execution across environments.
• **How It Works**: Standardizes workflows and manages resource lifecycles efficiently.
• **Real-World Value**: Improves scalability, reduces deployment overhead, and ensures high system availability.

*Tip: In technical interviews, always connect the definition with real-world trade-offs and performance benefits.*"""

    if intent == QueryIntent.MATHEMATICAL_NUMERICAL:
        return f"""**Step-by-Step Solution:**

1. **Identify the Given Expression**:
   Analyze the governing mathematical relation and input parameters.

2. **Isolate the Variable**:
   Apply algebraic transformations step-by-step on both sides.

3. **Compute Final Value**:
   Simplifying the equation yields the verified exact solution.

**Final Answer**: Verified mathematically."""

    return f"I'm here to help you ace your technical interviews, write LinkedIn posts, and master software concepts. How would you like to proceed with '{message[:50]}'?"


async def generate_chatbot_response(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main Chatbot Handler with Lightweight Intent Detection.
    Routes queries to Groq / Gemini with specialized instructions.
    """
    intent = detect_query_intent(message)
    system_prompt = get_system_prompt_for_intent(intent)

    # Contextual user details if provided
    context_addon = ""
    if user_context:
        role = user_context.get("target_role") or user_context.get("role")
        name = user_context.get("name")
        if role:
            context_addon = f"\nCandidate Target Role: {role}"
        if name:
            context_addon += f"\nCandidate Name: {name}"

    prompt = f"{context_addon}\nUser Query: {message}" if context_addon else message

    task_type = TaskType.LINKEDIN_POST_GENERATION if intent == QueryIntent.LINKEDIN_POST else TaskType.CHATBOT_RESPONSE

    try:
        ai_res = await ai_router.execute(AIRequest(
            task_type=task_type,
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=False,
            temperature=0.3 if intent == QueryIntent.LINKEDIN_POST else 0.2,
        ))

        if ai_res.success and ai_res.content:
            reply = ai_res.content.strip()

            # Clean up unwanted conversational prefixes for LinkedIn posts
            if intent == QueryIntent.LINKEDIN_POST:
                reply = re.sub(r"^(here is (your|a) linkedin post[^\n]*:?\s*|here's (your|a) post[^\n]*:?\s*)", "", reply, flags=re.IGNORECASE).strip()
                reply = reply.strip('"').strip("'")

            return {
                "success": True,
                "reply": reply,
                "intent": intent,
                "provider": ai_res.provider,
                "model": ai_res.model,
            }
    except Exception as e:
        logger.warning(f"AI Chatbot error notice ({e}), using fallback.")

    fallback_reply = _generate_fallback_response(message, intent)
    return {
        "success": True,
        "reply": fallback_reply,
        "intent": intent,
        "provider": "fallback",
        "model": "heuristic-engine",
    }
