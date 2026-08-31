from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, AuditLog, AnswerSheet
from app.schemas.schemas import AuditLogResponse, IntegrityVerificationResponse
from app.services.integrity_service import integrity_service

router = APIRouter(prefix="/audit", tags=["Tamper Resistance & Audit Trail"])

@router.get("/logs/{session_id}", response_model=List[AuditLogResponse])
def get_audit_logs(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).filter(
        (AuditLog.session_id == session_id) | (AuditLog.session_id == None)
    ).order_by(AuditLog.timestamp.desc()).all()
    for l in logs:
        if l.user:
            l.user_name = l.user.full_name
    return logs

@router.get("/verify-integrity/{session_id}", response_model=IntegrityVerificationResponse)
def verify_session_integrity(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return integrity_service.verify_session_integrity(db, session_id)

@router.post("/simulate-tamper/{sheet_id}")
def simulate_tamper(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Simulation tool for demonstrating tamper detection:
    Backs up the clean file, then appends alteration bytes to the stored file to verify that the cryptographic integrity scanner immediately catches it.
    """
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet or not sheet.storage_path:
        raise HTTPException(status_code=404, detail="Answer sheet file not found")
    
    p = Path(sheet.storage_path)
    bak = Path(str(sheet.storage_path) + ".bak")
    if p.exists():
        if not bak.exists():
            import shutil
            shutil.copy2(p, bak)
        with open(p, "ab") as f:
            f.write(b" TAMPER_TEST_ALTERATION ")
        return {"message": "Tampering simulated: file modified on disk. Run integrity check to detect!", "sheet_id": sheet.id}
    raise HTTPException(status_code=404, detail="Disk file missing")

@router.post("/restore-tamper/{sheet_id}")
def restore_tamper(sheet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Restores the clean original file from backup after running tamper simulation test.
    """
    sheet = db.query(AnswerSheet).filter(AnswerSheet.id == sheet_id).first()
    if not sheet or not sheet.storage_path:
        raise HTTPException(status_code=404, detail="Answer sheet file not found")
    
    p = Path(sheet.storage_path)
    bak = Path(str(sheet.storage_path) + ".bak")
    if bak.exists():
        import shutil
        shutil.copy2(bak, p)
        return {"message": "Original file restored from backup. Cryptographic checksum matches again.", "sheet_id": sheet.id}
    return {"message": "No backup found or file is already original.", "sheet_id": sheet.id}

