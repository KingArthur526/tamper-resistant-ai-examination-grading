from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import AnswerSheet, AuditLog, ExamSession
from app.core.integrity import calculate_sha256_file, GENESIS_HASH

class IntegrityService:
    def verify_session_integrity(self, db: Session, session_id: str) -> Dict[str, Any]:
        answer_sheets = db.query(AnswerSheet).filter(AnswerSheet.session_id == session_id).all()
        
        files_checked = 0
        files_valid = 0
        files_tampered = 0
        tampered_details = []

        for sheet in answer_sheets:
            if sheet.storage_path:
                files_checked += 1
                p = Path(sheet.storage_path)
                if p.exists():
                    current_hash = calculate_sha256_file(p)
                    if current_hash == sheet.sha256_hash:
                        files_valid += 1
                    else:
                        files_tampered += 1
                        tampered_details.append({
                            "sheet_id": sheet.id,
                            "student_id": sheet.student_id,
                            "file_type": "original",
                            "expected_hash": sheet.sha256_hash,
                            "actual_hash": current_hash,
                            "status": "TAMPERED"
                        })
                else:
                    files_tampered += 1
                    tampered_details.append({
                        "sheet_id": sheet.id,
                        "student_id": sheet.student_id,
                        "file_type": "original",
                        "status": "FILE_MISSING"
                    })

            if sheet.preprocessed_path and sheet.preprocessed_hash:
                files_checked += 1
                p_prep = Path(sheet.preprocessed_path)
                if p_prep.exists():
                    curr_prep_hash = calculate_sha256_file(p_prep)
                    if curr_prep_hash == sheet.preprocessed_hash:
                        files_valid += 1
                    else:
                        files_tampered += 1
                        tampered_details.append({
                            "sheet_id": sheet.id,
                            "student_id": sheet.student_id,
                            "file_type": "preprocessed",
                            "expected_hash": sheet.preprocessed_hash,
                            "actual_hash": curr_prep_hash,
                            "status": "TAMPERED"
                        })

        # Check Audit Log Chain for this session
        session_events = db.query(AuditLog).filter(
            AuditLog.session_id == session_id
        ).order_by(AuditLog.timestamp.asc()).all()

        chain_valid = True
        broken_indices = []
        if session_events:
            prev_h = session_events[0].previous_hash
            for idx, event in enumerate(session_events):
                if idx > 0 and event.previous_hash != prev_h:
                    chain_valid = False
                    broken_indices.append(idx)
                prev_h = event.event_hash
        else:
            chain_valid = True

        overall_status = "VERIFIED" if (files_tampered == 0 and chain_valid) else "COMPROMISED"

        return {
            "session_id": session_id,
            "overall_status": overall_status,
            "total_files_checked": files_checked,
            "files_valid": files_valid,
            "files_tampered": files_tampered,
            "tampered_files_detail": tampered_details,
            "total_audit_events": len(session_events),
            "audit_chain_valid": chain_valid,
            "broken_chain_indices": broken_indices,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

integrity_service = IntegrityService()
