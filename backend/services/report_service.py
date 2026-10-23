import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_unified import save_report, get_report_by_id, list_reports, delete_report, get_active_db_type

class ReportService:
    """
    Member 5 - Report & Dashboard Service.
    Handles:
    - Multi-modal Consolidated Final Reports
    - Analysis History Retrieval & Filtering
    - Dashboard Statistics & Metrics
    """

    def generate_final_report(
        self,
        title: str,
        target: str,
        profile_data: Optional[Dict[str, Any]] = None,
        media_data: Optional[Dict[str, Any]] = None,
        content_data: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        scores = []
        verdict_weights = []

        if profile_data:
            p_score = profile_data.get("trust_score", 50.0)
            scores.append(p_score)
            verdict_weights.append(profile_data.get("verdict_badge", "Moderate Risk"))

        if media_data:
            m_score = media_data.get("authenticity_score", 50.0)
            scores.append(m_score)
            verdict_weights.append(media_data.get("verdict", "Moderate Risk"))

        if content_data:
            c_score = content_data.get("overall_safety_score", 50.0)
            scores.append(c_score)
            verdict_weights.append(content_data.get("verdict_badge", "Safe"))

        avg_score = round(sum(scores) / len(scores), 1) if scores else 75.0

        if avg_score >= 70.0 and "High Risk" not in verdict_weights:
            verdict = "Authentic / Trusted Overall"
            verdict_badge = "Trusted"
            summary = "Target displays consistent authentic behavioral, media, and communication signals."
        elif avg_score >= 40.0:
            verdict = "Moderate Risk / Ambiguous Signals"
            verdict_badge = "Moderate Risk"
            summary = "Cross-module signals reveal mixed credibility indicators requiring human oversight."
        else:
            verdict = "High Risk / Compromised Identity"
            verdict_badge = "High Risk"
            summary = "Critical anomalies flagged across evaluated profile, media, or content channels."

        final_data = {
            "id": report_id,
            "title": title,
            "target": target,
            "type": "consolidated",
            "status": "completed",
            "score": avg_score,
            "trust_score": avg_score,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "summary": summary,
            "notes": notes,
            "profile_analysis": profile_data,
            "media_analysis": media_data,
            "content_analysis": content_data,
            "created_at": created_at
        }

        save_report(
            report_id=report_id,
            report_type="consolidated",
            target=target,
            status="completed",
            score=avg_score,
            verdict=verdict_badge,
            summary=summary,
            data=final_data
        )

        return final_data

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        all_reports = list_reports(limit=500)
        total_count = len(all_reports)

        profile_count = sum(1 for r in all_reports if r.get("type") == "profile")
        video_count = sum(1 for r in all_reports if r.get("type") == "video")
        image_count = sum(1 for r in all_reports if r.get("type") == "image")
        content_count = sum(1 for r in all_reports if r.get("type") == "content")
        consolidated_count = sum(1 for r in all_reports if r.get("type") == "consolidated")

        scores = [r.get("score") for r in all_reports if r.get("score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 84.5

        high_risk = sum(1 for r in all_reports if "high" in str(r.get("verdict", "")).lower())
        mod_risk = sum(1 for r in all_reports if "mod" in str(r.get("verdict", "")).lower())
        trusted = total_count - (high_risk + mod_risk)

        recent = all_reports[:10]

        return {
            "total_analyses": total_count,
            "breakdown": {
                "profile_analyses": profile_count,
                "video_analyses": video_count,
                "image_analyses": image_count,
                "content_analyses": content_count,
                "consolidated_reports": consolidated_count
            },
            "average_trust_score": avg_score,
            "risk_distribution": {
                "high_risk": high_risk,
                "moderate_risk": mod_risk,
                "trusted": max(0, trusted)
            },
            "database_engine": get_active_db_type(),
            "recent_activity": recent,
            "system_status": {
                "server": "healthy",
                "database": get_active_db_type(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

report_service = ReportService()
