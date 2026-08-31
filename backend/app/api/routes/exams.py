from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, ExamSession, Question, AnswerSheet, QuestionGroup, QuestionEvaluation
from app.schemas.schemas import (
    ExamSessionCreate, ExamSessionUpdate, ExamSessionResponse, DashboardStats,
    QuestionGroupCreate, QuestionGroupResponse
)
from app.services.exam_service import exam_service

router = APIRouter(prefix="/exams", tags=["Examinations"])

@router.get("/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exams = db.query(ExamSession).order_by(ExamSession.created_at.desc()).all()
    sheets = db.query(AnswerSheet).all()
    
    total_evals = sum(1 for s in sheets if s.processing_status in ["EVALUATED", "FINALIZED"])
    pending_evals = len(sheets) - total_evals
    
    # Calculate average marks
    all_evals = db.query(QuestionEvaluation).filter(QuestionEvaluation.is_or_group_selected == True).all()
    total_awarded = sum(e.teacher_final_score for e in all_evals)
    total_max = sum(e.question.max_marks for e in all_evals if e.question)
    avg_pct = (total_awarded / total_max * 100.0) if total_max > 0 else 0.0

    return {
        "total_exams": len(exams),
        "active_exams": sum(1 for e in exams if e.status != "FINALIZED"),
        "completed_evaluations": total_evals,
        "pending_evaluations": pending_evals,
        "total_answer_sheets": len(sheets),
        "average_marks_percentage": round(avg_pct, 1),
        "recent_exams": exams[:5]
    }

@router.get("", response_model=List[ExamSessionResponse])
def list_exams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exams = db.query(ExamSession).order_by(ExamSession.created_at.desc()).all()
    for e in exams:
        e.total_answer_sheets = len(e.answer_sheets)
        e.evaluated_count = sum(1 for s in e.answer_sheets if s.processing_status in ["EVALUATED", "FINALIZED"])
    return exams

@router.post("", response_model=ExamSessionResponse)
def create_exam(data: ExamSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return exam_service.create_exam_session(db, data, creator_id=current_user.id)

@router.get("/{exam_id}", response_model=ExamSessionResponse)
def get_exam(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    exam.total_answer_sheets = len(exam.answer_sheets)
    exam.evaluated_count = sum(1 for s in exam.answer_sheets if s.processing_status in ["EVALUATED", "FINALIZED"])
    return exam

@router.put("/{exam_id}", response_model=ExamSessionResponse)
def update_exam(exam_id: str, data: ExamSessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    for field, val in data.dict(exclude_unset=True).items():
        setattr(exam, field, val)
    db.commit()
    db.refresh(exam)
    return exam

@router.delete("/{exam_id}")
def delete_exam(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    db.delete(exam)
    db.commit()
    return {"message": "Exam session deleted successfully"}

@router.post("/{exam_id}/question-groups", response_model=QuestionGroupResponse)
def create_question_group(exam_id: str, data: QuestionGroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grp = QuestionGroup(
        session_id=exam_id,
        name=data.name,
        group_type=data.group_type,
        selection_policy=data.selection_policy,
        max_selectable_marks=data.max_selectable_marks
    )
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return grp
