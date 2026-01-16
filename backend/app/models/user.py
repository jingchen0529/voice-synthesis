from sqlalchemy import Column, BigInteger, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "ipl_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100))
    username = Column(String(100))
    avatar = Column(String(500))
    status = Column(Integer, default=1)  # 0-禁用 1-正常
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    tts_tasks = relationship("TtsTask", back_populates="user", cascade="all, delete-orphan")
    video_tasks = relationship("VideoTask", back_populates="user", cascade="all, delete-orphan")
    service_quotas = relationship("UserServiceQuota", back_populates="user", cascade="all, delete-orphan")
