from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import (
    ExamSession, AnswerSheet, Question, StudentAnswer,
    ConceptEvaluation, QuestionEvaluation, EvaluationConfig, QuestionGroup
)
from app.ml.grading.scoring_engine import scoring_engine
from app.ml.explainability.explainer import explainer
from app.core.integrity import calculate_sha256_text
from app.services.audit_service import log_audit_event

class GradingService:
    def evaluate_answer_sheet(self, db: Session, answer_sheet_id: str, user_id: str = None) -> Dict[str, Any]:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="Answer sheet not found")

        sheet.processing_status = "EVALUATING"
        db.commit()

        # Load session configuration
        cfg = db.query(EvaluationConfig).filter(EvaluationConfig.session_id == sheet.session_id).first()
        full_thresh = cfg.full_match_threshold if cfg else 0.78
        part_thresh = cfg.partial_match_threshold if cfg else 0.52
        or_policy = cfg.or_selection_policy if cfg else "best_attempted"

        questions = db.query(Question).filter(Question.session_id == sheet.session_id).order_by(Question.question_number).all()
        q_groups = db.query(QuestionGroup).filter(QuestionGroup.session_id == sheet.session_id).all()

        # Clear existing evaluations if re-evaluating
        db.query(QuestionEvaluation).filter(QuestionEvaluation.answer_sheet_id == sheet.id).delete()

        enable_spelling = getattr(cfg, "enable_spelling_evaluation", True) if cfg else True
        spelling_deduction = getattr(cfg, "spelling_deduction_per_error", 0.25) if cfg else 0.25
        spelling_max_penalty = getattr(cfg, "spelling_max_penalty", 1.0) if cfg else 1.0

        evaluated_questions = []

        for q in questions:
            student_ans = db.query(StudentAnswer).filter(
                StudentAnswer.answer_sheet_id == sheet.id,
                StudentAnswer.question_id == q.id
            ).first()

            if student_ans:
                db.query(ConceptEvaluation).filter(ConceptEvaluation.student_answer_id == student_ans.id).delete()
                db.commit()

            text_to_grade = student_ans.cleaned_text if student_ans else ""
            ocr_conf = student_ans.ocr_confidence if student_ans else 0.90

            # Run deterministic scoring engine
            q_eval_res = scoring_engine.evaluate_question(
                question=q,
                student_text=text_to_grade,
                ocr_confidence=ocr_conf,
                full_match_threshold=full_thresh,
                partial_match_threshold=part_thresh,
                enable_spelling=enable_spelling,
                spelling_deduction_per_error=spelling_deduction,
                spelling_max_penalty=spelling_max_penalty
            )

            # Create QuestionEvaluation record
            q_eval = QuestionEvaluation(
                answer_sheet_id=sheet.id,
                question_id=q.id,
                ai_score=q_eval_res["ai_score"],
                teacher_final_score=q_eval_res["teacher_final_score"],
                is_overridden=False,
                confidence_level=q_eval_res["confidence_level"],
                needs_review=q_eval_res["needs_review"],
                review_reasons=q_eval_res["review_reasons"],
                calculation_trace=q_eval_res["calculation_trace"],
                is_or_group_selected=True,
                spelling_score=q_eval_res.get("spelling_score", 100.0),
                spelling_penalty_deducted=q_eval_res.get("spelling_penalty_deducted", 0.0),
                spelling_errors=q_eval_res.get("spelling_errors", []),
                status="EVALUATED",
                evaluated_at=datetime.now(timezone.utc)
            )
            db.add(q_eval)
            db.commit()
            db.refresh(q_eval)

            # Persist concept evaluations
            for c_res in q_eval_res["concept_evaluations"]:
                # Generate grounded explanation
                expl = explainer.generate_concept_explanation(c_res)
                c_res["explanation"] = expl

                c_eval = ConceptEvaluation(
                    student_answer_id=student_ans.id if student_ans else q_eval.id,
                    rubric_concept_id=c_res["rubric_concept_id"],
                    similarity_score=c_res["similarity_score"],
                    semantic_status=c_res["semantic_status"],
                    awarded_marks=c_res["awarded_marks"],
                    max_marks=c_res["max_marks"],
                    matched_evidence=c_res["matched_evidence"],
                    matched_span_indices=c_res["matched_span_indices"],
                    missing_evidence=c_res["missing_evidence"],
                    explanation=expl,
                    confidence_score=c_res["confidence_score"],
                    model_name=c_res["model_name"],
                    scoring_policy=c_res["scoring_policy"],
                    evaluated_at=datetime.now(timezone.utc)
                )
                db.add(c_eval)

            # Compute evaluation snapshot hash
            eval_hash_content = f"{sheet.id}|{q.id}|{q_eval_res['ai_score']}|{q_eval_res['calculation_trace']}"
            q_eval.evaluation_hash = calculate_sha256_text(eval_hash_content)
            db.commit()
            db.refresh(q_eval)

            q_eval_res["id"] = q_eval.id
            q_eval_res["question"] = q
            evaluated_questions.append(q_eval_res)

        # Apply OR-question selection logic
        scoring_engine.resolve_or_question_groups(evaluated_questions, q_groups, policy=or_policy)

        # Sync OR-selection flags to database
        for eq in evaluated_questions:
            db_qe = db.query(QuestionEvaluation).filter(QuestionEvaluation.id == eq["id"]).first()
            if db_qe:
                db_qe.is_or_group_selected = eq.get("is_or_group_selected", True)
        db.commit()

        sheet.processing_status = "EVALUATED"
        db.commit()
        db.refresh(sheet)

        log_audit_event(
            db=db,
            action="EVALUATION_COMPLETED",
            entity_type="AnswerSheet",
            entity_id=sheet.id,
            session_id=sheet.session_id,
            user_id=user_id,
            payload={"student_id": sheet.student_id, "questions_count": len(evaluated_questions)}
        )

        return {"answer_sheet_id": sheet.id, "status": "EVALUATED", "questions_evaluated": len(evaluated_questions)}

    def evaluate_entire_session(self, db: Session, session_id: str, user_id: str = None) -> Dict[str, Any]:
        sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == session_id).all()
        results = []
        for sheet in sheets:
            res = self.evaluate_answer_sheet(db, sheet.id, user_id=user_id)
            results.append(res)
        
        exam = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if exam:
            exam.status = "COMPLETED"
            db.commit()

        return {"session_id": session_id, "evaluated_total": len(results)}

grading_service = GradingService()
