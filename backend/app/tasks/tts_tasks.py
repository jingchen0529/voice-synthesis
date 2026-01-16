import os
import time
from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import TtsTask


@celery_app.task(bind=True)
def run_tts_synthesis(self, task_id: str, text: str, language: str, upload_path: str, output_path: str, task_type: str = 'clone', voice: str = None):
    """执行 TTS 合成任务"""
    db = SessionLocal()
    import asyncio

    
    try:
        # 更新状态为处理中
        task_db = db.query(TtsTask).filter(TtsTask.task_id == task_id).first()
        if task_db:
            task_db.status = 1
            db.commit()
        
        # 更新 Celery 任务状态
        self.update_state(state='PROCESSING', meta={'progress': 10, 'message': '正在加载模型...'})
        
        if task_type == 'clone':
             # 加载 TTS 模型
            from app.services.tts_service import get_tts
            tts = get_tts()
            
            self.update_state(state='PROCESSING', meta={'progress': 30, 'message': '正在分析参考音频...'})
            
            # 执行合成
            self.update_state(state='PROCESSING', meta={'progress': 50, 'message': '正在合成语音...'})
            
            start_time = time.time()
            tts.tts_to_file(
                text=text,
                speaker_wav=upload_path,
                language=language,
                file_path=output_path
            )
            elapsed = time.time() - start_time
            
        elif task_type == 'tts':
            self.update_state(state='PROCESSING', meta={'progress': 30, 'message': '正在初始化语音服务...'})
            
            from app.services.edge_tts_service import generate_audio
            
            self.update_state(state='PROCESSING', meta={'progress': 50, 'message': '正在生成语音...'})
            
            start_time = time.time()
            # 运行异步生成
            asyncio.run(generate_audio(
                text=text,
                voice=voice,
                output_path=output_path
            ))
            elapsed = time.time() - start_time
            
        else:
             raise ValueError(f"Unknown task type: {task_type}")

        
        self.update_state(state='PROCESSING', meta={'progress': 90, 'message': '正在保存文件...'})
        
        # 更新数据库状态为完成
        task_db = db.query(TtsTask).filter(TtsTask.task_id == task_id).first()
        if task_db:
            task_db.status = 2
            task_db.output_audio_url = output_path
            task_db.duration_seconds = elapsed
            db.commit()
        
        return {
            'status': 'completed',
            'progress': 100,
            'message': f'合成完成，耗时 {elapsed:.1f} 秒',
            'download_url': f'/api/tts/{task_id}/download'
        }
        
    except Exception as e:
        print(f"[Task {task_id[:8]}] 错误: {str(e)}")
        
        # 更新数据库状态为失败
        task_db = db.query(TtsTask).filter(TtsTask.task_id == task_id).first()
        if task_db:
            task_db.status = 3
            task_db.error_message = str(e)
            db.commit()
        
        raise
        
    finally:
        # 清理上传文件 (仅当存在且为Clone模式或者确认是临时文件时)
        if upload_path and os.path.exists(upload_path) and task_type == 'clone':
            os.remove(upload_path)
        db.close()
