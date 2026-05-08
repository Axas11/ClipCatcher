from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from backend.database import Base

class Clip(Base):
    __tablename__ = "clips"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    video_id = Column(Integer, ForeignKey("videos.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(Integer)  # in seconds
    end_time = Column(Integer)  # in seconds
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())