from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ProfileAnalyzeRequest(BaseModel):
    platform: str = Field(..., description="Target platform (Instagram, Facebook, LinkedIn, X, TikTok, YouTube)")
    username: str = Field(..., description="Username or full profile URL")
    bio: Optional[str] = Field(None, description="Profile biography text")
    followers_count: Optional[int] = Field(None, ge=0, description="Followers count")
    following_count: Optional[int] = Field(None, ge=0, description="Following count")
    posts_count: Optional[int] = Field(None, ge=0, description="Total posts count")
    avg_likes_per_post: Optional[float] = Field(None, ge=0, description="Average likes per post for engagement calculation")
    avg_comments_per_post: Optional[float] = Field(None, ge=0, description="Average comments per post for engagement calculation")
    has_avatar: Optional[bool] = Field(None, description="Whether custom profile avatar is present")
    account_age_days: Optional[int] = Field(None, ge=0, description="Account age in days")
    is_verified: Optional[bool] = Field(None, description="Whether account is officially verified")

class UsernameAnalysisResult(BaseModel):
    clean_username: str
    length: int
    digit_count: int
    digit_ratio: float
    is_bot_pattern: bool
    risk_points: float
    findings: List[str]

class BioAnalysisResult(BaseModel):
    bio_text: Optional[str]
    length: int
    has_spam_keywords: bool
    has_suspicious_links: bool
    emoji_count: int
    sentiment: str
    risk_points: float
    findings: List[str]

class FollowerRatioResult(BaseModel):
    followers: Optional[int]
    following: Optional[int]
    ratio: Optional[float]
    ratio_status: str
    is_follow_farming: bool
    risk_points: float
    findings: List[str]

class EngagementRateResult(BaseModel):
    engagement_rate_percent: float
    benchmark_status: str
    estimated_activity_level: str
    risk_points: float
    findings: List[str]

class ProfileAnalyzeResponse(BaseModel):
    report_id: str
    platform: str
    username: str
    fake_profile_score: float
    trust_score: float
    verdict: str
    verdict_badge: str
    recommendation: str
    username_analysis: Dict[str, Any]
    bio_analysis: Dict[str, Any]
    followers_following_ratio: Dict[str, Any]
    engagement_rate: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    missing_data_notes: List[str]
    disclaimer: str
