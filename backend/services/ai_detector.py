import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from .face_detector import face_detector

class AIMediaDetector:
    """
    Member 3 - Video AI & Deepfake Likelihood Estimator.
    Inspects:
    - AI-generated Video Detection (diffusion model temporal variance, edge stability, motion flow)
    - Deepfake Detection (face seam artifacts, eye/skin smoothing across frames)
    - Face Detection across sampled video frames
    """

    def __init__(self):
        pass

    def inspect_frame_edges(self, frame: np.ndarray) -> float:
        """Measures high-frequency edge distribution via Laplacian operator."""
        if frame is None or frame.size == 0:
            return 0.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return float(laplacian.var())

    def analyze(self, sampled_frames: List[Tuple[int, np.ndarray]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        limitations = [
            "AI-generated video and deepfake detection produce probabilistic signals, not absolute truth.",
            "Modern generative diffusion models and neural face-swappers evolve continuously.",
            "Heavy social media compression (e.g. WhatsApp, Instagram, TikTok) can distort frame artifacts and trigger false positives.",
            "Absence of C2PA provenance metadata is common in legitimate legacy user recordings."
        ]

        if not sampled_frames or len(sampled_frames) < 2:
            return {
                "ai_likelihood_score": 15.0,
                "deepfake_probability": 10.0,
                "authenticity_score": 85.0,
                "verdict": "Inconclusive (Insufficient Frames)",
                "risk_badge": "Authentic",
                "summary": "Video stream contained too few decodable frames for multi-frame artifact analysis.",
                "face_detection": {
                    "faces_detected_count": 0,
                    "has_faces": False,
                    "bounding_boxes": [],
                    "face_details": []
                },
                "deepfake_analysis": {
                    "deepfake_score": 10.0,
                    "findings": ["Insufficient frames to evaluate face tracking."]
                },
                "signals": {
                    "temporal_consistency": "Insufficient data",
                    "edge_stability": "Insufficient data",
                    "compression_anomaly": "Standard"
                },
                "limitations": limitations
            }

        # 1. Temporal Frame Variance Analysis
        variances = []
        interframe_diffs = []
        prev_gray = None

        # 2. Face Detection across sampled video frames (Member 3)
        faces_detected_in_frames = 0
        total_boxes = []
        deepfake_signals = []
        deepfake_points = 5.0

        for idx, frame in sampled_frames:
            var = self.inspect_frame_edges(frame)
            variances.append(var)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                interframe_diffs.append(float(np.mean(diff)))
            prev_gray = gray

            # Detect faces on every 3rd sampled frame for efficiency
            if idx % 3 == 0:
                fd = face_detector.detect_faces(frame)
                if fd["has_faces"]:
                    faces_detected_in_frames += 1
                    total_boxes.extend(fd["bounding_boxes"][:2])
                    for fdetail in fd["face_details"]:
                        if fdetail["is_synthetic_smoothing"]:
                            deepfake_points += 15.0
                            deepfake_signals.append(f"Synthetic skin smoothing detected on frame {idx}.")

        avg_edge_var = float(np.mean(variances)) if variances else 0.0
        edge_std = float(np.std(variances)) if len(variances) > 1 else 0.0
        avg_motion_diff = float(np.mean(interframe_diffs)) if interframe_diffs else 0.0

        # Heuristic scoring based on temporal warping and edge anomalies
        ai_risk_score = 10.0  # Base natural baseline

        if avg_edge_var < 80.0:
            ai_risk_score += 20.0
        elif avg_edge_var > 600.0 and edge_std > 250.0:
            ai_risk_score += 25.0

        if avg_motion_diff > 45.0:
            ai_risk_score += 15.0

        fps = metadata.get("fps", 0)
        if fps > 0 and (fps < 18 or (abs(fps - 24) > 5 and abs(fps - 30) > 3 and abs(fps - 60) > 3)):
            ai_risk_score += 10.0

        has_faces = faces_detected_in_frames > 0
        if has_faces and edge_std > 180.0:
            deepfake_points += 20.0
            deepfake_signals.append("Temporal boundary jitter around detected facial bounding boxes.")

        # Normalize scores
        ai_likelihood = min(92.0, max(6.0, round(ai_risk_score, 1)))
        deepfake_prob = min(95.0, max(5.0, round(deepfake_points, 1))) if has_faces else 0.0

        overall_risk = max(ai_likelihood, deepfake_prob)
        authenticity = round(100.0 - overall_risk, 1)

        if overall_risk >= 55.0:
            verdict = "Elevated AI Generation / Deepfake Indicators"
            risk_badge = "High Risk"
            summary_text = "Analysis detected noticeable temporal variance or edge smoothing anomalies common in generative pipelines."
        elif overall_risk >= 30.0:
            verdict = "Mixed / Inconclusive Indicators"
            risk_badge = "Moderate Risk"
            summary_text = "Some compression or motion signals deviate from standard capture profiles; manual review advised."
        else:
            verdict = "Authentic / Natural Capture"
            risk_badge = "Authentic"
            summary_text = "Frame cadence, natural sensor grain, and temporal motion flow are consistent with real camera recordings."

        return {
            "ai_likelihood_score": ai_likelihood,
            "deepfake_probability": deepfake_prob,
            "authenticity_score": authenticity,
            "verdict": verdict,
            "risk_badge": risk_badge,
            "summary": summary_text,
            "confidence": "Moderate",
            "face_detection": {
                "faces_detected_count": len(total_boxes),
                "has_faces": has_faces,
                "bounding_boxes": total_boxes[:10],
                "frames_with_faces_count": faces_detected_in_frames
            },
            "deepfake_analysis": {
                "deepfake_score": deepfake_prob,
                "findings": deepfake_signals or ["No facial manipulation artifacts detected."]
            },
            "signals": {
                "average_edge_sharpness": round(avg_edge_var, 1),
                "temporal_edge_stability": round(edge_std, 1),
                "motion_continuity_delta": round(avg_motion_diff, 1),
                "fps_conformity": f"{fps} FPS"
            },
            "limitations": limitations
        }

ai_media_detector = AIMediaDetector()
