"""获客线索模型"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Lead(Base):
    """
    获客线索表
    
    用于存储从各渠道获取的潜在客户信息
    """
    __tablename__ = "ipl_leads"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 渠道来源
    # google: 谷歌, yahoo: 雅虎, tiktok: TikTok, facebook: Facebook, youtube: YouTube
    channel = Column(String(50), nullable=False, index=True, comment="渠道来源")
    
    # 获客方式
    # whatsapp: WhatsApp, email: 邮箱, competitor_fans: 竞品粉丝, 
    # comments: 评论数据, website: 网址, phone: 电话
    acquisition_type = Column(String(50), nullable=False, index=True, comment="获客方式")
    
    # 线索基本信息
    name = Column(String(200), comment="名称/昵称")
    contact = Column(String(500), comment="联系方式(邮箱/电话/WhatsApp等)")
    website = Column(String(500), comment="网址/主页链接")
    description = Column(Text, comment="描述/备注")
    
    # 来源详情
    source_url = Column(String(1000), comment="来源页面URL")
    source_keyword = Column(String(200), index=True, comment="搜索关键词")
    
    # 扩展数据 (JSON格式存储额外信息)
    extra_data = Column(Text, comment="扩展数据JSON")
    
    # 状态: 0-未处理, 1-已联系, 2-有意向, 3-已成交, 4-无效
    status = Column(Integer, default=0, index=True, comment="状态")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True, comment="最近更新时间")


# 渠道选项
CHANNEL_OPTIONS = [
    {"value": "google", "label": "谷歌"},
    {"value": "yahoo", "label": "雅虎"},
    {"value": "tiktok", "label": "TikTok"},
    {"value": "facebook", "label": "Facebook"},
    {"value": "youtube", "label": "YouTube"},
]

# 获客方式选项
ACQUISITION_TYPE_OPTIONS = [
    {"value": "whatsapp", "label": "WhatsApp"},
    {"value": "email", "label": "邮箱"},
    {"value": "competitor_fans", "label": "竞品粉丝"},
    {"value": "comments", "label": "评论数据"},
    {"value": "website", "label": "网址"},
    {"value": "phone", "label": "电话"},
]

# 状态选项
STATUS_OPTIONS = [
    {"value": 0, "label": "未处理"},
    {"value": 1, "label": "已联系"},
    {"value": 2, "label": "有意向"},
    {"value": 3, "label": "已成交"},
    {"value": 4, "label": "无效"},
]
