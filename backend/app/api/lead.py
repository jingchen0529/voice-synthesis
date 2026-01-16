"""获客线索 API"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.lead import Lead, CHANNEL_OPTIONS, ACQUISITION_TYPE_OPTIONS, STATUS_OPTIONS

router = APIRouter()


# ============ 请求/响应模型 ============

class LeadCreate(BaseModel):
    """创建线索"""
    channel: str = Field(..., description="渠道来源")
    acquisition_type: str = Field(..., description="获客方式")
    name: Optional[str] = None
    contact: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    source_keyword: Optional[str] = None
    extra_data: Optional[str] = None
    status: int = 0


class LeadUpdate(BaseModel):
    """更新线索"""
    name: Optional[str] = None
    contact: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None


class LeadResponse(BaseModel):
    """线索响应"""
    id: int
    channel: str
    channel_label: str
    acquisition_type: str
    acquisition_type_label: str
    name: Optional[str]
    contact: Optional[str]
    website: Optional[str]
    description: Optional[str]
    source_url: Optional[str]
    source_keyword: Optional[str]
    status: int
    status_label: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """线索列表响应"""
    total: int
    page: int
    page_size: int
    items: List[LeadResponse]


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int]


# ============ 辅助函数 ============

def get_label(options: list, value: str) -> str:
    """获取选项标签"""
    for opt in options:
        if opt["value"] == value:
            return opt["label"]
    return value


def lead_to_response(lead: Lead) -> dict:
    """转换为响应格式"""
    return {
        "id": lead.id,
        "channel": lead.channel,
        "channel_label": get_label(CHANNEL_OPTIONS, lead.channel),
        "acquisition_type": lead.acquisition_type,
        "acquisition_type_label": get_label(ACQUISITION_TYPE_OPTIONS, lead.acquisition_type),
        "name": lead.name,
        "contact": lead.contact,
        "website": lead.website,
        "description": lead.description,
        "source_url": lead.source_url,
        "source_keyword": lead.source_keyword,
        "status": lead.status,
        "status_label": get_label(STATUS_OPTIONS, lead.status),
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


# ============ API 路由 ============

@router.get("/options")
def get_options():
    """获取筛选选项"""
    return {
        "channels": CHANNEL_OPTIONS,
        "acquisition_types": ACQUISITION_TYPE_OPTIONS,
        "statuses": STATUS_OPTIONS,
    }


@router.get("/list")
def get_lead_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    channel: Optional[str] = None,
    acquisition_type: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[int] = None,
    created_start: Optional[datetime] = None,
    created_end: Optional[datetime] = None,
    updated_start: Optional[datetime] = None,
    updated_end: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取线索列表
    
    支持筛选条件：
    - channel: 渠道
    - acquisition_type: 获客方式
    - keyword: 关键词搜索（匹配名称、联系方式、描述、来源关键词）
    - status: 状态
    - created_start/created_end: 创建时间范围
    - updated_start/updated_end: 更新时间范围
    """
    query = db.query(Lead)
    
    # 渠道筛选
    if channel:
        query = query.filter(Lead.channel == channel)
    
    # 获客方式筛选
    if acquisition_type:
        query = query.filter(Lead.acquisition_type == acquisition_type)
    
    # 状态筛选
    if status is not None:
        query = query.filter(Lead.status == status)
    
    # 关键词搜索
    if keyword:
        keyword_filter = or_(
            Lead.name.like(f"%{keyword}%"),
            Lead.contact.like(f"%{keyword}%"),
            Lead.description.like(f"%{keyword}%"),
            Lead.source_keyword.like(f"%{keyword}%"),
            Lead.website.like(f"%{keyword}%"),
        )
        query = query.filter(keyword_filter)
    
    # 创建时间筛选
    if created_start:
        query = query.filter(Lead.created_at >= created_start)
    if created_end:
        query = query.filter(Lead.created_at <= created_end)
    
    # 更新时间筛选
    if updated_start:
        query = query.filter(Lead.updated_at >= updated_start)
    if updated_end:
        query = query.filter(Lead.updated_at <= updated_end)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    leads = query.order_by(Lead.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [lead_to_response(lead) for lead in leads]
    }


@router.get("/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """获取单条线索详情"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")
    return lead_to_response(lead)


@router.post("/create")
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    """创建线索"""
    # 验证渠道
    valid_channels = [opt["value"] for opt in CHANNEL_OPTIONS]
    if data.channel not in valid_channels:
        raise HTTPException(status_code=400, detail=f"无效的渠道: {data.channel}")
    
    # 验证获客方式
    valid_types = [opt["value"] for opt in ACQUISITION_TYPE_OPTIONS]
    if data.acquisition_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的获客方式: {data.acquisition_type}")
    
    lead = Lead(
        channel=data.channel,
        acquisition_type=data.acquisition_type,
        name=data.name,
        contact=data.contact,
        website=data.website,
        description=data.description,
        source_url=data.source_url,
        source_keyword=data.source_keyword,
        extra_data=data.extra_data,
        status=data.status,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    return lead_to_response(lead)


@router.put("/{lead_id}")
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    """更新线索"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")
    
    if data.name is not None:
        lead.name = data.name
    if data.contact is not None:
        lead.contact = data.contact
    if data.website is not None:
        lead.website = data.website
    if data.description is not None:
        lead.description = data.description
    if data.status is not None:
        lead.status = data.status
    
    db.commit()
    db.refresh(lead)
    
    return lead_to_response(lead)


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """删除线索"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")
    
    db.delete(lead)
    db.commit()
    
    return {"message": "删除成功"}


@router.post("/batch-delete")
def batch_delete_leads(data: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除线索"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的线索")
    
    deleted_count = db.query(Lead).filter(Lead.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    
    return {"message": f"成功删除 {deleted_count} 条线索", "deleted_count": deleted_count}


@router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """获取统计摘要"""
    from sqlalchemy import func
    
    total = db.query(Lead).count()
    
    # 按渠道统计
    channel_stats = db.query(
        Lead.channel, 
        func.count(Lead.id).label("count")
    ).group_by(Lead.channel).all()
    
    # 按获客方式统计
    type_stats = db.query(
        Lead.acquisition_type,
        func.count(Lead.id).label("count")
    ).group_by(Lead.acquisition_type).all()
    
    # 按状态统计
    status_stats = db.query(
        Lead.status,
        func.count(Lead.id).label("count")
    ).group_by(Lead.status).all()
    
    return {
        "total": total,
        "by_channel": {item[0]: item[1] for item in channel_stats},
        "by_type": {item[0]: item[1] for item in type_stats},
        "by_status": {item[0]: item[1] for item in status_stats},
    }
