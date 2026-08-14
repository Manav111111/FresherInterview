from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    type: str = Field(..., description="Interview type: 'hr' or 'technical'")
    role: str = Field(..., description="Candidate target role")
    useResume: bool = Field(False, description="Whether to personalize questions with resume")
    resume: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parsed resume data")


class SubmitAnswerRequest(BaseModel):
    interviewId: str = Field(..., description="ID of the interview session")
    answer: str = Field(..., description="User's transcribed / typed answer")


class FeedbackData(BaseModel):
    score: int = 0
    correctness: int = 0
    clarity: int = 0
    relevance: int = 0
    detail: int = 0
    efficiency: int = 0
    communication: int = 0
    problemSolving: int = 0
    creativity: int = 0
    feedback: str = ""
    improvements: List[str] = Field(default_factory=list)


class QuestionData(BaseModel):
    question: str
    difficulty: str = "easy"
    timer: int = 60
    userAnswer: Optional[str] = ""
    feedback: Optional[FeedbackData] = None


class StartInterviewResponse(BaseModel):
    success: bool = True
    interviewId: str
    currentQuestion: int = 0
    totalQuestions: int = 6
    question: Optional[Dict[str, Any]] = None


class SubmitAnswerResponse(BaseModel):
    success: bool = True
    completed: bool = False
    currentQuestion: Optional[int] = None
    question: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    interview: Optional[Dict[str, Any]] = None
