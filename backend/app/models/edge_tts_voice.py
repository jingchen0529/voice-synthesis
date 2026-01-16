"""Edge TTS 音色模型"""
from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class EdgeTtsVoice(Base):
    """Edge TTS 音色表"""
    __tablename__ = "ipl_tts_voices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(100), unique=True, nullable=False, comment="音色短名称")
    name = Column(String(200), nullable=False, comment="完整名称")
    locale = Column(String(20), nullable=False, comment="语言区域")
    locale_name = Column(String(100), comment="语言区域名称")
    language = Column(String(50), nullable=False, comment="语言名称")
    gender = Column(String(20), nullable=False, comment="性别")
    display_name = Column(String(100), comment="显示名称")
    voice_type = Column(String(50), comment="音色类型")
    status = Column(Integer, default=1, comment="状态：1启用 0禁用")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
