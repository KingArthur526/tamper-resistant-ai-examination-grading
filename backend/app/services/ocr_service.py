from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import AnswerSheet, StudentAnswer, Question, ExamSession
from app.ml.ocr.preprocessor import preprocess_image
from app.ml.ocr.engine import ocr_engine
from app.ml.segmentation.parser import segmenter
from app.core.config import settings
from app.core.integrity import calculate_sha256_text
from app.services.audit_service import log_audit_event

class OCRService:
    def process_answer_sheet_ocr(self, db: Session, answer_sheet_id: str, user_id: str = None) -> AnswerSheet:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="Answer sheet not found")

        sheet.processing_status = "PREPROCESSING"
        db.commit()

        orig_path = Path(sheet.storage_path)
        ext = orig_path.suffix.lower()

        try:
            # 1. Image Preprocessing (for image formats or PDF page render)
            if ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                prep_filename = f"prep_{sheet.sha256_hash[:16]}_{sheet.student_id}.png"
                prep_path = settings.PREPROCESSED_PATH / prep_filename
                _, prep_hash = preprocess_image(orig_path, prep_path)
                sheet.preprocessed_path = str(prep_path)
                sheet.preprocessed_hash = prep_hash
            elif ext == ".pdf":
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(str(orig_path))
                    if len(doc) > 0:
                        page = doc[0]
                        pix = page.get_pixmap(dpi=150)
                        prep_filename = f"prep_{sheet.sha256_hash[:16]}_{sheet.student_id}.png"
                        prep_path = settings.PREPROCESSED_PATH / prep_filename
                        pix.save(str(prep_path))
                        sheet.preprocessed_path = str(prep_path)
                        from app.core.integrity import calculate_sha256_file
                        sheet.preprocessed_hash = calculate_sha256_file(prep_path)
                except Exception:
                    pass

            # 2. Run Text Extraction (supports PDF, TXT, MD, Images)
            ocr_res = ocr_engine.extract_text(orig_path)
            raw_text = ocr_res["raw_text"]
            conf_avg = ocr_res["confidence_avg"]
            sheet.ocr_confidence_avg = conf_avg
            sheet.ocr_hash = calculate_sha256_text(raw_text)

            # Save extracted transcript
            ocr_file = settings.OCR_PATH / f"ocr_{sheet.id}.txt"
            ocr_file.write_text(raw_text, encoding="utf-8")
            sheet.ocr_raw_path = str(ocr_file)

            # 3. Segment into Questions
            questions = db.query(Question).filter(Question.session_id == sheet.session_id).order_by(Question.question_number).all()
            q_numbers = [q.question_number for q in questions]
            segmented_dict = segmenter.segment_answers(raw_text, q_numbers)

            # Remove previous student answers if reprocessing
            db.query(StudentAnswer).filter(StudentAnswer.answer_sheet_id == sheet.id).delete()

            for q in questions:
                q_key = q.question_number.strip().lower()
                seg_info = segmented_dict.get(q_key, {"text": "", "confidence": conf_avg, "attempted": False})
                
                if not seg_info["text"]:
                    for k, v in segmented_dict.items():
                        if k in q_key or q_key in k:
                            seg_info = v
                            break

                s_answer = StudentAnswer(
                    answer_sheet_id=sheet.id,
                    question_id=q.id,
                    raw_ocr_text=seg_info["text"],
                    cleaned_text=seg_info["text"],
                    ocr_confidence=seg_info.get("confidence", conf_avg),
                    segmentation_confidence=0.95 if seg_info["text"] else 0.40,
                    attempted=bool(seg_info["text"].strip())
                )
                db.add(s_answer)

            # For digital documents (confidence >= 0.75), mark as completed
            sheet.processing_status = "OCR_COMPLETED" if conf_avg >= 0.75 else "NEEDS_OCR_REVIEW"
            db.commit()
            db.refresh(sheet)

            # Auto-trigger semantic grading on extracted answers
            try:
                from app.services.grading_service import grading_service
                grading_service.evaluate_answer_sheet(db, sheet.id, user_id=user_id)
            except Exception as eval_err:
                print(f"[OCRService] Auto-evaluation warning: {eval_err}")

            log_audit_event(
                db=db,
                action="DOCUMENT_TEXT_PROCESSED",
                entity_type="AnswerSheet",
                entity_id=sheet.id,
                session_id=sheet.session_id,
                user_id=user_id,
                payload={
                    "confidence_avg": conf_avg,
                    "doc_type": ocr_res.get("document_type", ext),
                    "status": sheet.processing_status
                }
            )
            return sheet

        except Exception as e:
            sheet.processing_status = "ERROR"
            sheet.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")

    def approve_ocr(self, db: Session, answer_sheet_id: str, user_id: str = None) -> AnswerSheet:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="Answer sheet not found")

        sheet.processing_status = "OCR_APPROVED"
        db.commit()
        db.refresh(sheet)

        # Auto-evaluate on approval
        try:
            from app.services.grading_service import grading_service
            grading_service.evaluate_answer_sheet(db, sheet.id, user_id=user_id)
        except Exception as eval_err:
            print(f"[OCRService] Approval evaluation warning: {eval_err}")

        log_audit_event(
            db=db,
            action="OCR_APPROVED",
            entity_type="AnswerSheet",
            entity_id=sheet.id,
            session_id=sheet.session_id,
            user_id=user_id,
            payload={"student_id": sheet.student_id}
        )
        return sheet

    def submit_corrections(
        self,
        db: Session,
        answer_sheet_id: str,
        corrections: List[Dict[str, Any]],
        user_id: str = None,
        re_evaluate: bool = True
    ) -> AnswerSheet:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="Answer sheet not found")

        reconstructed_lines = []
        for c in corrections:
            ans_id = c.get("student_answer_id")
            new_text = c.get("edited_text")
            if ans_id and new_text is not None:
                ans = db.query(StudentAnswer).filter(StudentAnswer.id == ans_id).first()
                if ans:
                    ans.teacher_edited_text = new_text
                    ans.cleaned_text = new_text
                    ans.attempted = bool(new_text.strip())
                    ans.is_edited = True
                    q_num = ans.question.question_number if ans.question else ""
                    reconstructed_lines.append(f"Question {q_num}:\n{new_text}")

        # Update raw transcript file on disk
        if reconstructed_lines and sheet.ocr_raw_path:
            full_text = "\n\n".join(reconstructed_lines)
            Path(sheet.ocr_raw_path).write_text(full_text, encoding="utf-8")
            sheet.ocr_hash = calculate_sha256_text(full_text)

        sheet.processing_status = "OCR_APPROVED"
        db.commit()
        db.refresh(sheet)

        log_audit_event(
            db=db,
            action="OCR_CORRECTIONS_APPLIED",
            entity_type="AnswerSheet",
            entity_id=sheet.id,
            session_id=sheet.session_id,
            user_id=user_id,
            payload={"corrections_count": len(corrections), "re_evaluated": re_evaluate}
        )

        if re_evaluate:
            from app.services.grading_service import grading_service
            grading_service.evaluate_answer_sheet(db, sheet.id, user_id=user_id)

        return sheet

    def update_entire_sheet_raw_text(
        self,
        db: Session,
        answer_sheet_id: str,
        entire_raw_text: str,
        user_id: str = None,
        re_evaluate: bool = True
    ) -> AnswerSheet:
        sheet = db.query(AnswerSheet).filter(AnswerSheet.id == answer_sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="Answer sheet not found")

        # Save to disk
        ocr_file = settings.OCR_PATH / f"ocr_{sheet.id}.txt"
        ocr_file.write_text(entire_raw_text, encoding="utf-8")
        sheet.ocr_raw_path = str(ocr_file)
        sheet.ocr_hash = calculate_sha256_text(entire_raw_text)

        # Re-segment
        questions = db.query(Question).filter(Question.session_id == sheet.session_id).order_by(Question.question_number).all()
        q_numbers = [q.question_number for q in questions]
        segmented_dict = segmenter.segment_answers(entire_raw_text, q_numbers)

        for q in questions:
            q_key = q.question_number.strip().lower()
            seg_info = segmented_dict.get(q_key, {"text": "", "confidence": 1.0, "attempted": False})
            
            if not seg_info["text"]:
                for k, v in segmented_dict.items():
                    if k in q_key or q_key in k:
                        seg_info = v
                        break

            ans = db.query(StudentAnswer).filter(
                StudentAnswer.answer_sheet_id == sheet.id,
                StudentAnswer.question_id == q.id
            ).first()

            if ans:
                ans.teacher_edited_text = seg_info["text"]
                ans.cleaned_text = seg_info["text"]
                ans.is_edited = True
                ans.attempted = bool(seg_info["text"].strip())
            else:
                ans = StudentAnswer(
                    answer_sheet_id=sheet.id,
                    question_id=q.id,
                    raw_ocr_text=seg_info["text"],
                    cleaned_text=seg_info["text"],
                    teacher_edited_text=seg_info["text"],
                    is_edited=True,
                    ocr_confidence=1.0,
                    segmentation_confidence=0.95,
                    attempted=bool(seg_info["text"].strip())
                )
                db.add(ans)

        sheet.processing_status = "OCR_APPROVED"
        sheet.ocr_confidence_avg = 1.0 # 100% verified by evaluator
        db.commit()
        db.refresh(sheet)

        log_audit_event(
            db=db,
            action="ENTIRE_SHEET_OCR_UPDATED",
            entity_type="AnswerSheet",
            entity_id=sheet.id,
            session_id=sheet.session_id,
            user_id=user_id,
            payload={"text_length": len(entire_raw_text), "re_evaluated": re_evaluate}
        )

        if re_evaluate:
            from app.services.grading_service import grading_service
            grading_service.evaluate_answer_sheet(db, sheet.id, user_id=user_id)

        return sheet

ocr_service = OCRService()

