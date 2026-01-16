from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User, Service, UserServiceQuota, QuotaLog


def check_and_deduct_quota(db: Session, user_id: int, service_code: str, task_id: str = None) -> str:
    """
    检查并扣除配额
    返回扣除的配额类型: 'free' 或 'paid'
    """
    # 获取服务
    service = db.query(Service).filter(Service.code == service_code, Service.status == 1).first()
    if not service:
        raise HTTPException(status_code=400, detail=f"服务 {service_code} 不可用")
    
    # 获取用户配额
    quota = db.query(UserServiceQuota).filter(
        UserServiceQuota.user_id == user_id,
        UserServiceQuota.service_id == service.id
    ).first()
    
    if not quota:
        raise HTTPException(status_code=403, detail="配额不足，请充值")
    
    amount = service.quota_per_call
    quota_type = None
    
    # 优先扣免费配额
    if quota.free_quota >= amount:
        quota.free_quota -= amount
        quota_type = "free"
    elif quota.paid_quota >= amount:
        quota.paid_quota -= amount
        quota_type = "paid"
    else:
        raise HTTPException(status_code=403, detail="配额不足，请充值")
    
    # 记录配额消耗
    log = QuotaLog(
        user_id=user_id,
        service_id=service.id,
        task_id=task_id,
        quota_type=quota_type,
        amount=amount
    )
    db.add(log)
    db.commit()
    
    return quota_type


def get_user_quotas(db: Session, user_id: int) -> list:
    """获取用户所有服务的配额"""
    quotas = db.query(UserServiceQuota, Service).join(
        Service, UserServiceQuota.service_id == Service.id
    ).filter(UserServiceQuota.user_id == user_id).all()
    
    return [
        {
            "service_code": service.code,
            "service_name": service.name,
            "free_quota": quota.free_quota,
            "paid_quota": quota.paid_quota,
            "total": quota.free_quota + quota.paid_quota
        }
        for quota, service in quotas
    ]


def init_user_quotas(db: Session, user_id: int, free_quota: int = 3):
    """为新用户初始化所有服务的配额"""
    services = db.query(Service).filter(Service.status == 1).all()
    
    for service in services:
        quota = UserServiceQuota(
            user_id=user_id,
            service_id=service.id,
            free_quota=free_quota,
            paid_quota=0
        )
        db.add(quota)
    
    db.commit()
