from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import ExamSession, Question, RubricConcept, QuestionGroup, EvaluationConfig, AnswerSheet
from app.schemas.schemas import ExamSessionCreate, ExamSessionUpdate, QuestionCreate, RubricConceptCreate
from app.services.audit_service import log_audit_event
from app.core.config import settings

class ExamService:
    def create_exam_session(self, db: Session, data: ExamSessionCreate, creator_id: Optional[str] = None) -> ExamSession:
        exam = ExamSession(
            name=data.name,
            subject=data.subject,
            course_semester=data.course_semester,
            academic_year=data.academic_year,
            exam_date=data.exam_date,
            description=data.description,
            creator_id=creator_id,
            total_marks=0.0
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        # Create default evaluation config for this session
        eval_cfg = EvaluationConfig(
            session_id=exam.id,
            model_name=settings.DEFAULT_MODEL_NAME,
            full_match_threshold=settings.DEFAULT_FULL_MATCH_THRESHOLD,
            partial_match_threshold=settings.DEFAULT_PARTIAL_MATCH_THRESHOLD,
            or_selection_policy=settings.DEFAULT_OR_POLICY,
            scoring_policy_version=settings.DEFAULT_SCORING_POLICY_VERSION
        )
        db.add(eval_cfg)
        db.commit()

        # Add questions if provided
        total_marks = 0.0
        if data.questions:
            for q_data in data.questions:
                self.add_question(db, exam.id, q_data)
                total_marks += q_data.max_marks

            exam.total_marks = total_marks
            db.commit()
            db.refresh(exam)

        log_audit_event(
            db=db,
            action="EXAM_SESSION_CREATED",
            entity_type="ExamSession",
            entity_id=exam.id,
            session_id=exam.id,
            user_id=creator_id,
            payload={"name": exam.name, "subject": exam.subject, "total_marks": exam.total_marks}
        )

        return exam

    def add_question(self, db: Session, session_id: str, q_data: QuestionCreate) -> Question:
        # Validate rubric concept marks sum if concepts are provided
        if q_data.rubric_concepts:
            concepts_total = sum(c.max_marks for c in q_data.rubric_concepts)
            if round(concepts_total, 2) != round(q_data.max_marks, 2):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question {q_data.question_number} max marks ({q_data.max_marks}) must equal sum of rubric concepts ({concepts_total})."
                )

        q = Question(
            session_id=session_id,
            question_number=q_data.question_number,
            question_text=q_data.question_text,
            max_marks=q_data.max_marks,
            question_type=q_data.question_type,
            group_id=q_data.group_id,
            instructions=q_data.instructions
        )
        db.add(q)
        db.commit()
        db.refresh(q)

        for c_data in q_data.rubric_concepts:
            concept = RubricConcept(
                question_id=q.id,
                concept_code=c_data.concept_code,
                name=c_data.name,
                description=c_data.description,
                reference_text=c_data.reference_text,
                max_marks=c_data.max_marks,
                required=c_data.required,
                full_match_threshold=c_data.full_match_threshold,
                partial_match_threshold=c_data.partial_match_threshold,
                keywords=c_data.keywords,
                negative_indicators=c_data.negative_indicators,
                weight=c_data.weight
            )
            db.add(concept)

        db.commit()
        db.refresh(q)
        return q

    def validate_rubric(self, question_max_marks: float, concepts: List[RubricConceptCreate]) -> Dict[str, Any]:
        c_total = sum(c.max_marks for c in concepts)
        diff = round(question_max_marks - c_total, 2)
        is_valid = (diff == 0.0)
        msg = "✓ Rubric marks match question total." if is_valid else f"✗ Rubric total ({c_total}) does not equal question maximum ({question_max_marks}). Difference: {diff} marks."
        return {
            "is_valid": is_valid,
            "question_max_marks": question_max_marks,
            "concepts_total_marks": c_total,
            "difference": diff,
            "message": msg
        }

exam_service = ExamService()
