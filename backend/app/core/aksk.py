import hmac
import hashlib
import secrets
import time
from typing import Optional, Tuple
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db


def generate_ak_sk() -> Tuple[str, str]:
    """生成AK/SK密钥对"""
    access_key = "AK" + secrets.token_hex(16).upper()
    secret_key = secrets.token_hex(32)
    return access_key, secret_key


def hash_secret_key(secret_key: str) -> str:
    """对SK进行哈希存储"""
    return hashlib.sha256(secret_key.encode()).hexdigest()


def create_signature(secret_key: str, method: str, path: str, timestamp: str, body: str = "") -> str:
    """
    创建请求签名
    签名算法: HMAC-SHA256(secret_key, method + path + timestamp + body_hash)
    """
    body_hash = hashlib.sha256(body.encode()).hexdigest() if body else ""
    string_to_sign = f"{method}\n{path}\n{timestamp}\n{body_hash}"
    signature = hmac.new(
        secret_key.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(secret_key: str, method: str, path: str, timestamp: str, signature: str, body: str = "") -> bool:
    """验证请求签名"""
    # 检查时间戳是否在5分钟内
    try:
        req_time = int(timestamp)
        now = int(time.time())
        if abs(now - req_time) > 300:  # 5分钟
            return False
    except ValueError:
        return False
    
    expected_signature = create_signature(secret_key, method, path, timestamp, body)
    return hmac.compare_digest(signature, expected_signature)


async def verify_aksk(request: Request, db: Session = Depends(get_db)):
    """
    验证AK/SK签名的依赖
    请求头需要包含:
    - X-Access-Key: AK
    - X-Timestamp: 时间戳
    - X-Signature: 签名
    """
    from app.models import ApiKey, User
    from datetime import datetime
    
    access_key = request.headers.get("X-Access-Key")
    timestamp = request.headers.get("X-Timestamp")
    signature = request.headers.get("X-Signature")
    
    if not all([access_key, timestamp, signature]):
        raise HTTPException(status_code=401, detail="缺少认证头信息")
    
    # 查找API密钥
    api_key = db.query(ApiKey).filter(
        ApiKey.access_key == access_key,
        ApiKey.status == 1
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="无效的Access Key")
    
    # 检查是否过期
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API密钥已过期")
    
    # 获取请求体
    body = ""
    if request.method in ["POST", "PUT", "PATCH"]:
        body = (await request.body()).decode()
    
    # 验证签名（注意：存储的是原始SK，不是哈希后的）
    if not verify_signature(
        api_key.secret_key,
        request.method,
        request.url.path,
        timestamp,
        signature,
        body
    ):
        raise HTTPException(status_code=401, detail="签名验证失败")
    
    # 更新最后使用时间
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    # 获取用户
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or user.status != 1:
        raise HTTPException(status_code=403, detail="用户已被禁用")
    
    return user, api_key
