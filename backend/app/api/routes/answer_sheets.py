from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, AnswerSheet, QuestionEvaluation
from app.schemas.schemas import AnswerSheetResponse
from app.services.answer_sheet_service import answer_sheet_service

router = APIRouter(prefix="/answer-sheets", tags=["Answer Sheets"])

@router.get("/exam/{exam_id}", response_model=List[AnswerSheetResponse])
def get_exam_answer_sheets(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == exam_id).order_by(AnswerSheet.uploaded_at.desc()).all()
    results = []
    for s in sheets:
        q_evals = db.query(QuestionEvaluation).filter(QuestionEvaluation.answer_sheet_id == s.id).all()
        tot_score = sum(qe.teacher_final_score for qe in q_evals if qe.is_or_group_selected) if q_evals else None
        tot_max = sum(qe.question.max_marks for qe in q_evals if qe.is_or_group_selected and qe.question) if q_evals else None
        pct = (tot_score / tot_max * 100.0) if (tot_score is not None and tot_max and tot_max > 0) else None
        needs_rev = any(qe.needs_review for qe in q_evals) or s.processing_status == "NEEDS_OCR_REVIEW"

        resp = AnswerSheetResponse.from_orm(s)
        resp.total_score = tot_score
        resp.max_marks = tot_max
        resp.percentage = round(pct, 1) if pct is not None else None
        resp.needs_review = needs_rev
        results.append(resp)
    return results

@router.post("/upload/{exam_id}", response_model=AnswerSheetResponse)
async def upload_sheet(
    exam_id: str,
    file: UploadFile = File(...),
    student_id: str = Form(...),
    student_name: str = Form(...),
    roll_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sheet = await answer_sheet_service.upload_answer_sheet(
        db=db,
        session_id=exam_id,
        file=file,
        student_id=student_id,
        student_name=student_name,
        roll_number=roll_number,
        user_id=current_user.id
    )
    return sheet

@router.get("/{sheet_id}/original-file")
def get_original_file(sheet_id: str, db: Session = Depends(get_db)):
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet or not sheet.storage_path or not Path(sheet.storage_path).exists():
        raise HTTPException(status_code=404, detail="Original file not found")
    return FileResponse(sheet.storage_path)

@router.get("/{sheet_id}/preprocessed-file")
def get_preprocessed_file(sheet_id: str, db: Session = Depends(get_db)):
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet or not sheet.preprocessed_path or not Path(sheet.preprocessed_path).exists():
        # If not preprocessed yet, return original
        if sheet and sheet.storage_path and Path(sheet.storage_path).exists():
            return FileResponse(sheet.storage_path)
        raise HTTPException(status_code=404, detail="Preprocessed file not found")
    return FileResponse(sheet.preprocessed_path)
