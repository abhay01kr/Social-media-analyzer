import uuid
from fastapi import APIRouter, HTTPException, status
from models.content_models import ContentAnalyzeRequest, ContentAnalyzeResponse
from services.content_analyzer import content_safety_analyzer
from database.db_unified import save_report

router = APIRouter(tags=["Member 4 - Content Analyzer"])

@router.post("/analyze/content", response_model=None)
@router.post("/api/analyze/content", response_model=None)
@router.post("/api/content/analyze", response_model=None)
def analyze_content(payload: ContentAnalyzeRequest):
    """
    Member 4 - Content Analyzer Endpoint.
    Analyzes:
    - Spam Detection
    - Toxic Comments
    - Hate Speech Detection
    - NSFW Detection
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content text cannot be empty."
        )

    result = content_safety_analyzer.analyze(
        text=payload.text,
        author_username=payload.author_username,
        context=payload.context
    )

    report_id = str(uuid.uuid4())
    result["report_id"] = report_id

    # Persist report in database (MongoDB or SQLite)
    target_label = f"Text by @{payload.author_username}" if payload.author_username else f"Text: {result['analyzed_text_sample']}"
    save_report(
        report_id=report_id,
        report_type="content",
        target=target_label,
        status="completed",
        score=result["overall_safety_score"],
        verdict=result["verdict_badge"],
        summary=result["summary"],
        data=result
    )

    return result
