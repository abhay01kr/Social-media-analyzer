import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL,
                verdict TEXT,
                summary TEXT,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

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
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO reports (id, type, target, status, score, verdict, summary, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (report_id, report_type, target, status, score, verdict, summary, data_json, created_at)
        )
        conn.commit()
    
    return {
        "id": report_id,
        "type": report_type,
        "target": target,
        "status": status,
        "score": score,
        "verdict": verdict,
        "summary": summary,
        "data": data,
        "created_at": created_at
    }

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "type": row["type"],
            "target": row["target"],
            "status": row["status"],
            "score": row["score"],
            "verdict": row["verdict"],
            "summary": row["summary"],
            "data": json.loads(row["data"]),
            "created_at": row["created_at"]
        }

def list_reports(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        reports = []
        for row in rows:
            reports.append({
                "id": row["id"],
                "type": row["type"],
                "target": row["target"],
                "status": row["status"],
                "score": row["score"],
                "verdict": row["verdict"],
                "summary": row["summary"],
                "data": json.loads(row["data"]),
                "created_at": row["created_at"]
            })
        return reports
