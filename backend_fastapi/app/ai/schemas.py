from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    FAST_INTERVIEW_QUESTION = "fast_interview_question"
    REAL_TIME_FOLLOWUP = "real_time_followup"
    FAST_EVALUATION = "fast_evaluation"
    DEEP_EVALUATION = "deep_evaluation"
    FINAL_REPORT = "final_report"
    RESUME_ATS_ANALYSIS = "resume_ats_analysis"
    ROADMAP_GENERATION = "roadmap_generation"
    VIDEO_STORYBOARD = "video_storyboard"
    GENERAL = "general"


class AIProviderName(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    FALLBACK = "fallback"


class AIRequest(BaseModel):
    task_type: TaskType = TaskType.GENERAL
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.2
    json_mode: bool = True
    images: Optional[List[Dict[str, Any]]] = None  # Multimodal support
    preferred_provider: Optional[AIProviderName] = None
    timeout_seconds: float = 35.0


class AIResponse(BaseModel):
    success: bool = True
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    provider: str
    model: str
    latency_ms: float
    fallback_used: bool = False
    error: Optional[str] = None


# ─── Strict Structured Pydantic Schemas for Outputs ───

class AnswerEvaluationSchema(BaseModel):
    overall_score: int = Field(ge=0, le=100, default=75)
    technical_score: int = Field(ge=0, le=100, default=75)
    communication_score: int = Field(ge=0, le=100, default=80)
    problem_solving_score: int = Field(ge=0, le=100, default=70)
    relevance_score: int = Field(ge=0, le=100, default=80)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    feedback: str = ""
    better_answer: Optional[str] = ""
    follow_up_required: bool = False
    suggested_follow_up: Optional[str] = None


class InterviewQuestionSchema(BaseModel):
    question: str
    type: str = "technical"
    difficulty: str = "medium"
    topic: str = "Core Concepts"
    skills_tested: List[str] = Field(default_factory=list)
    expected_key_points: List[str] = Field(default_factory=list)
    timer_seconds: int = 90


class QuestionReviewItem(BaseModel):
    question: str
    user_answer: str
    score: int
    feedback: str
    better_approach: str


class InterviewReportSchema(BaseModel):
    overall_score: int = Field(ge=0, le=100, default=75)
    technical_score: int = Field(ge=0, le=100, default=75)
    communication_score: int = Field(ge=0, le=100, default=80)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    summary: str = ""
    hiring_recommendation: str = "Hire"
    question_by_question: List[QuestionReviewItem] = Field(default_factory=list)
    actionable_next_steps: List[str] = Field(default_factory=list)


class ATSSectionAudit(BaseModel):
    present: bool = True
    feedback: str = "Well formatted"


class ResumeATSAnalysisSchema(BaseModel):
    score: int = Field(ge=0, le=100, default=75)
    level: str = "Intermediate"
    summary: str = ""
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    bullet_improvements: List[Dict[str, str]] = Field(default_factory=list)
    ats_formatting_score: int = Field(ge=0, le=100, default=85)
    sections_detected: Dict[str, bool] = Field(default_factory=dict)
    key_strengths: List[str] = Field(default_factory=list)
    critical_fixes: List[str] = Field(default_factory=list)
