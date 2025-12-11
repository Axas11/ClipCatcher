from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClipBase(BaseModel):
    title: str

class ClipCreate(ClipBase):
    video_id: int
    start_time: int
    end_time: int

class Clip(ClipBase):
    id: int
    file_path: str
    video_id: int
    user_id: int
    start_time: int
    end_time: int
    views: int
    likes: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClipWithUser(BaseModel):
    id: int
    title: str
    file_path: str
    user_id: int
    username: str
    views: int
    likes: int
    created_at: datetime
    
    class Config:
        from_attributes = True