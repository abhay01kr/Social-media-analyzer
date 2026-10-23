from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ContentAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Post text, caption, or comment to analyze", example="Earn $5000 fast! Join my telegram t.me/crypto_scam right now!")
    author_username: Optional[str] = Field(None, description="Optional username of author")
    context: Optional[str] = Field(None, description="Context (e.g., comment, bio, direct_message, post_caption)")

class SpamDetectionResult(BaseModel):
    is_spam: bool
    spam_score: float
    confidence: str
    reasons: List[str]
    flagged_patterns: List[str]

class ToxicityResult(BaseModel):
    is_toxic: bool
    toxicity_score: float
    severity: str
    flagged_tokens: List[str]
    subcategories: Dict[str, float]

class HateSpeechResult(BaseModel):
    is_hate_speech: bool
    hate_speech_score: float
    severity: str
    targeted_categories: List[str]
    flagged_terms: List[str]

class NSFWResult(BaseModel):
    is_nsfw: bool
    nsfw_score: float
    severity: str
    content_types: List[str]
    flagged_terms: List[str]

class ContentAnalyzeResponse(BaseModel):
    report_id: str
    text_length: int
    analyzed_text_sample: str
    overall_safety_score: float
    threat_level: str
    verdict: str
    verdict_badge: str
    summary: str
    spam_detection: SpamDetectionResult
    toxic_comments: ToxicityResult
    hate_speech_detection: HateSpeechResult
    nsfw_detection: NSFWResult
    action_recommendation: str
