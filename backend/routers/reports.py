import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from models.report_models import FinalReportRequest
from services.report_service import report_service
from services.pdf_generator import pdf_generator
from database.db_unified import get_report_by_id, list_reports, delete_report

router = APIRouter(tags=["Member 5 - Report & Dashboard"])

# ==================== FINAL REPORT GENERATION ====================

@router.post("/report")
@router.post("/api/report")
def create_final_report(payload: FinalReportRequest):
    """
    Member 5 - Generate Final Report.
    Synthesizes Profile, Media, and Content analyses into a unified audit report.
    """
    report = report_service.generate_final_report(
        title=payload.title,
        target=payload.target,
        profile_data=payload.profile_data,
        media_data=payload.media_data,
        content_data=payload.content_data,
        notes=payload.notes
    )
    return {
        "status": "success",
        "message": "Final report generated successfully.",
        "report": report
    }

@router.get("/report/{report_id}")
@router.get("/api/report/{report_id}")
@router.get("/api/reports/{report_id}")
def get_report(report_id: str):
    """Retrieve full report by ID."""
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return report

# ==================== PDF REPORT DOWNLOAD ====================

@router.get("/report/{report_id}/pdf")
@router.get("/api/report/{report_id}/pdf")
@router.get("/api/reports/{report_id}/pdf")
def download_pdf_report(report_id: str):
    """
    Member 5 - Generate Downloadable PDF Report.
    Produces high-fidelity downloadable forensic PDF via ReportLab.
    """
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    pdf_buffer = pdf_generator.generate_pdf_bytes(report)
    filename = f"SMA_Report_{report_id[:8]}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

# ==================== ANALYSIS HISTORY ====================

@router.get("/history")
@router.get("/api/history")
@router.get("/api/reports")
def get_analysis_history(
    type: Optional[str] = Query(None, description="Filter by analysis type (profile, video, image, content, consolidated)"),
    search: Optional[str] = Query(None, description="Search by target or summary text"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Member 5 - Analysis History.
    Returns logged analyses with search and type filtering.
    """
    reports = list_reports(limit=limit, report_type=type)

    if search and search.strip():
        term = search.strip().lower()
        reports = [
            r for r in reports
            if term in str(r.get("target", "")).lower()
            or term in str(r.get("summary", "")).lower()
            or term in str(r.get("verdict", "")).lower()
        ]

    return {
        "status": "success",
        "total": len(reports),
        "history": reports
    }

@router.delete("/history/{report_id}")
@router.delete("/api/history/{report_id}")
def delete_history_item(report_id: str):
    """Deletes an analysis report from history."""
    success = delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found or could not be deleted.")
    return {
        "status": "success",
        "message": f"Report '{report_id}' deleted successfully."
    }

# ==================== DASHBOARD METRICS ====================

@router.get("/dashboard")
@router.get("/api/dashboard")
def get_dashboard_data():
    """
    Member 5 - Dashboard Endpoint.
    Aggregates statistical overview of analyses, risk distributions, and system health.
    """
    metrics = report_service.get_dashboard_metrics()
    return {
        "status": "success",
        **metrics
    }
