from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, EvaluationConfig
from app.schemas.schemas import EvaluationConfigResponse, EvaluationConfigUpdate
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/settings", tags=["Model & Evaluation Settings"])

@router.get("/{session_id}", response_model=EvaluationConfigResponse)
def get_config(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cfg = db.query(EvaluationConfig).filter(EvaluationConfig.session_id == session_id).first()
    if not cfg:
        # Default config
        cfg = EvaluationConfig(session_id=session_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg

@router.put("/{session_id}", response_model=EvaluationConfigResponse)
def update_config(
    session_id: str,
    data: EvaluationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cfg = db.query(EvaluationConfig).filter(EvaluationConfig.session_id == session_id).first()
    if not cfg:
        cfg = EvaluationConfig(session_id=session_id)
        db.add(cfg)

    for k, v in data.dict(exclude_unset=True).items():
        if v is not None:
            setattr(cfg, k, v)

    db.commit()
    db.refresh(cfg)
    log_audit_event(db, "EVALUATION_CONFIG_UPDATED", "EvaluationConfig", cfg.id, session_id=session_id, user_id=current_user.id, payload=data.dict(exclude_unset=True))
    return cfg
