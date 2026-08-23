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

class TechnicalRubric(BaseModel):
    correctness: int = Field(ge=0, le=40, default=30, description="Technical Correctness (max 40)")
    completeness: int = Field(ge=0, le=20, default=15, description="Completeness of concepts (max 20)")
    reasoning: int = Field(ge=0, le=15, default=12, description="Problem-Solving & Reasoning (max 15)")
    communication: int = Field(ge=0, le=15, default=12, description="Communication & Clarity (max 15)")
    relevance: int = Field(ge=0, le=10, default=8, description="Relevance & Conciseness (max 10)")


class HRRubric(BaseModel):
    relevance: int = Field(ge=0, le=25, default=20, description="Relevance to question (max 25)")
    communication: int = Field(ge=0, le=25, default=20, description="Communication & Clarity (max 25)")
    structure: int = Field(ge=0, le=20, default=15, description="Structure & STAR methodology (max 20)")
    examples: int = Field(ge=0, le=15, default=12, description="Specific real-world examples (max 15)")
    confidence: int = Field(ge=0, le=15, default=12, description="Confidence & Professionalism (max 15)")


class AnswerEvaluationSchema(BaseModel):
    overall_score: int = Field(ge=0, le=100, default=75)
    technical_score: Optional[int] = Field(default=None, ge=0, le=100)
    communication_score: Optional[int] = Field(default=None, ge=0, le=100)
    problem_solving_score: Optional[int] = Field(default=None, ge=0, le=100)
    relevance_score: Optional[int] = Field(default=None, ge=0, le=100)
    result: str = Field(default="partially_correct", description="correct, partially_correct, incorrect, or insufficient")
    technical_rubric: Optional[TechnicalRubric] = None
    hr_rubric: Optional[HRRubric] = None
    strengths: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    incorrect_points: List[str] = Field(default_factory=list)
    what_you_should_understand: Optional[str] = None
    ideal_answer_summary: str = ""
    approach_guidance: List[str] = Field(default_factory=list)
    feedback: str = ""
    improvements: List[str] = Field(default_factory=list)



class InterviewQuestionSchema(BaseModel):
    question: str
    type: str = "technical"
    difficulty: str = "medium"
    topic: str = "Core Concepts"
    skills_tested: List[str] = Field(default_factory=list)
    expected_key_points: List[str] = Field(default_factory=list)
    timer_seconds: int = 90
    source: str = "standard"  # 'standard' or 'resume'
    resume_section: Optional[str] = None
    resume_reference: Optional[str] = None


class QuestionReviewItem(BaseModel):
    question_index: int = 1
    question: str
    user_answer: str = ""
    difficulty: str = "medium"
    topic: str = "General"
    score: int = Field(ge=0, le=100, default=75)
    result: str = "partially_correct"  # 'correct', 'partially_correct', 'incorrect', 'insufficient'
    category_scores: Dict[str, int] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    incorrect_points: List[str] = Field(default_factory=list)
    what_you_should_understand: Optional[str] = None
    approach_guidance: List[str] = Field(default_factory=list)
    ideal_answer: str = ""
    source: str = "standard"
    resume_reference: Optional[str] = None


class TopicAccuracyItem(BaseModel):
    topic: str
    score: int = Field(ge=0, le=100)
    questions_count: int = 1
    correct_count: int = 0


class StandardizedInterviewReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    readiness_label: str
    readiness_description: str
    questions_count: int
    correct_count: int
    partial_count: int
    incorrect_count: int
    insufficient_count: int
    average_score: int
    category_scores: Dict[str, int]
    topic_accuracy: List[TopicAccuracyItem]
    top_strengths: List[str]
    priority_improvements: List[str]
    recommendations: List[str]
    summary: str
    question_reviews: List[QuestionReviewItem]


# Backwards compatibility alias
InterviewReportSchema = StandardizedInterviewReport




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
