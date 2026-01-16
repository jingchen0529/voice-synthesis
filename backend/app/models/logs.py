from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class QuotaLog(Base):
    __tablename__ = "ipl_quota_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("ipl_users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(BigInteger, ForeignKey("ipl_services.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64))
    quota_type = Column(Enum("free", "paid"), nullable=False)
    amount = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class ApiLog(Base):
    __tablename__ = "ipl_api_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    api_key_id = Column(BigInteger, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(Integer)
    request_body = Column(Text)
    response_time_ms = Column(Integer)
    ip = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
