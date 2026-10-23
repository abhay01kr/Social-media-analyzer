from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class FinalReportRequest(BaseModel):
    title: str = Field(..., example="Comprehensive Audit for @target_user")
    target: str = Field(..., example="@target_user")
    profile_data: Optional[Dict[str, Any]] = None
    media_data: Optional[Dict[str, Any]] = None
    content_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    total_analyses: int
    profile_analyses: int
    media_analyses: int
    content_analyses: int
    average_trust_score: float
    high_risk_count: int
    moderate_risk_count: int
    trusted_count: int
    recent_activity: List[Dict[str, Any]]
    system_status: Dict[str, Any]

class HistoryFilterParams(BaseModel):
    type: Optional[str] = None
    verdict: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
