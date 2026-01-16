import os
import uuid
import time
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.aksk import verify_aksk
from app.core.config import settings
from app.models import User, ApiKey, TtsTask
from app.services.tts_service import get_tts, SUPPORTED_LANGUAGES, ALLOWED_AUDIO_EXTENSIONS
from app.services.quota_service import check_and_deduct_quota

router = APIRouter()


@router.post("/tts")
async def open_tts(
    text: str = Form(..., description="要合成的文本"),
    speaker_audio: UploadFile = File(..., description="参考音频文件"),
    language: str = Form("zh", description="语言代码"),
    auth: tuple = Depends(verify_aksk),
    db: Session = Depends(get_db)
):
    """
    开放API - TTS语音合成
    
    需要在请求头中携带:
    - X-Access-Key: 你的AK
    - X-Timestamp: 当前时间戳
    - X-Signature: 请求签名
    """
    user, api_key = auth
    
    # 验证语言
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"不支持的语言: {language}")
    
    # 验证文本长度
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="文本不能超过1000字符")
    
    # 验证文件格式
    ext = os.path.splitext(speaker_audio.filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")
    
    # 验证文件大小
    content = await speaker_audio.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过10MB")
    
    # 检查并扣除配额
    check_and_deduct_quota(db, user.id, "tts")
    
    # 创建任务
    task_id = str(uuid.uuid4())
    upload_path = f"{settings.UPLOAD_DIR}/{task_id}{ext}"
    output_path = f"{settings.OUTPUT_DIR}/{task_id}.wav"
    
    # 保存上传文件
    with open(upload_path, "wb") as f:
        f.write(content)
    
    try:
        # 执行合成
        start_time = time.time()
        tts = get_tts()
        tts.tts_to_file(
            text=text,
            speaker_wav=upload_path,
            language=language,
            file_path=output_path
        )
        elapsed = time.time() - start_time
        
        # 保存任务记录
        tts_task = TtsTask(
            task_id=task_id,
            user_id=user.id,
            text=text,
            language=language,
            speaker_audio_url=upload_path,
            output_audio_url=output_path,
            status=2,
            duration_seconds=elapsed
        )
        db.add(tts_task)
        db.commit()
        
        # 返回音频文件
        timestamp = int(time.time() * 1000)
        filename = f"generated_audio_{timestamp}.wav"
        
        return FileResponse(output_path, media_type="audio/wav", filename=filename)
        
    except Exception as e:
        # 记录失败任务
        tts_task = TtsTask(
            task_id=task_id,
            user_id=user.id,
            text=text,
            language=language,
            status=3,
            error_message=str(e)
        )
        db.add(tts_task)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")
    
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)


@router.get("/quota")
async def get_quota(auth: tuple = Depends(verify_aksk), db: Session = Depends(get_db)):
    """获取当前配额"""
    from app.services.quota_service import get_user_quotas
    
    user, api_key = auth
    quotas = get_user_quotas(db, user.id)
    
    return {"quotas": quotas}
