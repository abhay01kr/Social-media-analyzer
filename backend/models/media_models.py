from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class FaceDetectionBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float] = None

class FaceDetectionResult(BaseModel):
    faces_detected_count: int
    has_faces: bool
    bounding_boxes: List[FaceDetectionBox]
    face_details: List[Dict[str, Any]] = []

class ImageAnalyzeResponse(BaseModel):
    report_id: str
    filename: str
    media_type: str = "image"
    width: int
    height: int
    face_detection: FaceDetectionResult
    ai_generated_detection: Dict[str, Any]
    deepfake_detection: Dict[str, Any]
    authenticity_score: float
    ai_likelihood_score: float
    verdict: str
    risk_badge: str
    summary: str
    forensic_signals: Dict[str, Any]
    limitations: List[str]

class VideoAnalyzeResponse(BaseModel):
    report_id: str
    filename: str
    media_type: str = "video"
    metadata: Dict[str, Any]
    face_detection: FaceDetectionResult
    ai_analysis: Dict[str, Any]
    deepfake_analysis: Dict[str, Any]
    duplicate_analysis: Dict[str, Any]
    authenticity_score: float
    deepfake_probability: float
    verdict: str
    summary: str
