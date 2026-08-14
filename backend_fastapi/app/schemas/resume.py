from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ResumeData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missingSkills: List[str] = Field(default_factory=list)
    suggestedRole: str = ""
    score: int = 0
    recommendations: List[str] = Field(default_factory=list)
    userId: Optional[str] = None
    extractedText: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    success: bool = True
    message: str = "Resume analyzed successfully"
    data: Optional[Any] = None


class ResumeGetResponse(BaseModel):
    success: bool = True
    source: Optional[str] = "supabase"
    data: Optional[Any] = None
    message: Optional[str] = None
