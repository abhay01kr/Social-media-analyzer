"""
Unified Database Layer for Social Media Analyzer (Member 6 Architecture).
Primary: MongoDB Database
Fallback: SQLite Database
Ensures the server runs reliably both in production with MongoDB and locally without requiring external services.
"""
from typing import Optional, Dict, Any, List
from .mongo_db import mongo_manager
from . import db as sqlite_db
from . import auth_db as sqlite_auth_db

def get_active_db_type() -> str:
    return "MongoDB" if mongo_manager.is_connected else "SQLite"

# ----------------- Reports -----------------

def save_report(
    report_id: str,
    report_type: str,
    target: str,
    status: str,
    score: Optional[float],
    verdict: Optional[str],
    summary: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    if mongo_manager.is_connected:
        try:
            return mongo_manager.save_report(
                report_id=report_id,
                report_type=report_type,
                target=target,
                status=status,
                score=score,
                verdict=verdict,
                summary=summary,
                data=data
            )
        except Exception as e:
            print(f"[UnifiedDB] Error saving to MongoDB ({e}), falling back to SQLite.")

    return sqlite_db.save_report(
        report_id=report_id,
        report_type=report_type,
        target=target,
        status=status,
        score=score,
        verdict=verdict,
        summary=summary,
        data=data
    )

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    if mongo_manager.is_connected:
        try:
            report = mongo_manager.get_report_by_id(report_id)
            if report:
                return report
        except Exception:
            pass
    return sqlite_db.get_report_by_id(report_id)

def list_reports(limit: int = 50, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
    if mongo_manager.is_connected:
        try:
            return mongo_manager.list_reports(limit=limit, report_type=report_type)
        except Exception:
            pass
    reports = sqlite_db.list_reports(limit=limit)
    if report_type:
        reports = [r for r in reports if r.get("type") == report_type]
    return reports

def delete_report(report_id: str) -> bool:
    if mongo_manager.is_connected:
        try:
            res = mongo_manager.delete_report(report_id)
            if res:
                return True
        except Exception:
            pass
    # Also attempt delete in SQLite
    try:
        with sqlite_db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False
