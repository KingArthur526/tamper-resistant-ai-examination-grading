from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import QuestionEvaluation, TeacherOverride, User
from app.services.audit_service import log_audit_event

class OverrideService:
    def apply_teacher_override(
        self,
        db: Session,
        question_evaluation_id: str,
        new_score: float,
        reason: str,
        teacher_id: str = None,
        teacher_name: str = "Teacher"
    ) -> TeacherOverride:
        q_eval = db.query(QuestionEvaluation).filter(QuestionEvaluation.id == question_evaluation_id).first()
        if not q_eval:
            raise HTTPException(status_code=404, detail="Question evaluation not found")

        max_marks = q_eval.question.max_marks if q_eval.question else 100.0
        if new_score < 0.0 or new_score > max_marks:
            raise HTTPException(status_code=400, detail=f"Override score must be between 0 and {max_marks}")

        prev_score = q_eval.teacher_final_score
        q_eval.teacher_final_score = new_score
        q_eval.is_overridden = True
        q_eval.status = "OVERRIDDEN"

        override_entry = TeacherOverride(
            question_evaluation_id=q_eval.id,
            previous_score=prev_score,
            new_score=new_score,
            override_reason=reason,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(override_entry)
        db.commit()
        db.refresh(override_entry)

        # Log audit trail event
        log_audit_event(
            db=db,
            action="TEACHER_SCORE_OVERRIDE",
            entity_type="QuestionEvaluation",
            entity_id=q_eval.id,
            session_id=q_eval.question.session_id if q_eval.question else None,
            user_id=teacher_id,
            payload={
                "previous_score": prev_score,
                "new_score": new_score,
                "reason": reason,
                "teacher_name": teacher_name
            }
        )

        return override_entry

override_service = OverrideService()
