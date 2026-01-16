"""视频混剪 API"""
import os
import uuid
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.celery_app import celery_app
from app.models import User, VideoTask
from app.services.quota_service import check_and_deduct_quota
from app.tasks.video_tasks import run_video_synthesis
from app.services.ai_service import get_available_providers, generate_script
from app.services.edge_tts_service import get_voices_from_db, get_locales_from_db, sync_voices_to_db, generate_audio

router = APIRouter()

# 确保目录存在
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/bgm", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/videos", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/images", exist_ok=True)


class VideoTaskCreate(BaseModel):
    """创建视频任务请求 (Requirements 9.1)"""
    # 文案配置
    topic: Optional[str] = None
    script: str
    script_language: str = "zh"
    
    # 配音配置
    voice_language: str = "zh"
    voice_name: str = "zh-CN-XiaoxiaoNeural"
    voice_speed: str = "+0%"
    voice_audio_url: Optional[str] = None  # 已有的配音文件
    
    # 背景音乐配置 (Requirements 6.7, 6.8)
    bgm_enabled: bool = False
    bgm_path: Optional[str] = None
    bgm_volume: float = Field(default=0.3, ge=0.0, le=1.0, description="BGM音量 0-1 (0%-100%)")
    bgm_fade_in: float = Field(default=0.0, ge=0.0, le=5.0, description="BGM淡入时长（秒）")
    bgm_fade_out: float = Field(default=0.0, ge=0.0, le=5.0, description="BGM淡出时长（秒）")
    
    # 视频配置 (Requirements 5.1, 5.2, 5.3, 5.4)
    video_resolution: str = Field(default="1080p", description="分辨率: 480p, 720p, 1080p, 2k, 4k")
    video_layout: str = Field(default="9:16", description="布局: 9:16, 3:4, 1:1, 4:3, 16:9, 21:9")
    video_fps: int = Field(default=30, ge=24, le=60, description="帧率: 24, 25, 30, 50, 60")
    platform_preset: Optional[str] = Field(default=None, description="平台预设: douyin, kuaishou, xiaohongshu, bilibili, youtube, instagram_reels, instagram_feed, weixin")
    fit_mode: str = Field(default="crop", description="素材适配模式: crop, fit, stretch")
    
    # 旧版视频配置（保持向后兼容）
    video_size: str = "1080p"  # 已废弃，使用 video_resolution
    
    # 片段配置 (Requirements 6.2)
    clip_min_duration: float = Field(default=3.0, ge=1.0, le=30.0, description="片段最小时长（秒）")
    clip_max_duration: float = Field(default=10.0, ge=1.0, le=60.0, description="片段最大时长（秒）")
    
    # 素材配置
    use_local_videos: bool = False
    local_video_dir: Optional[str] = None
    media_paths: Optional[List[str]] = None  # 上传的素材路径列表（图片+视频）
    
    # 转场配置 (Requirements 6.4, 6.5)
    transition_enabled: bool = True
    transition_type: str = Field(default="fade", description="转场类型: none, fade, slide_left, slide_right, slide_up, slide_down, zoom_in, zoom_out, dissolve, wipe_left, wipe_right")
    transition_effect: str = "fade"  # 已废弃，使用 transition_type
    transition_duration: float = Field(default=0.5, ge=0.3, le=2.0, description="转场时长（秒）")
    
    # 字幕配置 (Requirements 7.1-7.6)
    subtitle_enabled: bool = True
    subtitle_font: str = "Heiti-SC-Medium"
    subtitle_size: int = Field(default=48, ge=12, le=120, description="字幕字号")
    subtitle_color: str = "#FFFFFF"
    subtitle_stroke_color: str = "#000000"
    subtitle_stroke_width: float = Field(default=2.0, ge=0.0, le=10.0, description="字幕描边宽度")
    subtitle_position: str = Field(default="bottom", description="字幕位置: top, center, bottom")
    subtitle_line_spacing: int = 2
    
    # 特效配置 (Requirements 10.1, 10.2, 10.3)
    effect_type: Optional[str] = Field(default=None, description="特效类型: none, ken_burns_in, ken_burns_out, shake, zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down")
    color_filter: str = Field(default="none", description="颜色滤镜: none, grayscale, vintage, warm, cool, high_contrast, soft")
    brightness: float = Field(default=1.0, ge=0.5, le=2.0, description="亮度 0.5-2.0")
    contrast: float = Field(default=1.0, ge=0.5, le=2.0, description="对比度 0.5-2.0")
    saturation: float = Field(default=1.0, ge=0.0, le=2.0, description="饱和度 0-2.0")
    
    # 输出配置 (Requirements 6.10)
    output_quality: str = Field(default="high", description="输出质量: low, medium, high, ultra")


@router.get("/config")
def get_video_config():
    """获取视频配置选项 (Requirements 9.1)
    
    返回完整的配置选项，包括分辨率、布局、帧率、平台预设、转场、滤镜等。
    """
    from app.services.video_service import (
        VIDEO_RESOLUTIONS,
        VIDEO_LAYOUTS,
        FRAME_RATES,
        PLATFORM_PRESETS,
        TRANSITIONS,
        FIT_MODES,
        COLOR_FILTERS,
        EFFECT_TYPES,
        TRANSITION_DURATION_MIN,
        TRANSITION_DURATION_MAX,
        TRANSITION_DURATION_DEFAULT,
        BRIGHTNESS_MIN,
        BRIGHTNESS_MAX,
        BRIGHTNESS_DEFAULT,
        CONTRAST_MIN,
        CONTRAST_MAX,
        CONTRAST_DEFAULT,
        SATURATION_MIN,
        SATURATION_MAX,
        SATURATION_DEFAULT,
        BGM_VOLUME_MIN,
        BGM_VOLUME_MAX,
        BGM_VOLUME_DEFAULT,
        BGM_FADE_IN_MIN,
        BGM_FADE_IN_MAX,
        BGM_FADE_IN_DEFAULT,
        BGM_FADE_OUT_MIN,
        BGM_FADE_OUT_MAX,
        BGM_FADE_OUT_DEFAULT,
    )
    
    return {
        # 视频分辨率选项 (Requirements 5.1)
        "resolutions": [
            {"value": key, "label": f"{key.upper()} ({val['width']}x{val['height']})"}
            for key, val in VIDEO_RESOLUTIONS.items()
        ],
        
        # 视频布局选项 (Requirements 5.2)
        "layouts": [
            {"value": key, "label": val["name"], "ratio": f"{val['ratio'][0]}:{val['ratio'][1]}"}
            for key, val in VIDEO_LAYOUTS.items()
        ],
        
        # 帧率选项 (Requirements 5.3)
        "fps_options": [
            {"value": fps, "label": f"{fps}fps"}
            for fps in FRAME_RATES
        ],
        
        # 平台预设 (Requirements 5.4)
        "platform_presets": [
            {
                "value": key,
                "label": val["name"],
                "resolution": val["resolution"],
                "layout": val["layout"],
                "fps": val["fps"]
            }
            for key, val in PLATFORM_PRESETS.items()
        ],
        
        # 素材适配模式 (Requirements 6.1)
        "fit_modes": [
            {"value": key, "label": val}
            for key, val in FIT_MODES.items()
        ],
        
        # 转场效果 (Requirements 6.4)
        "transitions": [
            {"value": key, "label": val["name"], "default_duration": val["duration"]}
            for key, val in TRANSITIONS.items()
        ],
        
        # 转场时长配置 (Requirements 6.5)
        "transition_duration": {
            "min": TRANSITION_DURATION_MIN,
            "max": TRANSITION_DURATION_MAX,
            "default": TRANSITION_DURATION_DEFAULT
        },
        
        # 颜色滤镜 (Requirements 10.2)
        "color_filters": [
            {"value": key, "label": val}
            for key, val in COLOR_FILTERS.items()
        ],
        
        # 视频特效 (Requirements 10.1)
        "effect_types": [
            {"value": key, "label": val}
            for key, val in EFFECT_TYPES.items()
        ],
        
        # 亮度配置 (Requirements 10.3)
        "brightness": {
            "min": BRIGHTNESS_MIN,
            "max": BRIGHTNESS_MAX,
            "default": BRIGHTNESS_DEFAULT
        },
        
        # 对比度配置 (Requirements 10.3)
        "contrast": {
            "min": CONTRAST_MIN,
            "max": CONTRAST_MAX,
            "default": CONTRAST_DEFAULT
        },
        
        # 饱和度配置 (Requirements 10.3)
        "saturation": {
            "min": SATURATION_MIN,
            "max": SATURATION_MAX,
            "default": SATURATION_DEFAULT
        },
        
        # BGM 音量配置 (Requirements 6.7)
        "bgm_volume": {
            "min": BGM_VOLUME_MIN,
            "max": BGM_VOLUME_MAX,
            "default": BGM_VOLUME_DEFAULT
        },
        
        # BGM 淡入配置 (Requirements 6.8)
        "bgm_fade_in": {
            "min": BGM_FADE_IN_MIN,
            "max": BGM_FADE_IN_MAX,
            "default": BGM_FADE_IN_DEFAULT
        },
        
        # BGM 淡出配置 (Requirements 6.8)
        "bgm_fade_out": {
            "min": BGM_FADE_OUT_MIN,
            "max": BGM_FADE_OUT_MAX,
            "default": BGM_FADE_OUT_DEFAULT
        },
        
        # 字幕位置选项 (Requirements 7.4)
        "subtitle_positions": [
            {"value": "top", "label": "顶部"},
            {"value": "center", "label": "居中"},
            {"value": "bottom", "label": "底部"},
        ],
        
        # 语速选项
        "voice_speeds": [
            {"value": "-50%", "label": "慢速"},
            {"value": "-25%", "label": "稍慢"},
            {"value": "+0%", "label": "正常"},
            {"value": "+25%", "label": "稍快"},
            {"value": "+50%", "label": "快速"},
        ],
        
        # 输出质量选项 (Requirements 6.10)
        "output_qualities": [
            {"value": "low", "label": "低质量"},
            {"value": "medium", "label": "中等质量"},
            {"value": "high", "label": "高质量"},
            {"value": "ultra", "label": "极高质量"},
        ],
        
        # 片段时长配置 (Requirements 6.2)
        "clip_duration": {
            "min": 1.0,
            "max": 60.0,
            "default_min": 3.0,
            "default_max": 10.0
        },
        
        # 字幕字号配置
        "subtitle_size": {
            "min": 12,
            "max": 120,
            "default": 48
        },
        
        # 字幕描边宽度配置
        "subtitle_stroke_width": {
            "min": 0.0,
            "max": 10.0,
            "default": 2.0
        },
    }


@router.post("/create")
async def create_video_task(
    data: VideoTaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建视频混剪任务 - 后台线程处理，立即返回 (Requirements 9.4, 9.5)"""
    import threading
    import traceback
    from app.services.video_service import (
        create_video_from_config, get_media_files,
        VIDEO_RESOLUTIONS, VIDEO_LAYOUTS, FRAME_RATES, PLATFORM_PRESETS,
        TRANSITIONS, FIT_MODES, COLOR_FILTERS, EFFECT_TYPES,
        TRANSITION_DURATION_MIN, TRANSITION_DURATION_MAX,
        BRIGHTNESS_MIN, BRIGHTNESS_MAX,
        CONTRAST_MIN, CONTRAST_MAX,
        SATURATION_MIN, SATURATION_MAX,
        BGM_VOLUME_MIN, BGM_VOLUME_MAX,
        BGM_FADE_IN_MIN, BGM_FADE_IN_MAX,
        BGM_FADE_OUT_MIN, BGM_FADE_OUT_MAX,
    )
    from app.core.database import SessionLocal
    
    # 验证文案 (Requirements 9.4)
    if not data.script or len(data.script.strip()) == 0:
        raise HTTPException(status_code=400, detail="文案不能为空")
    
    if len(data.script) > 5000:
        raise HTTPException(status_code=400, detail="文案不能超过5000字符")
    
    # 验证视频分辨率 (Requirements 9.4, 9.5)
    if data.video_resolution not in VIDEO_RESOLUTIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的分辨率: {data.video_resolution}，支持的分辨率: {list(VIDEO_RESOLUTIONS.keys())}"
        )
    
    # 验证视频布局 (Requirements 9.4, 9.5)
    if data.video_layout not in VIDEO_LAYOUTS:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的布局: {data.video_layout}，支持的布局: {list(VIDEO_LAYOUTS.keys())}"
        )
    
    # 验证帧率 (Requirements 9.4, 9.5)
    if data.video_fps not in FRAME_RATES:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的帧率: {data.video_fps}，支持的帧率: {FRAME_RATES}"
        )
    
    # 验证平台预设（如果指定）(Requirements 9.4, 9.5)
    # 空字符串或 None 都视为不使用预设
    if data.platform_preset and data.platform_preset not in PLATFORM_PRESETS:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的平台预设: {data.platform_preset}，支持的预设: {list(PLATFORM_PRESETS.keys())}"
        )
    
    # 验证素材适配模式 (Requirements 9.4, 9.5)
    if data.fit_mode not in FIT_MODES:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的适配模式: {data.fit_mode}，支持的模式: {list(FIT_MODES.keys())}"
        )
    
    # 验证转场类型 (Requirements 9.4, 9.5)
    if data.transition_type not in TRANSITIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的转场类型: {data.transition_type}，支持的类型: {list(TRANSITIONS.keys())}"
        )
    
    # 验证转场时长 (Requirements 9.4, 9.5)
    if data.transition_duration < TRANSITION_DURATION_MIN or data.transition_duration > TRANSITION_DURATION_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"转场时长必须在 {TRANSITION_DURATION_MIN} 到 {TRANSITION_DURATION_MAX} 秒之间"
        )
    
    # 验证颜色滤镜 (Requirements 9.4, 9.5)
    if data.color_filter not in COLOR_FILTERS:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的滤镜类型: {data.color_filter}，支持的类型: {list(COLOR_FILTERS.keys())}"
        )
    
    # 验证特效类型（如果指定）(Requirements 9.4, 9.5)
    # 空字符串或 None 都视为不使用特效
    if data.effect_type and data.effect_type not in EFFECT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的特效类型: {data.effect_type}，支持的类型: {list(EFFECT_TYPES.keys())}"
        )
    
    # 验证亮度 (Requirements 9.4, 9.5)
    if data.brightness < BRIGHTNESS_MIN or data.brightness > BRIGHTNESS_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"亮度值必须在 {BRIGHTNESS_MIN} 到 {BRIGHTNESS_MAX} 之间"
        )
    
    # 验证对比度 (Requirements 9.4, 9.5)
    if data.contrast < CONTRAST_MIN or data.contrast > CONTRAST_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"对比度值必须在 {CONTRAST_MIN} 到 {CONTRAST_MAX} 之间"
        )
    
    # 验证饱和度 (Requirements 9.4, 9.5)
    if data.saturation < SATURATION_MIN or data.saturation > SATURATION_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"饱和度值必须在 {SATURATION_MIN} 到 {SATURATION_MAX} 之间"
        )
    
    # 验证 BGM 音量 (Requirements 9.4, 9.5)
    if data.bgm_volume < BGM_VOLUME_MIN or data.bgm_volume > BGM_VOLUME_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"BGM 音量必须在 {BGM_VOLUME_MIN} 到 {BGM_VOLUME_MAX} 之间"
        )
    
    # 验证 BGM 淡入时长 (Requirements 9.4, 9.5)
    if data.bgm_fade_in < BGM_FADE_IN_MIN or data.bgm_fade_in > BGM_FADE_IN_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"BGM 淡入时长必须在 {BGM_FADE_IN_MIN} 到 {BGM_FADE_IN_MAX} 秒之间"
        )
    
    # 验证 BGM 淡出时长 (Requirements 9.4, 9.5)
    if data.bgm_fade_out < BGM_FADE_OUT_MIN or data.bgm_fade_out > BGM_FADE_OUT_MAX:
        raise HTTPException(
            status_code=400, 
            detail=f"BGM 淡出时长必须在 {BGM_FADE_OUT_MIN} 到 {BGM_FADE_OUT_MAX} 秒之间"
        )
    
    # 验证片段时长配置 (Requirements 9.4, 9.5)
    if data.clip_min_duration > data.clip_max_duration:
        raise HTTPException(
            status_code=400, 
            detail="片段最小时长不能大于最大时长"
        )
    
    # 验证字幕位置 (Requirements 9.4, 9.5)
    valid_subtitle_positions = ["top", "center", "bottom", "top_left", "top_right", "left", "right", "bottom_left", "bottom_right"]
    if data.subtitle_position not in valid_subtitle_positions:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的字幕位置: {data.subtitle_position}，支持的位置: {valid_subtitle_positions}"
        )
    
    # 验证输出质量 (Requirements 9.4, 9.5)
    valid_output_qualities = ["low", "medium", "high", "ultra"]
    if data.output_quality not in valid_output_qualities:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的输出质量: {data.output_quality}，支持的质量: {valid_output_qualities}"
        )
    
    # 如果指定了平台预设，应用预设配置 (Requirements 5.5)
    if data.platform_preset:
        preset = PLATFORM_PRESETS[data.platform_preset]
        data.video_resolution = preset["resolution"]
        data.video_layout = preset["layout"]
        data.video_fps = preset["fps"]
    
    # 检查并扣除配额（统一使用 tts 配额）
    check_and_deduct_quota(db, user.id, "tts")
    
    # 创建任务 - 使用 UUID 格式 (Requirements 8.1)
    from app.services.video_service import generate_task_id
    task_id = generate_task_id()
    
    # 保存任务到数据库
    video_task = VideoTask(
        task_id=task_id,
        user_id=user.id,
        topic=data.topic,
        script=data.script,
        script_language=data.script_language,
        voice_language=data.voice_language,
        voice_name=data.voice_name,
        voice_speed=data.voice_speed,
        voice_audio_url=data.voice_audio_url,
        bgm_enabled=1 if data.bgm_enabled else 0,
        bgm_path=data.bgm_path,
        bgm_volume=data.bgm_volume,
        video_resolution=data.video_resolution,
        video_layout=data.video_layout,
        video_fps=data.video_fps,
        fit_mode=data.fit_mode,
        clip_min_duration=data.clip_min_duration,
        clip_max_duration=data.clip_max_duration,
        use_local_videos=1 if data.use_local_videos else 0,
        local_video_dir=data.local_video_dir,
        transition_enabled=1 if data.transition_enabled else 0,
        transition_type=data.transition_type,
        transition_effect=data.transition_effect,
        transition_duration=data.transition_duration,
        subtitle_enabled=1 if data.subtitle_enabled else 0,
        subtitle_font=data.subtitle_font,
        subtitle_size=data.subtitle_size,
        subtitle_color=data.subtitle_color,
        subtitle_stroke_color=data.subtitle_stroke_color,
        subtitle_stroke_width=data.subtitle_stroke_width,
        subtitle_position=data.subtitle_position,
        subtitle_line_spacing=data.subtitle_line_spacing,
        # 特效配置
        effect_type=data.effect_type,
        color_filter=data.color_filter,
        brightness=data.brightness,
        contrast=data.contrast,
        saturation=data.saturation,
        output_quality=data.output_quality,
        # BGM 淡入淡出
        bgm_fade_in=data.bgm_fade_in,
        bgm_fade_out=data.bgm_fade_out,
        status=1,  # 处理中
        progress=0,
        progress_message="任务已创建，等待处理..."
    )
    db.add(video_task)
    db.commit()
    
    # 准备素材文件
    media_files = []
    # 使用上传的素材
    if data.media_paths:
        media_files = [p for p in data.media_paths if os.path.exists(p)]
    # 如果没有上传素材，尝试使用本地目录
    if not media_files and data.use_local_videos and data.local_video_dir:
        media_files = get_media_files(data.local_video_dir)
    
    print(f"[Video {task_id[:8]}] 素材文件: {len(media_files)} 个")
    
    # 准备输出路径
    output_path = f"{settings.OUTPUT_DIR}/{task_id}.mp4"
    
    # 构建完整配置
    full_config = {
        "script": data.script,
        "voice_audio_path": data.voice_audio_url,
        "bgm_path": data.bgm_path if data.bgm_enabled else None,
        "bgm_volume": data.bgm_volume,
        "bgm_fade_in": data.bgm_fade_in,
        "bgm_fade_out": data.bgm_fade_out,
        "video_resolution": data.video_resolution,
        "video_layout": data.video_layout,
        "video_fps": data.video_fps,
        "fit_mode": data.fit_mode,
        "media_files": media_files,
        "clip_min_duration": data.clip_min_duration,
        "clip_max_duration": data.clip_max_duration,
        "transition_type": data.transition_type,
        "transition_duration": data.transition_duration,
        "subtitle_enabled": data.subtitle_enabled,
        "subtitle_config": {
            "font": data.subtitle_font,
            "size": data.subtitle_size,
            "color": data.subtitle_color,
            "stroke_color": data.subtitle_stroke_color,
            "stroke_width": data.subtitle_stroke_width,
            "position": data.subtitle_position,
        },
        # 特效配置
        "effect_type": data.effect_type,
        "color_filter": data.color_filter,
        "brightness": data.brightness,
        "contrast": data.contrast,
        "saturation": data.saturation,
        "output_quality": data.output_quality,
        "output_path": output_path,
    }
    
    # 后台线程处理视频生成
    def process_video():
        import asyncio
        from moviepy.editor import VideoFileClip
        from app.services.edge_tts_service import generate_audio
        
        # 创建新的数据库会话
        thread_db = SessionLocal()
        try:
            thread_task = thread_db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
            if not thread_task:
                return
            
            print(f"[Video {task_id[:8]}] 开始后台处理...")
            
            def progress_callback(percent: int, message: str):
                print(f"[Video {task_id[:8]}] 进度: {percent}% - {message}")
                thread_task.progress = percent
                thread_task.progress_message = message
                thread_db.commit()
            
            # 第一步：生成配音（带字幕时间戳）
            progress_callback(5, "正在生成配音...")
            voice_audio_path = None
            sentence_subtitles = []
            if data.script and data.voice_name:
                try:
                    voice_output = f"{settings.OUTPUT_DIR}/tts/{task_id}.mp3"
                    os.makedirs(os.path.dirname(voice_output), exist_ok=True)
                    
                    # 使用 Edge TTS 生成配音并获取字幕时间戳
                    from app.services.edge_tts_service import generate_audio_with_subtitles, merge_word_subtitles_to_sentences
                    
                    voice_audio_path, word_subtitles = asyncio.run(generate_audio_with_subtitles(
                        text=data.script,
                        voice=data.voice_name,
                        rate=data.voice_speed or "+0%",
                        output_path=voice_output
                    ))
                    
                    # 合并为句子级字幕
                    if word_subtitles:
                        sentence_subtitles = merge_word_subtitles_to_sentences(word_subtitles, data.script)
                    
                    print(f"[Video {task_id[:8]}] 配音生成完成: {voice_audio_path}, 字幕: {len(sentence_subtitles)} 句")
                except Exception as e:
                    print(f"[Video {task_id[:8]}] 配音生成失败: {e}")
                    # 降级到普通配音
                    try:
                        voice_audio_path = asyncio.run(generate_audio(
                            text=data.script,
                            voice=data.voice_name,
                            rate=data.voice_speed or "+0%",
                            output_path=voice_output
                        ))
                    except:
                        pass
            
            # 更新配置中的配音路径和字幕
            full_config["voice_audio_path"] = voice_audio_path
            full_config["sentence_subtitles"] = sentence_subtitles
            
            # 第二步：生成视频
            create_video_from_config(full_config, progress_callback)
            
            # 获取视频时长
            with VideoFileClip(output_path) as clip:
                duration = clip.duration
            
            # 更新数据库状态为完成
            thread_task.status = 2
            thread_task.progress = 100
            thread_task.progress_message = "视频生成完成"
            thread_task.output_video_url = output_path
            thread_task.output_duration = duration
            thread_db.commit()
            
            print(f"[Video {task_id[:8]}] 完成! 时长: {duration}s")
            
        except Exception as e:
            print(f"[Video {task_id[:8]}] 错误: {str(e)}")
            traceback.print_exc()
            
            thread_task = thread_db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
            if thread_task:
                thread_task.status = 3
                thread_task.progress = 0
                thread_task.error_message = str(e)
                thread_db.commit()
        finally:
            thread_db.close()
    
    # 启动后台线程
    thread = threading.Thread(target=process_video, daemon=True)
    thread.start()
    
    # 立即返回任务 ID
    return {
        "task_id": task_id,
        "status": "processing"
    }


@router.get("/{task_id}/status")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """查询视频任务状态 (Requirements 8.3, 8.5, 8.6)
    
    返回完整状态信息：
    - status: 状态枚举值 (pending, processing, completed, failed)
    - progress: 进度百分比 (0-100)
    - message: 状态消息
    - download_url: 下载链接（仅完成状态）
    - error_message: 错误信息（仅失败状态）
    """
    from app.services.video_service import (
        build_task_status_response,
        TASK_STATUS_PENDING,
        TASK_STATUS_PROCESSING,
        TASK_STATUS_COMPLETED,
        TASK_STATUS_FAILED,
    )
    
    task_db = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
    
    if not task_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    download_url = f"{settings.API_BASE_URL}/api/video/{task_id}/download"
    
    # 如果已完成，返回完整状态信息 (Requirements 8.5)
    if task_db.status == TASK_STATUS_COMPLETED:
        response = build_task_status_response(
            status_code=TASK_STATUS_COMPLETED,
            progress=100,
            progress_message="视频生成完成",
            download_url=download_url,
            duration=task_db.output_duration,
            task_id=task_id
        )
        return response.to_dict()
    
    # 如果失败，返回错误信息 (Requirements 8.6)
    if task_db.status == TASK_STATUS_FAILED:
        response = build_task_status_response(
            status_code=TASK_STATUS_FAILED,
            progress=0,
            progress_message=task_db.error_message or "视频生成失败",
            error_message=task_db.error_message or "视频生成失败",
            task_id=task_id
        )
        return response.to_dict()
    
    # 从 Celery 获取任务状态
    if task_db.celery_task_id:
        celery_result = AsyncResult(task_db.celery_task_id, app=celery_app)
        
        if celery_result.state == 'PENDING':
            response = build_task_status_response(
                status_code=TASK_STATUS_PENDING,
                progress=task_db.progress or 5,
                progress_message=task_db.progress_message or "任务排队中...",
                task_id=task_id
            )
            return response.to_dict()
        elif celery_result.state == 'PROCESSING':
            info = celery_result.info or {}
            response = build_task_status_response(
                status_code=TASK_STATUS_PROCESSING,
                progress=info.get('progress', task_db.progress or 30),
                progress_message=info.get('message', task_db.progress_message or "正在处理..."),
                task_id=task_id
            )
            return response.to_dict()
        elif celery_result.state == 'SUCCESS':
            result = celery_result.result or {}
            response = build_task_status_response(
                status_code=TASK_STATUS_COMPLETED,
                progress=100,
                progress_message=result.get('message', '视频生成完成'),
                download_url=download_url,
                duration=result.get('duration'),
                task_id=task_id
            )
            return response.to_dict()
        elif celery_result.state == 'FAILURE':
            error_msg = str(celery_result.info) if celery_result.info else '视频生成失败'
            response = build_task_status_response(
                status_code=TASK_STATUS_FAILED,
                progress=0,
                progress_message=error_msg,
                error_message=error_msg,
                task_id=task_id
            )
            return response.to_dict()
    
    # 默认返回数据库中的进度 (Requirements 8.3)
    response = build_task_status_response(
        status_code=task_db.status,
        progress=task_db.progress or 0,
        progress_message=task_db.progress_message or "等待处理...",
        task_id=task_id
    )
    return response.to_dict()


@router.get("/{task_id}/download")
async def download_video(task_id: str, db: Session = Depends(get_db)):
    """下载生成的视频"""
    task_db = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
    
    if not task_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_db.status != 2:
        raise HTTPException(status_code=400, detail="任务未完成")
    
    output_path = task_db.output_video_url or f"{settings.OUTPUT_DIR}/{task_id}.mp4"
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    timestamp = int(time.time() * 1000)
    filename = f"generated_video_{timestamp}.mp4"
    
    return FileResponse(output_path, media_type="video/mp4", filename=filename)


@router.post("/upload/bgm")
async def upload_bgm(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """上传背景音乐"""
    # 验证文件格式
    allowed_ext = {".mp3", ".wav", ".m4a", ".ogg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")
    
    # 验证文件大小 (最大 20MB)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过20MB")
    
    # 保存文件
    file_id = str(uuid.uuid4())
    file_path = f"{settings.UPLOAD_DIR}/bgm/{file_id}{ext}"
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_path": file_path,
        "filename": file.filename
    }


@router.post("/upload/voice")
async def upload_voice(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """上传自定义配音"""
    # 验证文件格式
    allowed_ext = {".mp3", ".wav", ".m4a", ".ogg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")
    
    # 验证文件大小 (最大 50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过50MB")
    
    # 确保目录存在
    voice_dir = f"{settings.UPLOAD_DIR}/voice/{user.id}"
    os.makedirs(voice_dir, exist_ok=True)
    
    # 保存文件
    file_id = str(uuid.uuid4())
    file_path = f"{voice_dir}/{file_id}{ext}"
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_path": file_path,
        "filename": file.filename
    }


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """上传图片素材"""
    # 验证文件格式
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")
    
    # 验证文件大小 (最大 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过10MB")
    
    # 保存文件
    file_id = str(uuid.uuid4())
    file_path = f"{settings.UPLOAD_DIR}/images/{user.id}/{file_id}{ext}"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_path": file_path,
        "filename": file.filename
    }


@router.post("/upload/images")
async def upload_images(
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user)
):
    """批量上传图片素材"""
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    results = []
    
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_ext:
            continue
        
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            continue
        
        file_id = str(uuid.uuid4())
        file_path = f"{settings.UPLOAD_DIR}/images/{user.id}/{file_id}{ext}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        results.append({
            "file_path": file_path,
            "filename": file.filename
        })
    
    return {"files": results, "count": len(results)}


@router.get("/list")
async def list_video_tasks(
    page: int = 1,
    page_size: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的视频任务列表"""
    offset = (page - 1) * page_size
    
    total = db.query(VideoTask).filter(VideoTask.user_id == user.id).count()
    tasks = db.query(VideoTask).filter(
        VideoTask.user_id == user.id
    ).order_by(VideoTask.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "task_id": t.task_id,
                "topic": t.topic,
                "status": t.status,
                "progress": t.progress,
                "duration": t.output_duration,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


@router.post("/upload/videos")
async def upload_videos(
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user)
):
    """批量上传视频素材（最大 150MB/个）"""
    allowed_ext = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    results = []
    max_size = 150 * 1024 * 1024  # 150MB
    
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_ext:
            continue
        
        content = await file.read()
        if len(content) > max_size:
            continue
        
        file_id = str(uuid.uuid4())
        file_path = f"{settings.UPLOAD_DIR}/videos/{user.id}/{file_id}{ext}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        results.append({
            "file_path": file_path,
            "filename": file.filename,
            "size": len(content)
        })
    
    return {"files": results, "count": len(results)}


class ScriptGenerateRequest(BaseModel):
    """文案生成请求"""
    topic: str
    provider: str = "auto"  # auto, openai, deepseek, grok, kimi, qwen
    style: str = "口播"  # 口播, 故事, 科普, 幽默
    duration: str = "1分钟"  # 30秒, 1分钟, 3分钟, 5分钟
    language: str = "zh"


@router.get("/ai/providers")
def get_ai_providers():
    """获取可用的 AI 服务商列表"""
    return {
        "providers": get_available_providers(),
        "styles": [
            {"value": "口播", "label": "口播讲解"},
            {"value": "故事", "label": "故事叙述"},
            {"value": "科普", "label": "科普知识"},
            {"value": "幽默", "label": "幽默搐笑"},
        ],
        "durations": [
            {"value": "30秒", "label": "30秒"},
            {"value": "1分钟", "label": "1分钟"},
            {"value": "3分钟", "label": "3分钟"},
            {"value": "5分钟", "label": "5分钟"},
        ]
    }


@router.post("/ai/generate-script")
async def api_generate_script(
    data: ScriptGenerateRequest,
    user: User = Depends(get_current_user)
):
    """使用 AI 生成视频文案"""
    if not data.topic or len(data.topic.strip()) == 0:
        raise HTTPException(status_code=400, detail="请输入视频主题")
    
    try:
        script = await generate_script(
            topic=data.topic,
            provider=data.provider,
            style=data.style,
            duration=data.duration,
            language=data.language
        )
        return {
            "script": script,
            "provider": data.provider,
            "topic": data.topic
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案生成失败: {str(e)}")


# ==================== Edge TTS 音色相关 API ====================

@router.get("/tts/voices")
def get_tts_voices(
    locale: Optional[str] = None,
    gender: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 Edge TTS 音色列表"""
    voices = get_voices_from_db(db, locale=locale, gender=gender, search=search)
    return {
        "voices": voices,
        "total": len(voices)
    }


@router.get("/tts/locales")
def get_tts_locales(db: Session = Depends(get_db)):
    """获取可用的语言列表"""
    locales = get_locales_from_db(db)
    return {
        "locales": locales,
        "speeds": [
            {"value": "-50%", "label": "慢速"},
            {"value": "-25%", "label": "稍慢"},
            {"value": "+0%", "label": "正常"},
            {"value": "+25%", "label": "稍快"},
            {"value": "+50%", "label": "快速"},
        ]
    }


class GenerateAudioRequest(BaseModel):
    text: str
    voice: str
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0Hz"


class GenerateAudioWithSubtitlesRequest(BaseModel):
    """生成配音并获取字幕时间戳"""
    text: str
    voice: str
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0Hz"


class VideoTrimRequest(BaseModel):
    """视频裁剪请求"""
    file_path: str
    start_time: float
    end_time: float


@router.post("/tts/generate-audio")
async def generate_audio_for_preview(
    request: GenerateAudioRequest,
    user: User = Depends(get_current_user)
):
    """生成配音用于预览"""
    from app.services.edge_tts_service import generate_audio
    
    # 参数验证
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")
    
    if not request.voice or not request.voice.strip():
        raise HTTPException(status_code=400, detail="请选择音色")
    
    print(f"[TTS] 生成音频: text={request.text[:50]}..., voice={request.voice}, rate={request.rate}")
    
    try:
        # 生成音频文件
        output_path = f"{settings.OUTPUT_DIR}/tts/preview_{uuid.uuid4()}.mp3"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        audio_path = await generate_audio(
            text=request.text.strip(),
            voice=request.voice.strip(),
            rate=request.rate,
            volume=request.volume,
            pitch=request.pitch,
            output_path=output_path
        )
        
        print(f"[TTS] 生成成功: {audio_path}")
        
        # 返回完整 URL（outputs 目录挂载在 /static/outputs）
        relative_path = audio_path.replace(settings.OUTPUT_DIR + "/", "").replace(settings.OUTPUT_DIR, "")
        audio_url = f"{settings.API_BASE_URL}/static/outputs/{relative_path}"
        
        return {
            "audio_url": audio_url,
            "file_path": audio_path
        }
    except Exception as e:
        print(f"[TTS] 生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成配音失败: {str(e)}")


@router.post("/tts/generate-audio-with-subtitles")
async def generate_audio_with_subtitles_api(
    request: GenerateAudioWithSubtitlesRequest,
    user: User = Depends(get_current_user)
):
    """生成配音并获取精准字幕时间戳"""
    from app.services.edge_tts_service import generate_audio_with_subtitles, merge_word_subtitles_to_sentences
    
    try:
        output_path = f"{settings.OUTPUT_DIR}/tts/preview_{uuid.uuid4()}.mp3"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 生成音频和字幕
        audio_path, word_subtitles = await generate_audio_with_subtitles(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume,
            pitch=request.pitch,
            output_path=output_path
        )
        
        # 合并为句子级字幕
        sentence_subtitles = merge_word_subtitles_to_sentences(word_subtitles, request.text)
        
        # 返回完整 URL
        relative_path = audio_path.replace(settings.OUTPUT_DIR + "/", "").replace(settings.OUTPUT_DIR, "")
        audio_url = f"{settings.API_BASE_URL}/static/outputs/{relative_path}"
        
        return {
            "audio_url": audio_url,
            "file_path": audio_path,
            "word_subtitles": word_subtitles,
            "sentence_subtitles": sentence_subtitles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成配音失败: {str(e)}")


@router.post("/media/video-info")
async def get_video_info_api(
    file_path: str = Form(...),
    user: User = Depends(get_current_user)
):
    """获取视频信息"""
    from app.services.video_service import get_video_info
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    try:
        info = get_video_info(file_path)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取视频信息失败: {str(e)}")


@router.post("/media/trim-video")
async def trim_video_api(
    request: VideoTrimRequest,
    user: User = Depends(get_current_user)
):
    """裁剪视频片段"""
    from app.services.video_service import trim_video, VideoTrimError
    
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    try:
        # 生成输出路径
        output_path = f"{settings.UPLOAD_DIR}/videos/{user.id}/trimmed_{uuid.uuid4()}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 裁剪视频
        result = trim_video(
            input_path=request.file_path,
            output_path=output_path,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        result_path = result["output_path"]
        
        # 返回裁剪后的视频信息
        from app.services.video_service import get_video_info
        info = get_video_info(result_path)
        
        # 生成预览 URL
        relative_path = result_path.replace(settings.UPLOAD_DIR + "/", "")
        preview_url = f"{settings.API_BASE_URL}/static/uploads/{relative_path}"
        
        return {
            "file_path": result_path,
            "preview_url": preview_url,
            "duration": info["duration"],
            "width": info["width"],
            "height": info["height"],
            "expected_duration": result["expected_duration"],
            "actual_duration": result["actual_duration"],
            "precision_error": result["precision_error"]
        }
    except VideoTrimError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"裁剪视频失败: {str(e)}")


@router.post("/media/thumbnails")
async def get_video_thumbnails_api(
    file_path: str = Form(...),
    count: int = Form(10),
    user: User = Depends(get_current_user)
):
    """提取视频缩略图"""
    from app.services.video_service import extract_video_thumbnails
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    try:
        output_dir = f"{settings.UPLOAD_DIR}/thumbnails/{user.id}/{uuid.uuid4()}"
        thumbnails = extract_video_thumbnails(file_path, output_dir, count)
        
        # 转换为 URL
        result = []
        for thumb in thumbnails:
            relative_path = thumb["path"].replace(settings.UPLOAD_DIR + "/", "")
            result.append({
                "url": f"{settings.API_BASE_URL}/static/uploads/{relative_path}",
                "time": thumb["time"]
            })
        
        return {"thumbnails": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取缩略图失败: {str(e)}")


@router.post("/tts/sync-voices")
def sync_tts_voices(db: Session = Depends(get_db)):
    """同步 Edge TTS 音色到数据库"""
    try:
        count = sync_voices_to_db(db)
        return {"message": f"成功同步 {count} 个新音色"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
