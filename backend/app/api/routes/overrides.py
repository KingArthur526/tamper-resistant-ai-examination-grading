from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, TeacherOverride
from app.schemas.schemas import TeacherOverrideRequest, TeacherOverrideResponse
from app.services.override_service import override_service

router = APIRouter(prefix="/overrides", tags=["Teacher Overrides"])

@router.post("/{question_evaluation_id}", response_model=TeacherOverrideResponse)
def apply_override(
    question_evaluation_id: str,
    data: TeacherOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    override = override_service.apply_teacher_override(
        db=db,
        question_evaluation_id=question_evaluation_id,
        new_score=data.new_score,
        reason=data.override_reason,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name
    )
    return override
