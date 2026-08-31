from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, AnswerSheet, ExamSession
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/pdf/student/{sheet_id}")
def download_student_pdf(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pdf_path = report_service.generate_student_pdf_scorecard(db, sheet_id)
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"Scorecard_{sheet_id[:8]}.pdf"
    )

@router.get("/csv/exam/{exam_id}")
def download_exam_csv(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    csv_data = report_service.export_exam_csv(db, exam_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Exam_Results_{exam_id[:8]}.csv"}
    )
