"""视频混剪 Celery 任务"""
import os
from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import VideoTask


@celery_app.task(bind=True)
def run_video_synthesis(self, task_id: str, config: dict):
    """执行视频混剪任务"""
    db = SessionLocal()
    
    try:
        # 更新状态为处理中
        task_db = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
        if task_db:
            task_db.status = 1
            task_db.progress = 5
            task_db.progress_message = "任务开始..."
            db.commit()
        
        def progress_callback(percent: int, message: str):
            """进度回调"""
            self.update_state(state='PROCESSING', meta={'progress': percent, 'message': message})
            # 同时更新数据库
            task = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
            if task:
                task.progress = percent
                task.progress_message = message
                db.commit()
        
        self.update_state(state='PROCESSING', meta={'progress': 10, 'message': '正在加载视频服务...'})
        
        # 导入视频服务
        from app.services.video_service import create_video_from_config, get_media_files
        
        # 准备素材文件
        media_files = []
        if config.get("use_local_videos") and config.get("local_video_dir"):
            media_files = get_media_files(config["local_video_dir"])
        
        # 准备输出路径
        output_path = f"{settings.OUTPUT_DIR}/{task_id}.mp4"
        
        # 构建完整配置
        full_config = {
            "script": config.get("script", ""),
            "voice_audio_path": config.get("voice_audio_path"),
            "bgm_path": config.get("bgm_path") if config.get("bgm_enabled") else None,
            "bgm_volume": config.get("bgm_volume", 0.3),
            "video_size": config.get("video_size", "1080p"),
            "video_layout": config.get("video_layout", "portrait"),
            "video_fps": config.get("video_fps", 30),
            "media_files": media_files,
            "clip_min_duration": config.get("clip_min_duration", 3.0),
            "clip_max_duration": config.get("clip_max_duration", 10.0),
            "transition_type": config.get("transition_type", "fade"),
            "transition_duration": config.get("transition_duration", 1.0),
            "subtitle_enabled": config.get("subtitle_enabled", True),
            "subtitle_config": {
                "font": config.get("subtitle_font", "SimHei"),
                "size": config.get("subtitle_size", 48),
                "color": config.get("subtitle_color", "#FFFFFF"),
                "stroke_color": config.get("subtitle_stroke_color", "#000000"),
                "stroke_width": config.get("subtitle_stroke_width", 2),
                "position": config.get("subtitle_position", "bottom"),
            },
            "output_path": output_path,
        }
        
        # 执行视频生成
        create_video_from_config(full_config, progress_callback)
        
        # 获取视频时长
        from moviepy.editor import VideoFileClip
        with VideoFileClip(output_path) as clip:
            duration = clip.duration
        
        # 更新数据库状态为完成
        task_db = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
        if task_db:
            task_db.status = 2
            task_db.progress = 100
            task_db.progress_message = "视频生成完成"
            task_db.output_video_url = output_path
            task_db.output_duration = duration
            db.commit()
        
        download_url = f"{settings.API_BASE_URL}/api/video/{task_id}/download"
        
        return {
            'status': 'completed',
            'progress': 100,
            'message': '视频生成完成',
            'download_url': download_url,
            'duration': duration
        }
        
    except Exception as e:
        print(f"[Video Task {task_id[:8]}] 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 更新数据库状态为失败
        task_db = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
        if task_db:
            task_db.status = 3
            task_db.progress = 0
            task_db.error_message = str(e)
            db.commit()
        
        raise
        
    finally:
        db.close()
