import os
import uuid
import time
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.celery_app import celery_app
from app.models import User, TtsTask
from app.services.tts_service import SUPPORTED_LANGUAGES, ALLOWED_AUDIO_EXTENSIONS
from app.services.edge_tts_service import get_voices_from_db
from app.services.quota_service import check_and_deduct_quota
from app.tasks.tts_tasks import run_tts_synthesis
from typing import Optional

router = APIRouter()

# 确保目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


@router.get("/languages")
def get_languages():
    """获取支持的语言列表"""
    return SUPPORTED_LANGUAGES


@router.get("/speakers")
def get_speakers(language: Optional[str] = None, db: Session = Depends(get_db)):
    """获取支持的音色列表"""
    # 如果指定了语言，进行过滤 (edge_tts 使用 locale 格式，如 zh-CN)
    locale = None
    if language == 'zh':
        locale = 'zh'
    elif language == 'en':
        locale = 'en'
    
    return get_voices_from_db(db, locale=locale)



@router.post("/create")
async def create_tts_task(
    text: str = Form(..., description="要合成的文本"),
    type: str = Form("clone", description="任务类型: clone | tts"),
    language: str = Form("zh", description="语言代码"),
    voice: Optional[str] = Form(default=None, description="音色名称(TTS模式需要)"),
    speaker_audio: Optional[UploadFile] = File(default=None, description="参考音频文件"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建TTS任务（需要登录）"""
    # 验证语言（clone 模式需要验证，tts 模式语言信息在 voice 中）
    if type == 'clone' and language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"不支持的语言: {language}")
    
    # 验证文本长度
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="文本不能超过1000字符")
    
    upload_path = None
    
    if type == 'clone':
        # 验证必须有音频文件
        if not speaker_audio:
            raise HTTPException(status_code=400, detail="语音克隆模式必须上传音频文件")
            
        # 验证文件格式
        ext = os.path.splitext(speaker_audio.filename)[1].lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")
        
        # 验证文件大小
        content = await speaker_audio.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件不能超过10MB")
            
        # 创建任务ID和路径
        task_id = str(uuid.uuid4())
        upload_path = f"{settings.UPLOAD_DIR}/{task_id}{ext}"
        output_path = f"{settings.OUTPUT_DIR}/{task_id}.wav"
        
        # 保存上传文件
        with open(upload_path, "wb") as f:
            f.write(content)
            
    elif type == 'tts':
        # 验证必须有音色
        if not voice:
            raise HTTPException(status_code=400, detail="文本转语音模式必须选择音色")
            
        task_id = str(uuid.uuid4())
        # TTS 模式不需要上传文件，但为了保持一致性，output_path 依然需要
        output_path = f"{settings.OUTPUT_DIR}/{task_id}.wav"
        # 可以在 speaker_audio_url 中存储音色名，或者留空
        upload_path = voice 
        
    else:
        raise HTTPException(status_code=400, detail=f"不支持的任务类型: {type}")
    
    # 检查并扣除配额
    check_and_deduct_quota(db, user.id, "tts")
    
    # 保存任务到数据库
    tts_task = TtsTask(
        task_id=task_id,
        user_id=user.id,
        text=text,
        language=language,
        speaker_audio_url=upload_path,  # clone模式为路径，tts模式为音色名
        status=0
    )
    db.add(tts_task)
    db.commit()
    
    # 提交 Celery 任务
    celery_task = run_tts_synthesis.delay(task_id, text, language, upload_path, output_path, type, voice)
    
    # 保存 Celery 任务 ID
    tts_task.celery_task_id = celery_task.id
    db.commit()
    
    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}/status")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """查询任务状态（从 Celery 获取实时进度）"""
    task_db = db.query(TtsTask).filter(TtsTask.task_id == task_id).first()
    
    if not task_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    download_url = f"{settings.API_BASE_URL}/api/tts/{task_id}/download"
    
    # 如果已完成或失败，直接返回数据库状态
    if task_db.status == 2:
        return {
            'status': 'completed',
            'progress': 100,
            'message': '合成完成',
            'download_url': download_url
        }
    
    if task_db.status == 3:
        return {
            'status': 'failed',
            'progress': 0,
            'message': task_db.error_message or '合成失败'
        }
    
    # 从 Celery 获取任务状态
    if task_db.celery_task_id:
        celery_result = AsyncResult(task_db.celery_task_id, app=celery_app)
        
        if celery_result.state == 'PENDING':
            return {
                'status': 'pending',
                'progress': 5,
                'message': '任务排队中...'
            }
        elif celery_result.state == 'PROCESSING':
            info = celery_result.info or {}
            return {
                'status': 'processing',
                'progress': info.get('progress', 30),
                'message': info.get('message', '正在处理...')
            }
        elif celery_result.state == 'SUCCESS':
            result = celery_result.result or {}
            return {
                'status': 'completed',
                'progress': 100,
                'message': result.get('message', '合成完成'),
                'download_url': download_url
            }
        elif celery_result.state == 'FAILURE':
            return {
                'status': 'failed',
                'progress': 0,
                'message': str(celery_result.info) if celery_result.info else '合成失败'
            }
    
    # 默认返回
    return {
        'status': 'pending',
        'progress': 0,
        'message': '等待处理...'
    }


@router.get("/{task_id}/download")
async def download_audio(task_id: str, db: Session = Depends(get_db)):
    """下载生成的音频"""
    task_db = db.query(TtsTask).filter(TtsTask.task_id == task_id).first()
    
    if not task_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_db.status != 2:
        raise HTTPException(status_code=400, detail="任务未完成")
    
    output_path = task_db.output_audio_url or f"{settings.OUTPUT_DIR}/{task_id}.wav"
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    timestamp = int(time.time() * 1000)
    filename = f"generated_audio_{timestamp}.wav"
    
    return FileResponse(output_path, media_type="audio/wav", filename=filename)
