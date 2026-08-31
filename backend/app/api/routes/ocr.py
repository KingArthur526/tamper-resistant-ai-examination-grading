from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, AnswerSheet, StudentAnswer
from app.schemas.schemas import OCRReviewResponse, StudentAnswerDetail, OCRCorrectionRequest
from app.services.ocr_service import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR & Segmentation"])

@router.post("/process/{sheet_id}")
def process_ocr(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheet = ocr_service.process_answer_sheet_ocr(db, sheet_id, user_id=current_user.id)
    return {"message": "OCR processed successfully", "status": sheet.processing_status, "confidence": sheet.ocr_confidence_avg}

@router.post("/process-all/{exam_id}")
def process_all_ocr(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == exam_id).all()
    count = 0
    for s in sheets:
        ocr_service.process_answer_sheet_ocr(db, s.id, user_id=current_user.id)
        count += 1
    return {"message": f"Processed OCR for {count} answer sheets", "count": count}

from pathlib import Path
from app.schemas.schemas import OCRReviewResponse, StudentAnswerDetail, OCRCorrectionRequest, EntireSheetCorrectionRequest, AnswerSheetPage

@router.get("/review/{sheet_id}", response_model=OCRReviewResponse)
def get_ocr_review(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Answer sheet not found")

    # Find all answer sheets/pages belonging to this candidate in this exam session
    sibling_sheets = db.query(AnswerSheet).filter(
        AnswerSheet.session_id == sheet.session_id,
        AnswerSheet.student_id == sheet.student_id
    ).order_by(AnswerSheet.uploaded_at.asc()).all()

    pages = []
    for idx, sib in enumerate(sibling_sheets, start=1):
        pages.append(AnswerSheetPage(
            page_number=idx,
            sheet_id=sib.id,
            image_url=f"/api/answer-sheets/{sib.id}/original-file",
            preprocessed_image_url=f"/api/answer-sheets/{sib.id}/preprocessed-file" if sib.preprocessed_path else None,
            filename=sib.original_filename,
            sha256_hash=sib.sha256_hash
        ))

    # Read raw entire sheet text transcript if exists
    raw_entire_text = ""
    if sheet.ocr_raw_path and Path(sheet.ocr_raw_path).exists():
        try:
            raw_entire_text = Path(sheet.ocr_raw_path).read_text(encoding="utf-8")
        except Exception:
            pass

    answers = db.query(StudentAnswer).filter(StudentAnswer.answer_sheet_id == sheet.id).all()
    ans_details = []
    for a in answers:
        q = a.question
        ans_details.append(StudentAnswerDetail(
            id=a.id,
            question_id=a.question_id,
            question_number=q.question_number if q else "-",
            question_text=q.question_text if q else "-",
            max_marks=q.max_marks if q else 0.0,
            raw_ocr_text=a.raw_ocr_text,
            cleaned_text=a.cleaned_text,
            teacher_edited_text=a.teacher_edited_text,
            is_edited=a.is_edited,
            ocr_confidence=a.ocr_confidence,
            segmentation_confidence=a.segmentation_confidence,
            attempted=a.attempted
        ))

    return OCRReviewResponse(
        answer_sheet_id=sheet.id,
        student_id=sheet.student_id,
        student_name=sheet.student_name,
        original_filename=sheet.original_filename,
        sha256_hash=sheet.sha256_hash,
        original_image_url=f"/api/answer-sheets/{sheet.id}/original-file",
        preprocessed_image_url=f"/api/answer-sheets/{sheet.id}/preprocessed-file" if sheet.preprocessed_path else None,
        ocr_confidence_avg=sheet.ocr_confidence_avg,
        status=sheet.processing_status,
        pages=pages,
        raw_entire_sheet_text=raw_entire_text,
        answers=ans_details
    )

@router.post("/correct/{sheet_id}")
def submit_ocr_corrections(
    sheet_id: str,
    data: OCRCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    corrections_payload = [
        {"student_answer_id": c.student_answer_id, "edited_text": c.edited_text}
        for c in data.corrections
    ]
    sheet = ocr_service.submit_corrections(
        db=db,
        answer_sheet_id=sheet_id,
        corrections=corrections_payload,
        user_id=current_user.id,
        re_evaluate=data.re_evaluate
    )
    return {
        "message": "OCR corrections saved and evaluation recomputed successfully",
        "status": sheet.processing_status
    }

@router.post("/correct-entire-raw/{sheet_id}")
def update_entire_raw_ocr(
    sheet_id: str,
    data: EntireSheetCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.entire_text is not None:
        sheet = ocr_service.update_entire_sheet_raw_text(
            db=db,
            answer_sheet_id=sheet_id,
            entire_raw_text=data.entire_text,
            user_id=current_user.id,
            re_evaluate=data.re_evaluate
        )
    elif data.corrections:
        corrections_payload = [
            {"student_answer_id": c.student_answer_id, "edited_text": c.edited_text}
            for c in data.corrections
        ]
        sheet = ocr_service.submit_corrections(
            db=db,
            answer_sheet_id=sheet_id,
            corrections=corrections_payload,
            user_id=current_user.id,
            re_evaluate=data.re_evaluate
        )
    else:
        raise HTTPException(status_code=400, detail="No text or corrections provided")

    return {
        "message": "Entire answer sheet corrected and re-evaluated successfully",
        "status": sheet.processing_status
    }

@router.post("/approve/{sheet_id}")
def approve_ocr(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheet = ocr_service.approve_ocr(db, sheet_id, user_id=current_user.id)
    return {"message": "OCR approved", "status": sheet.processing_status}
