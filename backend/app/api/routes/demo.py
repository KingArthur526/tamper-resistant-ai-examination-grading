from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User
import seed_demo

router = APIRouter(prefix="/demo", tags=["Demo Seed"])

@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam_id = seed_demo.seed_complete_demo(db, user_id=current_user.id)
    return {"message": "Demo examination and realistic student answer sheets seeded and evaluated successfully!", "exam_id": exam_id}
