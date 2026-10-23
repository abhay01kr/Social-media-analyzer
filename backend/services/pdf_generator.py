import io
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

class PDFReportGenerator:
    """
    Member 5 - PDF Report Generator.
    Produces high-fidelity downloadable forensic reports using ReportLab.
    """

    def generate_pdf_bytes(self, report_data: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        elements = []

        # Color scheme
        primary_color = colors.HexColor("#1e293b")  # Dark slate
        accent_color = colors.HexColor("#2563eb")   # Royal blue
        success_color = colors.HexColor("#16a34a")  # Green
        warning_color = colors.HexColor("#d97706")  # Amber
        danger_color = colors.HexColor("#dc2626")   # Red
        light_bg = colors.HexColor("#f8fafc")

        # Custom Styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        # 1. Header Banner
        elements.append(Paragraph("SOCIAL MEDIA ANALYZER", title_style))
        elements.append(Paragraph("Official Authenticity & Risk Forensic Report", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=15))

        # Extract Report Fields
        report_id = report_data.get("id", report_data.get("report_id", "N/A"))
        report_type = report_data.get("type", report_data.get("media_type", "Comprehensive")).capitalize()
        target = report_data.get("target", report_data.get("filename", report_data.get("username", "Unknown Subject")))
        created_at = report_data.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
        score = report_data.get("score", report_data.get("trust_score", report_data.get("authenticity_score", 0.0)))
        verdict = report_data.get("verdict", "Evaluated")
        summary = report_data.get("summary", "Analysis completed.")

        # Determine Score Badge Color
        score_val = float(score) if score is not None else 0.0
        if score_val >= 70.0:
            badge_color = success_color
            status_text = "TRUSTED / LOW RISK"
        elif score_val >= 40.0:
            badge_color = warning_color
            status_text = "MODERATE RISK"
        else:
            badge_color = danger_color
            status_text = "HIGH RISK / SUSPICIOUS"

        # 2. Executive Overview Table
        overview_data = [
            [
                Paragraph("<b>Report Identifier:</b>", body_style),
                Paragraph(str(report_id), body_style),
                Paragraph("<b>Analysis Date:</b>", body_style),
                Paragraph(str(created_at)[:19], body_style)
            ],
            [
                Paragraph("<b>Analysis Category:</b>", body_style),
                Paragraph(str(report_type), body_style),
                Paragraph("<b>Target Subject:</b>", body_style),
                Paragraph(str(target)[:30], body_style)
            ]
        ]

        overview_table = Table(overview_data, colWidths=[120, 150, 110, 150])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 15))

        # 3. Overall Authenticity Score Banner
        score_cell = Paragraph(
            f"<font size=28 color='{badge_color.hexval()}'><b>{score_val:.1f}%</b></font><br/>"
            f"<font size=10 color='#64748b'>COMPOSITE TRUST INDEX</font>",
            body_style
        )
        verdict_cell = Paragraph(
            f"<font size=14 color='{badge_color.hexval()}'><b>{status_text}</b></font><br/>"
            f"<font size=10 color='#334155'>{verdict}</font><br/><br/>"
            f"<font size=9 color='#475569'>{summary}</font>",
            body_style
        )

        score_table = Table([[score_cell, verdict_cell]], colWidths=[160, 370])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, badge_color),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 15))

        # 4. Detailed Breakdown Section
        elements.append(Paragraph("Signal Evaluation & Heuristics", section_heading))

        details = report_data.get("data", report_data)
        breakdown_rows = [
            [
                Paragraph("<b>Audit Module</b>", body_style),
                Paragraph("<b>Signal Inspected</b>", body_style),
                Paragraph("<b>Finding / Status</b>", body_style)
            ]
        ]

        # Extract evidence or details if available
        if "evidence" in details and isinstance(details["evidence"], list):
            for item in details["evidence"][:8]:
                sig = item.get("signal", "Signal")
                finding = item.get("finding", "Observed pattern")
                impact = item.get("impact", "")
                breakdown_rows.append([
                    Paragraph(str(report_type), body_style),
                    Paragraph(f"<b>{sig}</b>", body_style),
                    Paragraph(f"{finding} <font color='#64748b'>({impact})</font>", body_style)
                ])

        elif "metadata" in details:
            meta = details["metadata"]
            breakdown_rows.append([Paragraph("Video Codec", body_style), Paragraph("Stream Format", body_style), Paragraph(str(meta.get("codec")), body_style)])
            breakdown_rows.append([Paragraph("Duration & FPS", body_style), Paragraph("Temporal Cadence", body_style), Paragraph(f"{meta.get('duration')}s @ {meta.get('fps')} FPS", body_style)])
            breakdown_rows.append([Paragraph("Resolution", body_style), Paragraph("Frame Geometry", body_style), Paragraph(f"{meta.get('resolution')} ({meta.get('aspect_ratio')})", body_style)])
            breakdown_rows.append([Paragraph("AI Likelihood", body_style), Paragraph("Temporal Smoothness", body_style), Paragraph(f"{details.get('deepfake_probability', 10.0)}% synthetic score", body_style)])

        elif "spam_detection" in details:
            spam = details["spam_detection"]
            toxic = details.get("toxic_comments", {})
            hate = details.get("hate_speech_detection", {})
            nsfw = details.get("nsfw_detection", {})
            breakdown_rows.append([Paragraph("Spam Analyzer", body_style), Paragraph("Commercial Patterns", body_style), Paragraph(f"Spam Score: {spam.get('spam_score')}%", body_style)])
            breakdown_rows.append([Paragraph("Toxicity Analyzer", body_style), Paragraph("Profanity & Aggression", body_style), Paragraph(f"Toxicity: {toxic.get('toxicity_score')}% ({toxic.get('severity')})", body_style)])
            breakdown_rows.append([Paragraph("Hate Speech", body_style), Paragraph("Targeted Discrimination", body_style), Paragraph(f"Hate Score: {hate.get('hate_speech_score')}%", body_style)])
            breakdown_rows.append([Paragraph("NSFW Analyzer", body_style), Paragraph("Adult & Violence", body_style), Paragraph(f"NSFW Score: {nsfw.get('nsfw_score')}%", body_style)])

        else:
            breakdown_rows.append([
                Paragraph("Forensics", body_style),
                Paragraph("General Inspection", body_style),
                Paragraph(str(summary), body_style)
            ])

        details_table = Table(breakdown_rows, colWidths=[120, 150, 260])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 15))

        # 5. Recommendation & Advisory
        elements.append(Paragraph("Actionable Recommendations", section_heading))
        rec_text = details.get("recommendation", details.get("action_recommendation", "Continue monitoring account. Conduct secondary checks if suspicious signals escalate."))
        elements.append(Paragraph(f"• <b>Recommended Response:</b> {rec_text}", body_style))
        elements.append(Paragraph("• <b>Integrity Notice:</b> Analysis incorporates statistical heuristics across permitted signals and does not represent absolute proof of fraud.", body_style))
        elements.append(Spacer(1, 20))

        # Footer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#94a3b8"))
        elements.append(Paragraph(f"Generated by Social Media Analyzer | Backend API Server | MongoDB & Microservices Architecture | {created_at[:10]}", footer_style))

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer

pdf_generator = PDFReportGenerator()
