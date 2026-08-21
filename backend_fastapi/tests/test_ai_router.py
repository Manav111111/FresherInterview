from app.ai.schemas import TaskType, AIRequest, AIProviderName, AnswerEvaluationSchema
from app.ai.provider_router import ai_router


def test_ai_router_provider_selection():
    """Verify AI provider routing selects Groq for fast tasks and Gemini for deep/multimodal tasks."""
    assert ai_router.select_primary_provider(TaskType.FAST_INTERVIEW_QUESTION) == AIProviderName.GROQ
    assert ai_router.select_primary_provider(TaskType.FAST_EVALUATION) == AIProviderName.GROQ
    assert ai_router.select_primary_provider(TaskType.FINAL_REPORT) == AIProviderName.GEMINI
    assert ai_router.select_primary_provider(TaskType.RESUME_ATS_ANALYSIS) == AIProviderName.GEMINI


def test_ai_router_schema_validation():
    """Verify AnswerEvaluationSchema strict bounds validation."""
    valid_eval = AnswerEvaluationSchema(
        overall_score=88,
        technical_score=90,
        communication_score=85,
        strengths=["Clear logic", "Great explanation of indexing"],
        improvements=["Mention connection pooling"],
        feedback="Well structured answer."
    )
    assert valid_eval.overall_score == 88
    assert valid_eval.technical_score == 90
    assert len(valid_eval.strengths) == 2
