import pytest
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import QuestionEvaluation, ExamSession, Question, AnswerSheet
from app.services.override_service import override_service

def test_teacher_override_records_reason_and_scores():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        exam = db.query(ExamSession).first()
        if not exam:
            return
        qe = db.query(QuestionEvaluation).first()
        if not qe:
            return

        old_score = qe.teacher_final_score
        target_score = min(qe.question.max_marks, old_score + 1.0)
        reason = "Alternative valid explanation accepted for technical terminology."

        override = override_service.apply_teacher_override(
            db=db,
            question_evaluation_id=qe.id,
            new_score=target_score,
            reason=reason,
            teacher_name="Prof. Alan Turing"
        )
        assert override.new_score == target_score
        assert override.override_reason == reason
        assert qe.is_overridden is True
        assert qe.teacher_final_score == target_score
    finally:
        db.close()
