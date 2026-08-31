from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog
from app.core.integrity import calculate_event_hash, GENESIS_HASH

def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Creates an immutable audit event chained to the previous event hash for this session ledger.
    """
    now = datetime.now(timezone.utc)
    ts_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    query = db.query(AuditLog)
    if session_id:
        query = query.filter(AuditLog.session_id == session_id)
    
    last_event = query.order_by(AuditLog.timestamp.desc()).first()
    prev_hash = last_event.event_hash if last_event else GENESIS_HASH

    event_hash = calculate_event_hash(
        previous_hash=prev_hash,
        timestamp=ts_str,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {}
    )

    audit_entry = AuditLog(
        session_id=session_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {},
        previous_hash=prev_hash,
        event_hash=event_hash,
        timestamp=now
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
