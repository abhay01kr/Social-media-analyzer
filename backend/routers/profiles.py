import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from models.profile_models import ProfileAnalyzeRequest, ProfileAnalyzeResponse
from services.profile_analyzer import profile_risk_analyzer
from database.db_unified import save_report

router = APIRouter(tags=["Member 2 - Profile Analyzer"])

@router.post("/analyze/profile", response_model=None)
@router.post("/api/analyze/profile", response_model=None)
@router.post("/api/profiles/analyze", response_model=None)
def analyze_profile(payload: ProfileAnalyzeRequest):
    """
    Member 2: Profile Analyzer Endpoint
    Analyzes:
    - Username Analysis
    - Bio Analysis
    - Followers/Following Ratio
    - Engagement Rate
    - Fake Profile Score
    - Trust Score
    """
    if not payload.username or not payload.username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or profile URL is required."
        )

    result = profile_risk_analyzer.analyze(
        platform=payload.platform,
        username_or_url=payload.username,
        bio=payload.bio,
        followers_count=payload.followers_count,
        following_count=payload.following_count,
        posts_count=payload.posts_count,
        avg_likes_per_post=payload.avg_likes_per_post,
        avg_comments_per_post=payload.avg_comments_per_post,
        has_avatar=payload.has_avatar,
        account_age_days=payload.account_age_days,
        is_verified=payload.is_verified
    )

    report_id = str(uuid.uuid4())
    result["report_id"] = report_id

    # Persist report in database (MongoDB or SQLite)
    target_label = f"@{result['username']} ({result['platform']})"
    save_report(
        report_id=report_id,
        report_type="profile",
        target=target_label,
        status="completed",
        score=result["trust_score"],
        verdict=result["verdict_badge"],
        summary=result["recommendation"],
        data=result
    )

    return result
