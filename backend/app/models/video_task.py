from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class VideoTask(Base):
    """视频混剪任务"""
    __tablename__ = "ipl_video_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    celery_task_id = Column(String(64), index=True)
    user_id = Column(BigInteger, ForeignKey("ipl_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文案配置
    topic = Column(String(500))  # 视频主题
    script = Column(Text)  # 视频文案/脚本
    script_language = Column(String(10), default="zh")  # 文案语言
    
    # 配音配置
    voice_language = Column(String(10), default="zh")  # 配音语言
    voice_name = Column(String(100))  # 配音音色
    voice_speed = Column(String(20), default="normal")  # 语速
    voice_audio_url = Column(String(500))  # 生成的配音文件
    
    # 背景音乐配置
    bgm_enabled = Column(Integer, default=0)  # 是否启用BGM
    bgm_path = Column(String(500))  # BGM文件路径
    bgm_volume = Column(Float, default=0.3)  # BGM音量 0-1
    bgm_fade_in = Column(Float, default=0)  # BGM淡入时长(秒) 0-5
    bgm_fade_out = Column(Float, default=0)  # BGM淡出时长(秒) 0-5
    
    # 视频配置
    video_resolution = Column(String(10), default="1080p")  # 分辨率: 480p/720p/1080p/2k/4k
    video_layout = Column(String(10), default="9:16")  # 布局比例: 9:16/3:4/1:1/4:3/16:9/21:9
    video_fps = Column(Integer, default=30)  # 帧率: 24/25/30/50/60
    platform_preset = Column(String(50))  # 平台预设: douyin/kuaishou/xiaohongshu/bilibili/youtube等
    fit_mode = Column(String(20), default="crop")  # 素材适配模式: crop/fit/stretch
    clip_min_duration = Column(Float, default=3.0)  # 片段最小时长
    clip_max_duration = Column(Float, default=10.0)  # 片段最大时长
    
    # 素材配置
    use_local_videos = Column(Integer, default=0)  # 是否使用本地视频
    local_video_dir = Column(String(500))  # 本地视频目录
    
    # 转场配置
    transition_enabled = Column(Integer, default=1)  # 是否启用转场
    transition_type = Column(String(50), default="fade")  # 转场类型
    transition_effect = Column(String(50), default="fade")  # 转场效果
    transition_duration = Column(Float, default=1.0)  # 转场时长
    
    # 字幕配置
    subtitle_enabled = Column(Integer, default=1)  # 是否启用字幕
    subtitle_font = Column(String(100), default="SimHei")  # 字体
    subtitle_size = Column(Integer, default=48)  # 字号
    subtitle_color = Column(String(20), default="#FFFFFF")  # 字体颜色
    subtitle_stroke_color = Column(String(20), default="#000000")  # 描边颜色
    subtitle_stroke_width = Column(Float, default=2.0)  # 描边宽度
    subtitle_position = Column(String(50), default="bottom")  # 位置
    subtitle_line_spacing = Column(Integer, default=2)  # 行距
    
    # 输出配置
    output_video_url = Column(String(500))  # 输出视频路径
    output_duration = Column(Float)  # 视频时长
    output_quality = Column(String(20), default="high")  # 输出质量: low/medium/high/ultra
    
    # 特效配置
    effect_type = Column(String(50))  # 动效类型: ken_burns/shake/zoom_in/zoom_out/pan_left/pan_right等
    color_filter = Column(String(50), default="none")  # 颜色滤镜: none/grayscale/vintage/warm/cool/high_contrast/soft
    brightness = Column(Float, default=1.0)  # 亮度 0.5-2.0
    contrast = Column(Float, default=1.0)  # 对比度 0.5-2.0
    saturation = Column(Float, default=1.0)  # 饱和度 0-2.0
    
    # 任务状态
    status = Column(Integer, default=0)  # 0-待处理 1-处理中 2-完成 3-失败
    progress = Column(Integer, default=0)  # 进度 0-100
    progress_message = Column(String(200))  # 进度消息
    error_message = Column(Text)  # 错误信息
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="video_tasks")
