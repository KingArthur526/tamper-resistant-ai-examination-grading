from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import (
    User, AnswerSheet, QuestionEvaluation, ConceptEvaluation,
    StudentAnswer, Question, EvaluationConfig, ExamSession
)
from app.schemas.schemas import (
    QuestionEvaluationResponse, ConceptEvaluationResponse,
    WhyThisScoreResponse, StudentResultCard
)
from app.services.grading_service import grading_service
from app.ml.explainability.explainer import explainer

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Results"])

@router.post("/run/{sheet_id}")
def evaluate_sheet(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = grading_service.evaluate_answer_sheet(db, sheet_id, user_id=current_user.id)
    return res

@router.post("/run-exam/{exam_id}")
def evaluate_exam(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = grading_service.evaluate_entire_session(db, exam_id, user_id=current_user.id)
    return res

@router.get("/student-results/{sheet_id}", response_model=StudentResultCard)
def get_student_results(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Answer sheet not found")

    exam = sheet.session
    q_evals = db.query(QuestionEvaluation).filter(QuestionEvaluation.answer_sheet_id == sheet.id).all()

    q_resp_list = []
    tot_ai = 0.0
    tot_teacher = 0.0
    tot_max = 0.0

    for qe in q_evals:
        q = qe.question
        # Find student answer text
        sa = db.query(StudentAnswer).filter(
            StudentAnswer.answer_sheet_id == sheet.id,
            StudentAnswer.question_id == qe.question_id
        ).first()

        student_txt = sa.cleaned_text if sa else ""
        ocr_conf = sa.ocr_confidence if sa else 0.90

        # Concepts
        c_evals = db.query(ConceptEvaluation).filter(
            ConceptEvaluation.student_answer_id == (sa.id if sa else qe.id)
        ).all()

        c_resp_list = []
        for ce in c_evals:
            rc = ce.rubric_concept
            c_resp_list.append(ConceptEvaluationResponse(
                id=ce.id,
                rubric_concept_id=ce.rubric_concept_id,
                concept_code=rc.concept_code if rc else "C",
                concept_name=rc.name if rc else "Concept",
                concept_description=rc.description if rc else None,
                reference_text=rc.reference_text if rc else "",
                similarity_score=ce.similarity_score,
                semantic_status=ce.semantic_status,
                awarded_marks=ce.awarded_marks,
                max_marks=ce.max_marks,
                matched_evidence=ce.matched_evidence,
                matched_span_indices=ce.matched_span_indices or [],
                missing_evidence=ce.missing_evidence or [],
                explanation=ce.explanation,
                confidence_score=ce.confidence_score,
                model_name=ce.model_name,
                scoring_policy=ce.scoring_policy
            ))

        if qe.is_or_group_selected:
            tot_ai += qe.ai_score
            tot_teacher += qe.teacher_final_score
            tot_max += (q.max_marks if q else 0.0)

        q_resp_list.append(QuestionEvaluationResponse(
            id=qe.id,
            answer_sheet_id=sheet.id,
            question_id=qe.question_id,
            question_number=q.question_number if q else "-",
            question_text=q.question_text if q else "-",
            max_marks=q.max_marks if q else 0.0,
            student_answer_text=student_txt,
            ocr_confidence=ocr_conf,
            ai_score=qe.ai_score,
            teacher_final_score=qe.teacher_final_score,
            is_overridden=qe.is_overridden,
            confidence_level=qe.confidence_level,
            needs_review=qe.needs_review,
            review_reasons=qe.review_reasons or [],
            calculation_trace=qe.calculation_trace or {},
            is_or_group_selected=qe.is_or_group_selected,
            spelling_score=getattr(qe, "spelling_score", 100.0) or 100.0,
            spelling_penalty_deducted=getattr(qe, "spelling_penalty_deducted", 0.0) or 0.0,
            spelling_errors=getattr(qe, "spelling_errors", []) or [],
            status=qe.status,
            concept_evaluations=c_resp_list
        ))

    pct = (tot_teacher / tot_max * 100.0) if tot_max > 0 else 0.0
    needs_rev = any(qe.needs_review for qe in q_evals)

    return StudentResultCard(
        answer_sheet_id=sheet.id,
        student_id=sheet.student_id,
        student_name=sheet.student_name,
        roll_number=sheet.roll_number,
        session_id=exam.id if exam else "",
        session_name=exam.name if exam else "",
        subject=exam.subject if exam else "",
        total_ai_score=round(tot_ai, 2),
        total_teacher_score=round(tot_teacher, 2),
        total_max_marks=round(tot_max, 2),
        percentage=round(pct, 1),
        integrity_hash=sheet.sha256_hash,
        status=sheet.processing_status,
        needs_review=needs_rev,
        is_finalized=(exam.status == "FINALIZED" if exam else False),
        questions=q_resp_list
    )

@router.get("/why-this-score/{question_evaluation_id}", response_model=WhyThisScoreResponse)
def get_why_this_score(question_evaluation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    qe = db.query(QuestionEvaluation).filter(QuestionEvaluation.id == question_evaluation_id).first()
    if not qe:
        raise HTTPException(status_code=404, detail="Question evaluation not found")

    q = qe.question
    sheet = qe.answer_sheet
    cfg = db.query(EvaluationConfig).filter(EvaluationConfig.session_id == sheet.session_id).first()

    sa = db.query(StudentAnswer).filter(
        StudentAnswer.answer_sheet_id == sheet.id,
        StudentAnswer.question_id == qe.question_id
    ).first()

    c_evals = db.query(ConceptEvaluation).filter(
        ConceptEvaluation.student_answer_id == (sa.id if sa else qe.id)
    ).all()

    concepts_data = []
    for ce in c_evals:
        rc = ce.rubric_concept
        concepts_data.append({
            "id": ce.id,
            "rubric_concept_id": ce.rubric_concept_id,
            "concept_code": rc.concept_code if rc else "C",
            "concept_name": rc.name if rc else "Concept",
            "concept_description": rc.description if rc else None,
            "reference_text": rc.reference_text if rc else "",
            "similarity_score": ce.similarity_score,
            "semantic_status": ce.semantic_status,
            "awarded_marks": ce.awarded_marks,
            "max_marks": ce.max_marks,
            "matched_evidence": ce.matched_evidence,
            "matched_span_indices": ce.matched_span_indices or [],
            "missing_evidence": ce.missing_evidence or [],
            "explanation": ce.explanation,
            "confidence_score": ce.confidence_score,
            "model_name": ce.model_name,
            "scoring_policy": ce.scoring_policy
        })

    model_name = cfg.model_name if cfg else "all-MiniLM-L6-v2"
    sim_metric = cfg.similarity_metric if cfg else "Cosine Similarity"
    policy = cfg.scoring_policy_version if cfg else "v1.0-deterministic"
    ocr_conf = sa.ocr_confidence if sa else 0.95

    return explainer.assemble_why_this_score(
        question_evaluation=qe,
        concepts_data=concepts_data,
        semantic_model=model_name,
        similarity_method=sim_metric,
        scoring_policy=policy,
        ocr_confidence=ocr_conf
    )

@router.get("/needs-review-queue/{exam_id}")
def get_needs_review_queue(exam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == exam_id).all()
    queue = []
    for s in sheets:
        q_evals = db.query(QuestionEvaluation).filter(
            QuestionEvaluation.answer_sheet_id == s.id,
            QuestionEvaluation.needs_review == True
        ).all()
        for qe in q_evals:
            q = qe.question
            queue.append({
                "answer_sheet_id": s.id,
                "student_id": s.student_id,
                "student_name": s.student_name,
                "question_evaluation_id": qe.id,
                "question_number": q.question_number if q else "-",
                "question_text": q.question_text if q else "-",
                "ai_score": qe.ai_score,
                "teacher_score": qe.teacher_final_score,
                "confidence_level": qe.confidence_level,
                "review_reasons": qe.review_reasons or []
            })
    return queue
