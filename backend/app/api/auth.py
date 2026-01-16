from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.aksk import generate_ak_sk
from app.models import User, ApiKey
from app.services.quota_service import init_user_quotas, get_user_quotas

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    nickname: str = None


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateApiKeyRequest(BaseModel):
    name: str = None


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname or req.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 初始化配额（每个服务3次免费）
    init_user_quotas(db, user.id, free_quota=3)
    
    return {"message": "注册成功", "user_id": user.id}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname
        }
    }


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    quotas = get_user_quotas(db, user.id)
    
    # 计算总剩余次数
    total_remaining = sum(q.get('total', 0) for q in quotas) if quotas else 0
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "quotas": quotas,
        "remaining_uses": total_remaining
    }


@router.get("/api-key")
def get_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的 API 密钥"""
    key = db.query(ApiKey).filter(ApiKey.user_id == user.id).first()
    
    if not key:
        return None
    
    return {
        "id": key.id,
        "access_key": key.access_key,
        "status": key.status,
        "created_at": key.created_at
    }


@router.post("/api-key")
def create_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建 API 密钥（每个用户只能有一个）"""
    existing = db.query(ApiKey).filter(ApiKey.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="您已拥有 API 密钥")
    
    ak, sk = generate_ak_sk()
    api_key = ApiKey(user_id=user.id, access_key=ak, secret_key=sk)
    db.add(api_key)
    db.commit()
    
    return {
        "access_key": ak,
        "secret_key": sk,
        "message": "请妥善保存 Secret Key，它只会显示一次"
    }


@router.put("/api-key")
def regenerate_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """重新生成 Secret Key"""
    key = db.query(ApiKey).filter(ApiKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="您还没有 API 密钥")
    
    _, new_sk = generate_ak_sk()
    key.secret_key = new_sk
    db.commit()
    
    return {
        "access_key": key.access_key,
        "secret_key": new_sk,
        "message": "Secret Key 已重新生成"
    }
