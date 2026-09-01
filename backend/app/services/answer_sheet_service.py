import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models.models import AnswerSheet, ExamSession
from app.core.config import settings
from app.core.integrity import calculate_sha256_bytes, calculate_sha256_file
from app.services.audit_service import log_audit_event

class AnswerSheetService:
    async def upload_answer_sheet(
        self,
        db: Session,
        session_id: str,
        file: UploadFile,
        student_id: str,
        student_name: str,
        roll_number: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AnswerSheet:
        exam = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam session not found")

        content = await file.read()
        sha256 = calculate_sha256_bytes(content)
        file_size = len(content)

        # Save immutable original file
        ext = Path(file.filename).suffix.lower()
        storage_filename = f"{sha256[:16]}_{student_id}{ext}"
        storage_path = settings.ORIGINAL_PATH / storage_filename

        with open(storage_path, "wb") as f:
            f.write(content)

        sheet = AnswerSheet(
            session_id=session_id,
            student_id=student_id,
            student_name=student_name,
            roll_number=roll_number or student_id,
            original_filename=file.filename,
            storage_path=str(storage_path),
            sha256_hash=sha256,
            file_size_bytes=file_size,
            processing_status="UPLOADED"
        )
        db.add(sheet)
        db.commit()
        db.refresh(sheet)

        log_audit_event(
            db=db,
            action="ANSWER_SHEET_UPLOADED",
            entity_type="AnswerSheet",
            entity_id=sheet.id,
            session_id=session_id,
            user_id=user_id,
            payload={
                "student_id": student_id,
                "filename": file.filename,
                "sha256": sha256,
                "size_bytes": file_size
            }
        )

        # Automatically run OCR and semantic evaluation on the uploaded script
        try:
            from app.services.ocr_service import ocr_service
            sheet = ocr_service.process_answer_sheet_ocr(db, sheet.id, user_id=user_id)
        except Exception as ocr_err:
            print(f"[AnswerSheetService] Auto-OCR on upload note: {ocr_err}")

        return sheet

answer_sheet_service = AnswerSheetService()
