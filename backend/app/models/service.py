from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Service(Base):
    __tablename__ = "ipl_services"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(500))
    quota_per_call = Column(Integer, default=1)
    status = Column(Integer, default=1)  # 0-下线 1-正常 2-维护中
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user_quotas = relationship("UserServiceQuota", back_populates="service", cascade="all, delete-orphan")


class UserServiceQuota(Base):
    __tablename__ = "ipl_user_service_quotas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("ipl_users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(BigInteger, ForeignKey("ipl_services.id", ondelete="CASCADE"), nullable=False, index=True)
    free_quota = Column(Integer, default=0)
    paid_quota = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="service_quotas")
    service = relationship("Service", back_populates="user_quotas")
