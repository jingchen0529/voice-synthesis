from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "ipl_api_keys"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("ipl_users.id", ondelete="CASCADE"), nullable=False, index=True)
    access_key = Column(String(64), unique=True, nullable=False, index=True)
    secret_key = Column(String(128), nullable=False)
    name = Column(String(100))
    status = Column(Integer, default=1)  # 0-禁用 1-正常
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="api_keys")
