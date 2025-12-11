from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.clip import Clip as ClipModel
from backend.models.user import User as UserModel
from backend.schemas.clip import Clip, ClipWithUser
from backend.dependencies import get_current_user

router = APIRouter(prefix="/clips", tags=["clips"])

@router.get("/feed", response_model=list[ClipWithUser])
def get_clips_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    clips = db.query(
        ClipModel.id,
        ClipModel.title,
        ClipModel.file_path,
        ClipModel.user_id,
        UserModel.username,
        ClipModel.views,
        ClipModel.likes,
        ClipModel.created_at
    ).join(UserModel).order_by(ClipModel.likes.desc(), ClipModel.views.desc()).offset(skip).limit(limit).all()
    
    return [
        ClipWithUser(
            id=clip.id,
            title=clip.title,
            file_path=clip.file_path,
            user_id=clip.user_id,
            username=clip.username,
            views=clip.views,
            likes=clip.likes,
            created_at=clip.created_at
        ) for clip in clips
    ]

@router.get("/user/{user_id}", response_model=list[Clip])
def get_user_clips(user_id: int, db: Session = Depends(get_db)):
    clips = db.query(ClipModel).filter(ClipModel.user_id == user_id).order_by(ClipModel.created_at.desc()).all()
    return clips

@router.get("/my-clips", response_model=list[Clip])
def get_my_clips(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    clips = db.query(ClipModel).filter(ClipModel.user_id == current_user.id).order_by(ClipModel.created_at.desc()).all()
    return clips