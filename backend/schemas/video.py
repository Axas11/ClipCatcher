from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VideoBase(BaseModel):
    title: str

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    file_path: str
    user_id: int
    duration: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class VideoUploadResponse(BaseModel):
    video_id: int
    message: str
    tokens_consumed: int