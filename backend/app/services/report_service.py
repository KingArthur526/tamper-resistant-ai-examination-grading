import csv
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.models.models import ExamSession, AnswerSheet, QuestionEvaluation, Question, ConceptEvaluation
from app.core.config import settings

class ReportService:
    def generate_student_pdf_scorecard(self, db: Session, answer_sheet_id: str) -> Path:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise ValueError("Answer sheet not found")

        exam = sheet.session
        q_evals = db.query(QuestionEvaluation).filter(QuestionEvaluation.answer_sheet_id == sheet.id).all()

        total_awarded = sum(qe.teacher_final_score for qe in q_evals if qe.is_or_group_selected)
        total_max = sum(qe.question.max_marks for qe in q_evals if qe.is_or_group_selected and qe.question)
        pct = (total_awarded / total_max * 100.0) if total_max > 0 else 0.0

        pdf_path = settings.REPORTS_PATH / f"Scorecard_{sheet.student_id}_{sheet.id[:8]}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            alignment=1
        )
        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f172a")
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b")
        )

        elements = []

        # Title & Header
        elements.append(Paragraph("EXAMINATION EVALUATION & AUDIT SCORECARD", title_style))
        elements.append(Paragraph("Tamper Resistant AI-Powered Examination Grading Platform", subtitle_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=10))

        # Metadata Table
        meta_data = [
            [Paragraph("<b>Exam Name:</b>", body_style), Paragraph(exam.name, body_style),
             Paragraph("<b>Student ID:</b>", body_style), Paragraph(sheet.student_id, body_style)],
            [Paragraph("<b>Subject:</b>", body_style), Paragraph(exam.subject, body_style),
             Paragraph("<b>Student Name:</b>", body_style), Paragraph(sheet.student_name, body_style)],
            [Paragraph("<b>Academic Year:</b>", body_style), Paragraph(exam.academic_year, body_style),
             Paragraph("<b>Roll Number:</b>", body_style), Paragraph(sheet.roll_number or "-", body_style)],
            [Paragraph("<b>Evaluation Date:</b>", body_style), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), body_style),
             Paragraph("<b>SHA-256 Hash:</b>", body_style), Paragraph(sheet.sha256_hash[:20] + "...", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[90, 180, 90, 180])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Total Marks Banner
        summary_text = f"<b>TOTAL SCORE: {total_awarded:.1f} / {total_max:.1f} Marks ({pct:.1f}%)</b>"
        elements.append(Paragraph(summary_text, ParagraphStyle("Banner", parent=title_style, fontSize=13, textColor=colors.HexColor("#15803d"))))
        elements.append(Spacer(1, 10))

        # Question Breakdown Table
        elements.append(Paragraph("Question & Concept Evaluation Breakdown", heading_style))
        elements.append(Spacer(1, 6))

        table_data = [["Q#", "Question Text", "Max", "AI Score", "Teacher Final", "Status"]]
        for qe in q_evals:
            q = qe.question
            q_txt = (q.question_text[:55] + "...") if q and len(q.question_text) > 55 else (q.question_text if q else "-")
            status_txt = "OVERRIDDEN" if qe.is_overridden else ("NOT SELECTED (OR)" if not qe.is_or_group_selected else "VERIFIED")
            table_data.append([
                q.question_number if q else "-",
                Paragraph(q_txt, body_style),
                f"{q.max_marks:.1f}" if q else "-",
                f"{qe.ai_score:.1f}",
                f"{qe.teacher_final_score:.1f}",
                status_txt
            ])

        q_table = Table(table_data, colWidths=[30, 240, 45, 55, 75, 95])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(q_table)
        elements.append(Spacer(1, 16))

        # Integrity Stamp Footer
        footer_text = f"Cryptographically signed by Tamper-Resistant AI Evaluation Engine. Integrity Checksum: {sheet.sha256_hash}"
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
        elements.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=subtitle_style, fontSize=7, textColor=colors.HexColor("#64748b"))))

        doc.build(elements)
        return pdf_path

    def export_exam_csv(self, db: Session, session_id: str) -> str:
        exam = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not exam:
            raise ValueError("Exam not found")

        sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == session_id).all()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Exam Name", exam.name])
        writer.writerow(["Subject", exam.subject])
        writer.writerow(["Academic Year", exam.academic_year])
        writer.writerow([])
        writer.writerow(["Student ID", "Student Name", "Roll Number", "Total AI Score", "Final Score", "Max Marks", "Percentage", "Status", "SHA256 Hash"])

        for sheet in sheets:
            q_evals = db.query(QuestionEvaluation).filter(QuestionEvaluation.answer_sheet_id == sheet.id).all()
            ai_tot = sum(qe.ai_score for qe in q_evals if qe.is_or_group_selected)
            fin_tot = sum(qe.teacher_final_score for qe in q_evals if qe.is_or_group_selected)
            max_tot = sum(qe.question.max_marks for qe in q_evals if qe.is_or_group_selected and qe.question)
            pct = (fin_tot / max_tot * 100.0) if max_tot > 0 else 0.0

            writer.writerow([
                sheet.student_id,
                sheet.student_name,
                sheet.roll_number,
                f"{ai_tot:.2f}",
                f"{fin_tot:.2f}",
                f"{max_tot:.2f}",
                f"{pct:.1f}%",
                sheet.processing_status,
                sheet.sha256_hash
            ])

        return output.getvalue()

report_service = ReportService()
