from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GenerateRoadmapRequest(BaseModel):
    role: str = Field(..., description="Target Job Role, e.g. Frontend Developer, DevOps Engineer")
    targetPackage: str = Field(..., description="Target compensation/package, e.g. 15 LPA or $120k")
    useResume: bool = Field(False, description="Whether to tailor roadmap to uploaded resume")
    resume: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parsed candidate resume")


class RoadmapModule(BaseModel):
    title: str
    duration: str = "1 Week"
    difficulty: str = "Medium"
    description: str = ""
    youtube: str = ""
    article: str = ""


class RoadmapData(BaseModel):
    id: Optional[str] = None
    _id: Optional[str] = None
    userId: Optional[str] = None
    title: str
    targetPackage: str
    duration: str
    level: str = "Intermediate"
    modules: List[RoadmapModule] = Field(default_factory=list)
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None


class RoadmapResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
