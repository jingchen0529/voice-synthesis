from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TtsTask(Base):
    __tablename__ = "ipl_tts_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    celery_task_id = Column(String(64), index=True)  # Celery 任务 ID
    user_id = Column(BigInteger, ForeignKey("ipl_users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    language = Column(String(10), default="zh")
    speaker_audio_url = Column(String(500))
    output_audio_url = Column(String(500))
    status = Column(Integer, default=0)  # 0-待处理 1-处理中 2-完成 3-失败
    error_message = Column(Text)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tts_tasks")
