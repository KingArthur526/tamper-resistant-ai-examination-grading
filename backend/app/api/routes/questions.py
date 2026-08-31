from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, Question, RubricConcept, ExamSession
from app.schemas.schemas import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    RubricConceptCreate, RubricConceptResponse, RubricValidationResponse
)
from app.services.exam_service import exam_service

router = APIRouter(prefix="/questions", tags=["Questions & Rubrics"])

@router.post("/validate-rubric", response_model=RubricValidationResponse)
def validate_rubric_live(question_max_marks: float, concepts: List[RubricConceptCreate]):
    return exam_service.validate_rubric(question_max_marks, concepts)

@router.get("/exam/{exam_id}", response_model=List[QuestionResponse])
def get_exam_questions(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Question).filter(Question.session_id == exam_id).order_by(Question.question_number).all()

@router.post("/exam/{exam_id}", response_model=QuestionResponse)
def add_question_to_exam(exam_id: str, data: QuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = exam_service.add_question(db, exam_id, data)
    # Update total marks
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if exam:
        all_qs = db.query(Question).filter(Question.session_id == exam_id).all()
        exam.total_marks = sum(q_item.max_marks for q_item in all_qs)
        db.commit()
    return q

@router.delete("/{question_id}")
def delete_question(question_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    exam_id = q.session_id
    db.delete(q)
    db.commit()
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if exam:
        all_qs = db.query(Question).filter(Question.session_id == exam_id).all()
        exam.total_marks = sum(q_item.max_marks for q_item in all_qs)
        db.commit()
    return {"message": "Question deleted"}

@router.post("/{question_id}/concepts", response_model=RubricConceptResponse)
def add_concept(question_id: str, data: RubricConceptCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    concept = RubricConcept(
        question_id=q.id,
        concept_code=data.concept_code,
        name=data.name,
        description=data.description,
        reference_text=data.reference_text,
        max_marks=data.max_marks,
        required=data.required,
        full_match_threshold=data.full_match_threshold,
        partial_match_threshold=data.partial_match_threshold,
        keywords=data.keywords,
        negative_indicators=data.negative_indicators,
        weight=data.weight
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept

@router.delete("/concepts/{concept_id}")
def delete_concept(concept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(RubricConcept).filter(RubricConcept.id == concept_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Concept not found")
    db.delete(c)
    db.commit()
    return {"message": "Concept deleted"}
