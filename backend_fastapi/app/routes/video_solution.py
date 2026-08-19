import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status
from app.agents.video_solution_agent import generate_video_solution

logger = logging.getLogger("fresherai.video_solution")

video_solution_router = APIRouter(tags=["Video Solution"])


class GenerateSolutionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Question or problem statement to solve")


@video_solution_router.post("/generate-solution")
async def create_video_solution(body: GenerateSolutionRequest):
    """
    Generates a structured educational solution timeline with step-by-step
    whiteboard scenes and voice narration for a given question.
    """
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        solution_data = await generate_video_solution(question)
        return {
            "success": True,
            "data": solution_data,
        }
    except ValueError as val_err:
        logger.warning(f"Validation error generating video solution: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as e:
        logger.error(f"Error generating video solution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate video solution. Please try again.",
        )
