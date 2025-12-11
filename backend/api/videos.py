from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.video import Video as VideoModel
from backend.models.user import User as UserModel
from backend.schemas.video import VideoCreate, VideoUploadResponse
from backend.dependencies import get_current_user
import os

router = APIRouter(prefix="/videos", tags=["videos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=VideoUploadResponse)
def upload_video(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user has enough tokens
    if current_user.tokens < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough tokens to process this video"
        )
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Calculate tokens needed (simplified)
    # In a real implementation, this would be based on video duration
    tokens_consumed = min(100, max(10, len(content) // (1024 * 1024)))  # Simplified calculation
    
    if current_user.tokens < tokens_consumed:
        # Clean up uploaded file
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail="Not enough tokens to process this video"
        )
    
    # Create video record
    db_video = VideoModel(
        title=file.filename,
        file_path=file_path,
        user_id=current_user.id,
        duration=0,  # Would be determined by processing
        status="processing"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # Deduct tokens
    current_user.tokens -= tokens_consumed
    db.commit()
    
    # In a real implementation, this would trigger the video processing script
    # For now, we'll just simulate it
    
    return VideoUploadResponse(
        video_id=db_video.id,
        message="Video uploaded successfully. Processing started.",
        tokens_consumed=tokens_consumed
    )