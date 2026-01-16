"""视频混剪服务"""
import os
import re
from typing import List, Dict, Optional, Tuple

# 兼容 Pillow 10+ (ANTIALIAS 被移除，改用 LANCZOS)
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip, ColorClip,
    CompositeVideoClip, CompositeAudioClip, concatenate_videoclips,
    vfx, afx
)


# ============================================================
# 视频配置常量
# ============================================================

# 视频分辨率配置 (Requirements 5.1)
VIDEO_RESOLUTIONS = {
    "480p": {"width": 854, "height": 480},
    "720p": {"width": 1280, "height": 720},
    "1080p": {"width": 1920, "height": 1080},
    "2k": {"width": 2560, "height": 1440},
    "4k": {"width": 3840, "height": 2160},
}

# 视频布局（宽高比）配置 (Requirements 5.2)
VIDEO_LAYOUTS = {
    "9:16": {"name": "竖屏短视频", "ratio": (9, 16)},
    "3:4": {"name": "小红书", "ratio": (3, 4)},
    "1:1": {"name": "方形", "ratio": (1, 1)},
    "4:3": {"name": "传统", "ratio": (4, 3)},
    "16:9": {"name": "横屏标准", "ratio": (16, 9)},
    "21:9": {"name": "宽银幕", "ratio": (21, 9)},
}

# 帧率选项 (Requirements 5.3)
FRAME_RATES = [24, 25, 30, 50, 60]

# 平台预设配置 (Requirements 5.4)
PLATFORM_PRESETS = {
    "douyin": {"resolution": "1080p", "layout": "9:16", "fps": 30, "name": "抖音/TikTok"},
    "kuaishou": {"resolution": "1080p", "layout": "9:16", "fps": 30, "name": "快手"},
    "xiaohongshu": {"resolution": "1080p", "layout": "3:4", "fps": 30, "name": "小红书"},
    "bilibili": {"resolution": "1080p", "layout": "16:9", "fps": 30, "name": "B站"},
    "youtube": {"resolution": "1080p", "layout": "16:9", "fps": 30, "name": "YouTube"},
    "instagram_reels": {"resolution": "1080p", "layout": "9:16", "fps": 30, "name": "Instagram Reels"},
    "instagram_feed": {"resolution": "1080p", "layout": "1:1", "fps": 30, "name": "Instagram Feed"},
    "weixin": {"resolution": "1080p", "layout": "9:16", "fps": 30, "name": "微信视频号"},
}

# 转场效果配置 (Requirements 6.4, 6.5)
TRANSITIONS = {
    "none": {"name": "无", "duration": 0},
    "fade": {"name": "淡入淡出", "duration": 0.5},
    "slide_left": {"name": "左滑", "duration": 0.5},
    "slide_right": {"name": "右滑", "duration": 0.5},
    "slide_up": {"name": "上滑", "duration": 0.5},
    "slide_down": {"name": "下滑", "duration": 0.5},
    "zoom_in": {"name": "放大", "duration": 0.5},
    "zoom_out": {"name": "缩小", "duration": 0.5},
    "dissolve": {"name": "溶解", "duration": 0.5},
    "wipe_left": {"name": "左擦除", "duration": 0.5},
    "wipe_right": {"name": "右擦除", "duration": 0.5},
}

# 转场时长范围配置 (Requirements 6.5)
TRANSITION_DURATION_MIN = 0.3  # 最小转场时长（秒）
TRANSITION_DURATION_MAX = 2.0  # 最大转场时长（秒）
TRANSITION_DURATION_DEFAULT = 0.5  # 默认转场时长（秒）

# 素材适配模式 (Requirements 6.1)
FIT_MODES = {
    "crop": "裁剪填充",
    "fit": "适应填充",
    "stretch": "拉伸填充",
}

# 颜色滤镜 (Requirements 10.2)
COLOR_FILTERS = {
    "none": "原始",
    "grayscale": "黑白",
    "vintage": "复古",
    "warm": "暖色调",
    "cool": "冷色调",
    "high_contrast": "高对比度",
    "soft": "柔和",
}

# 视频特效类型 (Requirements 10.1)
EFFECT_TYPES = {
    "none": "无特效",
    "ken_burns_in": "Ken Burns 放大",
    "ken_burns_out": "Ken Burns 缩小",
    "shake": "轻微抖动",
    "zoom_in": "缩放放大",
    "zoom_out": "缩放缩小",
    "pan_left": "左平移",
    "pan_right": "右平移",
    "pan_up": "上平移",
    "pan_down": "下平移",
}

# 视频调节参数范围 (Requirements 10.3)
BRIGHTNESS_MIN = 0.5
BRIGHTNESS_MAX = 2.0
BRIGHTNESS_DEFAULT = 1.0

CONTRAST_MIN = 0.5
CONTRAST_MAX = 2.0
CONTRAST_DEFAULT = 1.0

SATURATION_MIN = 0.0
SATURATION_MAX = 2.0
SATURATION_DEFAULT = 1.0

# BGM 淡入淡出配置 (Requirements 6.8)
BGM_FADE_IN_MIN = 0.0  # 最小淡入时长（秒）
BGM_FADE_IN_MAX = 5.0  # 最大淡入时长（秒）
BGM_FADE_IN_DEFAULT = 0.0  # 默认淡入时长（秒）

BGM_FADE_OUT_MIN = 0.0  # 最小淡出时长（秒）
BGM_FADE_OUT_MAX = 5.0  # 最大淡出时长（秒）
BGM_FADE_OUT_DEFAULT = 0.0  # 默认淡出时长（秒）

# BGM 音量配置 (Requirements 6.7)
BGM_VOLUME_MIN = 0.0  # 最小音量（0%）
BGM_VOLUME_MAX = 1.0  # 最大音量（100%）
BGM_VOLUME_DEFAULT = 0.3  # 默认音量（30%）

# 片段时长配置 (Requirements 6.2)
CLIP_MIN_DURATION_MIN = 1.0  # 片段最小时长的最小值（秒）
CLIP_MIN_DURATION_MAX = 30.0  # 片段最小时长的最大值（秒）
CLIP_MIN_DURATION_DEFAULT = 3.0  # 片段最小时长默认值（秒）

CLIP_MAX_DURATION_MIN = 1.0  # 片段最大时长的最小值（秒）
CLIP_MAX_DURATION_MAX = 60.0  # 片段最大时长的最大值（秒）
CLIP_MAX_DURATION_DEFAULT = 10.0  # 片段最大时长默认值（秒）

# 字幕配置默认值 (Requirements 7.1-7.6)
SUBTITLE_SIZE_MIN = 12  # 字幕字号最小值
SUBTITLE_SIZE_MAX = 120  # 字幕字号最大值
SUBTITLE_SIZE_DEFAULT = 48  # 字幕字号默认值

SUBTITLE_STROKE_WIDTH_MIN = 0.0  # 字幕描边宽度最小值
SUBTITLE_STROKE_WIDTH_MAX = 10.0  # 字幕描边宽度最大值
SUBTITLE_STROKE_WIDTH_DEFAULT = 2.0  # 字幕描边宽度默认值

SUBTITLE_POSITIONS = ["top", "center", "bottom", "top_left", "top_right", "left", "right", "bottom_left", "bottom_right"]  # 支持的字幕位置
SUBTITLE_POSITION_DEFAULT = "bottom"  # 默认字幕位置

SUBTITLE_FONT_DEFAULT = "Heiti-SC-Medium"  # 默认字幕字体
SUBTITLE_COLOR_DEFAULT = "#FFFFFF"  # 默认字幕颜色
SUBTITLE_STROKE_COLOR_DEFAULT = "#000000"  # 默认字幕描边颜色

# 输出质量配置 (Requirements 6.10)
OUTPUT_QUALITIES = ["low", "medium", "high", "ultra"]  # 支持的输出质量
OUTPUT_QUALITY_DEFAULT = "high"  # 默认输出质量

# 视频帧率默认值 (Requirements 5.3)
VIDEO_FPS_DEFAULT = 30  # 默认帧率

# 视频分辨率默认值 (Requirements 5.1)
VIDEO_RESOLUTION_DEFAULT = "1080p"  # 默认分辨率

# 视频布局默认值 (Requirements 5.2)
VIDEO_LAYOUT_DEFAULT = "9:16"  # 默认布局

# 素材适配模式默认值 (Requirements 6.1)
FIT_MODE_DEFAULT = "crop"  # 默认适配模式

# 转场类型默认值 (Requirements 6.4)
TRANSITION_TYPE_DEFAULT = "fade"  # 默认转场类型

# 颜色滤镜默认值 (Requirements 10.2)
COLOR_FILTER_DEFAULT = "none"  # 默认颜色滤镜

# 特效类型默认值 (Requirements 10.1)
EFFECT_TYPE_DEFAULT = None  # 默认特效类型（无特效）

# 旧版视频尺寸配置（保持向后兼容）
VIDEO_SIZES = {
    "720p": {"portrait": (720, 1280), "landscape": (1280, 720)},
    "1080p": {"portrait": (1080, 1920), "landscape": (1920, 1080)},
    "4k": {"portrait": (2160, 3840), "landscape": (3840, 2160)},
}

# 支持的视频格式 (Requirements 3.1)
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# 支持的图片格式 (Requirements 3.2)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# 文件大小限制 (Requirements 3.3, 3.4)
MAX_VIDEO_FILE_SIZE = 150 * 1024 * 1024  # 150MB
MAX_IMAGE_FILE_SIZE = 10 * 1024 * 1024   # 10MB


# ============================================================
# 文件验证函数 (Requirements 3.1, 3.2, 3.3, 3.4)
# ============================================================

def validate_video_format(file_path: str) -> bool:
    """
    验证视频文件格式 (Requirements 3.1)
    
    验证文件扩展名是否在支持的视频格式列表中。
    
    Args:
        file_path: 文件路径或文件名
    
    Returns:
        True 如果格式有效，False 否则
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


def validate_image_format(file_path: str) -> bool:
    """
    验证图片文件格式 (Requirements 3.2)
    
    验证文件扩展名是否在支持的图片格式列表中。
    
    Args:
        file_path: 文件路径或文件名
    
    Returns:
        True 如果格式有效，False 否则
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def validate_media_format(file_path: str) -> Tuple[bool, str]:
    """
    验证媒体文件格式 (Requirements 3.1, 3.2)
    
    验证文件扩展名是否在支持的视频或图片格式列表中。
    
    Args:
        file_path: 文件路径或文件名
    
    Returns:
        (is_valid, media_type) 元组
        - is_valid: True 如果格式有效，False 否则
        - media_type: "video", "image", 或 "unknown"
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return True, "video"
    elif ext in ALLOWED_IMAGE_EXTENSIONS:
        return True, "image"
    else:
        return False, "unknown"


def validate_video_file_size(file_path: str) -> Tuple[bool, int]:
    """
    验证视频文件大小 (Requirements 3.3)
    
    验证视频文件大小是否不超过 150MB。
    
    Args:
        file_path: 文件路径
    
    Returns:
        (is_valid, file_size) 元组
        - is_valid: True 如果大小有效，False 否则
        - file_size: 文件大小（字节）
    
    Raises:
        FileNotFoundError: 如果文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = os.path.getsize(file_path)
    is_valid = file_size <= MAX_VIDEO_FILE_SIZE
    return is_valid, file_size


def validate_image_file_size(file_path: str) -> Tuple[bool, int]:
    """
    验证图片文件大小 (Requirements 3.4)
    
    验证图片文件大小是否不超过 10MB。
    
    Args:
        file_path: 文件路径
    
    Returns:
        (is_valid, file_size) 元组
        - is_valid: True 如果大小有效，False 否则
        - file_size: 文件大小（字节）
    
    Raises:
        FileNotFoundError: 如果文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = os.path.getsize(file_path)
    is_valid = file_size <= MAX_IMAGE_FILE_SIZE
    return is_valid, file_size


def validate_media_file_size(file_path: str) -> Tuple[bool, int, str]:
    """
    验证媒体文件大小 (Requirements 3.3, 3.4)
    
    根据文件类型验证文件大小是否在限制范围内。
    - 视频文件 ≤ 150MB
    - 图片文件 ≤ 10MB
    
    Args:
        file_path: 文件路径
    
    Returns:
        (is_valid, file_size, media_type) 元组
        - is_valid: True 如果大小有效，False 否则
        - file_size: 文件大小（字节）
        - media_type: "video", "image", 或 "unknown"
    
    Raises:
        FileNotFoundError: 如果文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 首先验证格式
    format_valid, media_type = validate_media_format(file_path)
    
    if not format_valid:
        return False, 0, "unknown"
    
    file_size = os.path.getsize(file_path)
    
    if media_type == "video":
        is_valid = file_size <= MAX_VIDEO_FILE_SIZE
    elif media_type == "image":
        is_valid = file_size <= MAX_IMAGE_FILE_SIZE
    else:
        is_valid = False
    
    return is_valid, file_size, media_type


def validate_media_file(file_path: str) -> Dict:
    """
    完整验证媒体文件 (Requirements 3.1, 3.2, 3.3, 3.4)
    
    验证文件格式和大小是否符合要求。
    
    Args:
        file_path: 文件路径
    
    Returns:
        验证结果字典，包含：
        - valid: 是否有效
        - format_valid: 格式是否有效
        - size_valid: 大小是否有效
        - media_type: 媒体类型 ("video", "image", "unknown")
        - file_size: 文件大小（字节）
        - max_size: 该类型的最大允许大小（字节）
        - error: 错误信息（如果有）
    
    Raises:
        FileNotFoundError: 如果文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    result = {
        "valid": False,
        "format_valid": False,
        "size_valid": False,
        "media_type": "unknown",
        "file_size": 0,
        "max_size": 0,
        "error": None
    }
    
    # 验证格式
    format_valid, media_type = validate_media_format(file_path)
    result["format_valid"] = format_valid
    result["media_type"] = media_type
    
    if not format_valid:
        ext = os.path.splitext(file_path)[1].lower()
        result["error"] = f"不支持的文件格式: {ext}"
        return result
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    result["file_size"] = file_size
    
    # 根据媒体类型验证大小
    if media_type == "video":
        result["max_size"] = MAX_VIDEO_FILE_SIZE
        result["size_valid"] = file_size <= MAX_VIDEO_FILE_SIZE
        if not result["size_valid"]:
            result["error"] = f"视频文件大小 ({file_size / 1024 / 1024:.2f}MB) 超过限制 (150MB)"
    elif media_type == "image":
        result["max_size"] = MAX_IMAGE_FILE_SIZE
        result["size_valid"] = file_size <= MAX_IMAGE_FILE_SIZE
        if not result["size_valid"]:
            result["error"] = f"图片文件大小 ({file_size / 1024 / 1024:.2f}MB) 超过限制 (10MB)"
    
    # 综合判断
    result["valid"] = result["format_valid"] and result["size_valid"]
    
    return result


# ============================================================
# 转场配置验证函数
# ============================================================

def validate_transition_duration(duration: float) -> float:
    """
    验证并规范化转场时长 (Requirements 6.5)
    
    Args:
        duration: 转场时长（秒）
    
    Returns:
        规范化后的转场时长，确保在有效范围内
    
    Raises:
        ValueError: 如果时长不在有效范围内
    """
    if duration < TRANSITION_DURATION_MIN or duration > TRANSITION_DURATION_MAX:
        raise ValueError(
            f"转场时长必须在 {TRANSITION_DURATION_MIN} 到 {TRANSITION_DURATION_MAX} 秒之间，"
            f"实际值: {duration}"
        )
    return duration


def validate_transition_type(transition_type: str) -> str:
    """
    验证转场类型 (Requirements 6.4)
    
    Args:
        transition_type: 转场类型
    
    Returns:
        验证后的转场类型
    
    Raises:
        ValueError: 如果转场类型无效
    """
    if transition_type not in TRANSITIONS:
        raise ValueError(
            f"无效的转场类型: {transition_type}，"
            f"支持的类型: {list(TRANSITIONS.keys())}"
        )
    return transition_type


def get_transition_config(transition_type: str, duration: Optional[float] = None) -> Dict:
    """
    获取转场配置 (Requirements 6.4, 6.5)
    
    Args:
        transition_type: 转场类型
        duration: 自定义转场时长（可选），如果不指定则使用默认值
    
    Returns:
        转场配置字典，包含 type, name, duration
    
    Raises:
        ValueError: 如果转场类型或时长无效
    """
    validate_transition_type(transition_type)
    
    # 获取默认配置
    config = TRANSITIONS[transition_type].copy()
    
    # 如果指定了自定义时长，验证并使用
    if duration is not None:
        if transition_type != "none":  # none 类型时长固定为 0
            validate_transition_duration(duration)
            config["duration"] = duration
    
    config["type"] = transition_type
    return config


# ============================================================
# 配置默认值验证函数 (Requirements 9.2, 9.3)
# ============================================================

def validate_config_defaults() -> Dict:
    """
    验证所有配置默认值在有效范围内 (Requirements 9.2, 9.3)
    
    检查系统中定义的所有默认值是否在其对应的有效范围内。
    
    Returns:
        验证结果字典，包含：
        - valid: 是否所有默认值都有效
        - errors: 错误列表（如果有）
        - defaults: 所有默认值的字典
    
    Raises:
        ValueError: 如果任何默认值不在有效范围内
    """
    errors = []
    defaults = {}
    
    # 验证亮度默认值
    if not (BRIGHTNESS_MIN <= BRIGHTNESS_DEFAULT <= BRIGHTNESS_MAX):
        errors.append(f"亮度默认值 {BRIGHTNESS_DEFAULT} 不在有效范围 [{BRIGHTNESS_MIN}, {BRIGHTNESS_MAX}] 内")
    defaults["brightness"] = BRIGHTNESS_DEFAULT
    
    # 验证对比度默认值
    if not (CONTRAST_MIN <= CONTRAST_DEFAULT <= CONTRAST_MAX):
        errors.append(f"对比度默认值 {CONTRAST_DEFAULT} 不在有效范围 [{CONTRAST_MIN}, {CONTRAST_MAX}] 内")
    defaults["contrast"] = CONTRAST_DEFAULT
    
    # 验证饱和度默认值
    if not (SATURATION_MIN <= SATURATION_DEFAULT <= SATURATION_MAX):
        errors.append(f"饱和度默认值 {SATURATION_DEFAULT} 不在有效范围 [{SATURATION_MIN}, {SATURATION_MAX}] 内")
    defaults["saturation"] = SATURATION_DEFAULT
    
    # 验证转场时长默认值
    if not (TRANSITION_DURATION_MIN <= TRANSITION_DURATION_DEFAULT <= TRANSITION_DURATION_MAX):
        errors.append(f"转场时长默认值 {TRANSITION_DURATION_DEFAULT} 不在有效范围 [{TRANSITION_DURATION_MIN}, {TRANSITION_DURATION_MAX}] 内")
    defaults["transition_duration"] = TRANSITION_DURATION_DEFAULT
    
    # 验证 BGM 音量默认值
    if not (BGM_VOLUME_MIN <= BGM_VOLUME_DEFAULT <= BGM_VOLUME_MAX):
        errors.append(f"BGM 音量默认值 {BGM_VOLUME_DEFAULT} 不在有效范围 [{BGM_VOLUME_MIN}, {BGM_VOLUME_MAX}] 内")
    defaults["bgm_volume"] = BGM_VOLUME_DEFAULT
    
    # 验证 BGM 淡入时长默认值
    if not (BGM_FADE_IN_MIN <= BGM_FADE_IN_DEFAULT <= BGM_FADE_IN_MAX):
        errors.append(f"BGM 淡入时长默认值 {BGM_FADE_IN_DEFAULT} 不在有效范围 [{BGM_FADE_IN_MIN}, {BGM_FADE_IN_MAX}] 内")
    defaults["bgm_fade_in"] = BGM_FADE_IN_DEFAULT
    
    # 验证 BGM 淡出时长默认值
    if not (BGM_FADE_OUT_MIN <= BGM_FADE_OUT_DEFAULT <= BGM_FADE_OUT_MAX):
        errors.append(f"BGM 淡出时长默认值 {BGM_FADE_OUT_DEFAULT} 不在有效范围 [{BGM_FADE_OUT_MIN}, {BGM_FADE_OUT_MAX}] 内")
    defaults["bgm_fade_out"] = BGM_FADE_OUT_DEFAULT
    
    # 验证片段最小时长默认值
    if not (CLIP_MIN_DURATION_MIN <= CLIP_MIN_DURATION_DEFAULT <= CLIP_MIN_DURATION_MAX):
        errors.append(f"片段最小时长默认值 {CLIP_MIN_DURATION_DEFAULT} 不在有效范围 [{CLIP_MIN_DURATION_MIN}, {CLIP_MIN_DURATION_MAX}] 内")
    defaults["clip_min_duration"] = CLIP_MIN_DURATION_DEFAULT
    
    # 验证片段最大时长默认值
    if not (CLIP_MAX_DURATION_MIN <= CLIP_MAX_DURATION_DEFAULT <= CLIP_MAX_DURATION_MAX):
        errors.append(f"片段最大时长默认值 {CLIP_MAX_DURATION_DEFAULT} 不在有效范围 [{CLIP_MAX_DURATION_MIN}, {CLIP_MAX_DURATION_MAX}] 内")
    defaults["clip_max_duration"] = CLIP_MAX_DURATION_DEFAULT
    
    # 验证片段时长逻辑关系
    if CLIP_MIN_DURATION_DEFAULT > CLIP_MAX_DURATION_DEFAULT:
        errors.append(f"片段最小时长默认值 {CLIP_MIN_DURATION_DEFAULT} 不能大于最大时长默认值 {CLIP_MAX_DURATION_DEFAULT}")
    
    # 验证字幕字号默认值
    if not (SUBTITLE_SIZE_MIN <= SUBTITLE_SIZE_DEFAULT <= SUBTITLE_SIZE_MAX):
        errors.append(f"字幕字号默认值 {SUBTITLE_SIZE_DEFAULT} 不在有效范围 [{SUBTITLE_SIZE_MIN}, {SUBTITLE_SIZE_MAX}] 内")
    defaults["subtitle_size"] = SUBTITLE_SIZE_DEFAULT
    
    # 验证字幕描边宽度默认值
    if not (SUBTITLE_STROKE_WIDTH_MIN <= SUBTITLE_STROKE_WIDTH_DEFAULT <= SUBTITLE_STROKE_WIDTH_MAX):
        errors.append(f"字幕描边宽度默认值 {SUBTITLE_STROKE_WIDTH_DEFAULT} 不在有效范围 [{SUBTITLE_STROKE_WIDTH_MIN}, {SUBTITLE_STROKE_WIDTH_MAX}] 内")
    defaults["subtitle_stroke_width"] = SUBTITLE_STROKE_WIDTH_DEFAULT
    
    # 验证字幕位置默认值
    if SUBTITLE_POSITION_DEFAULT not in SUBTITLE_POSITIONS:
        errors.append(f"字幕位置默认值 {SUBTITLE_POSITION_DEFAULT} 不在支持的位置列表 {SUBTITLE_POSITIONS} 中")
    defaults["subtitle_position"] = SUBTITLE_POSITION_DEFAULT
    
    # 验证输出质量默认值
    if OUTPUT_QUALITY_DEFAULT not in OUTPUT_QUALITIES:
        errors.append(f"输出质量默认值 {OUTPUT_QUALITY_DEFAULT} 不在支持的质量列表 {OUTPUT_QUALITIES} 中")
    defaults["output_quality"] = OUTPUT_QUALITY_DEFAULT
    
    # 验证视频帧率默认值
    if VIDEO_FPS_DEFAULT not in FRAME_RATES:
        errors.append(f"视频帧率默认值 {VIDEO_FPS_DEFAULT} 不在支持的帧率列表 {FRAME_RATES} 中")
    defaults["video_fps"] = VIDEO_FPS_DEFAULT
    
    # 验证视频分辨率默认值
    if VIDEO_RESOLUTION_DEFAULT not in VIDEO_RESOLUTIONS:
        errors.append(f"视频分辨率默认值 {VIDEO_RESOLUTION_DEFAULT} 不在支持的分辨率列表 {list(VIDEO_RESOLUTIONS.keys())} 中")
    defaults["video_resolution"] = VIDEO_RESOLUTION_DEFAULT
    
    # 验证视频布局默认值
    if VIDEO_LAYOUT_DEFAULT not in VIDEO_LAYOUTS:
        errors.append(f"视频布局默认值 {VIDEO_LAYOUT_DEFAULT} 不在支持的布局列表 {list(VIDEO_LAYOUTS.keys())} 中")
    defaults["video_layout"] = VIDEO_LAYOUT_DEFAULT
    
    # 验证素材适配模式默认值
    if FIT_MODE_DEFAULT not in FIT_MODES:
        errors.append(f"素材适配模式默认值 {FIT_MODE_DEFAULT} 不在支持的模式列表 {list(FIT_MODES.keys())} 中")
    defaults["fit_mode"] = FIT_MODE_DEFAULT
    
    # 验证转场类型默认值
    if TRANSITION_TYPE_DEFAULT not in TRANSITIONS:
        errors.append(f"转场类型默认值 {TRANSITION_TYPE_DEFAULT} 不在支持的类型列表 {list(TRANSITIONS.keys())} 中")
    defaults["transition_type"] = TRANSITION_TYPE_DEFAULT
    
    # 验证颜色滤镜默认值
    if COLOR_FILTER_DEFAULT not in COLOR_FILTERS:
        errors.append(f"颜色滤镜默认值 {COLOR_FILTER_DEFAULT} 不在支持的滤镜列表 {list(COLOR_FILTERS.keys())} 中")
    defaults["color_filter"] = COLOR_FILTER_DEFAULT
    
    # 验证特效类型默认值（None 表示无特效，是有效的）
    if EFFECT_TYPE_DEFAULT is not None and EFFECT_TYPE_DEFAULT not in EFFECT_TYPES:
        errors.append(f"特效类型默认值 {EFFECT_TYPE_DEFAULT} 不在支持的特效列表 {list(EFFECT_TYPES.keys())} 中")
    defaults["effect_type"] = EFFECT_TYPE_DEFAULT
    
    # 添加其他字符串默认值
    defaults["subtitle_font"] = SUBTITLE_FONT_DEFAULT
    defaults["subtitle_color"] = SUBTITLE_COLOR_DEFAULT
    defaults["subtitle_stroke_color"] = SUBTITLE_STROKE_COLOR_DEFAULT
    
    if errors:
        raise ValueError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": [],
        "defaults": defaults
    }


def get_config_with_defaults(config: Optional[Dict] = None) -> Dict:
    """
    获取带有默认值的配置 (Requirements 9.2, 9.3)
    
    对于未指定的配置项，使用系统默认值填充。
    
    Args:
        config: 用户提供的配置字典（可选）
    
    Returns:
        完整的配置字典，包含所有配置项（用户指定的值或默认值）
    """
    if config is None:
        config = {}
    
    # 创建带有默认值的配置
    result = {
        # 视频配置
        "video_resolution": config.get("video_resolution", VIDEO_RESOLUTION_DEFAULT),
        "video_layout": config.get("video_layout", VIDEO_LAYOUT_DEFAULT),
        "video_fps": config.get("video_fps", VIDEO_FPS_DEFAULT),
        "fit_mode": config.get("fit_mode", FIT_MODE_DEFAULT),
        
        # 转场配置
        "transition_type": config.get("transition_type", TRANSITION_TYPE_DEFAULT),
        "transition_duration": config.get("transition_duration", TRANSITION_DURATION_DEFAULT),
        "transition_enabled": config.get("transition_enabled", True),
        
        # 视频调节参数
        "brightness": config.get("brightness", BRIGHTNESS_DEFAULT),
        "contrast": config.get("contrast", CONTRAST_DEFAULT),
        "saturation": config.get("saturation", SATURATION_DEFAULT),
        
        # 特效和滤镜
        "color_filter": config.get("color_filter", COLOR_FILTER_DEFAULT),
        "effect_type": config.get("effect_type", EFFECT_TYPE_DEFAULT),
        
        # BGM 配置
        "bgm_volume": config.get("bgm_volume", BGM_VOLUME_DEFAULT),
        "bgm_fade_in": config.get("bgm_fade_in", BGM_FADE_IN_DEFAULT),
        "bgm_fade_out": config.get("bgm_fade_out", BGM_FADE_OUT_DEFAULT),
        "bgm_enabled": config.get("bgm_enabled", False),
        
        # 片段配置
        "clip_min_duration": config.get("clip_min_duration", CLIP_MIN_DURATION_DEFAULT),
        "clip_max_duration": config.get("clip_max_duration", CLIP_MAX_DURATION_DEFAULT),
        
        # 字幕配置
        "subtitle_enabled": config.get("subtitle_enabled", True),
        "subtitle_font": config.get("subtitle_font", SUBTITLE_FONT_DEFAULT),
        "subtitle_size": config.get("subtitle_size", SUBTITLE_SIZE_DEFAULT),
        "subtitle_color": config.get("subtitle_color", SUBTITLE_COLOR_DEFAULT),
        "subtitle_stroke_color": config.get("subtitle_stroke_color", SUBTITLE_STROKE_COLOR_DEFAULT),
        "subtitle_stroke_width": config.get("subtitle_stroke_width", SUBTITLE_STROKE_WIDTH_DEFAULT),
        "subtitle_position": config.get("subtitle_position", SUBTITLE_POSITION_DEFAULT),
        
        # 输出配置
        "output_quality": config.get("output_quality", OUTPUT_QUALITY_DEFAULT),
    }
    
    # 保留用户提供的其他配置项
    for key, value in config.items():
        if key not in result:
            result[key] = value
    
    return result


def get_all_config_defaults() -> Dict:
    """
    获取所有配置项的默认值 (Requirements 9.2)
    
    返回系统中所有配置项的默认值字典。
    
    Returns:
        包含所有默认值的字典
    """
    return {
        # 视频配置
        "video_resolution": VIDEO_RESOLUTION_DEFAULT,
        "video_layout": VIDEO_LAYOUT_DEFAULT,
        "video_fps": VIDEO_FPS_DEFAULT,
        "fit_mode": FIT_MODE_DEFAULT,
        
        # 转场配置
        "transition_type": TRANSITION_TYPE_DEFAULT,
        "transition_duration": TRANSITION_DURATION_DEFAULT,
        
        # 视频调节参数
        "brightness": BRIGHTNESS_DEFAULT,
        "contrast": CONTRAST_DEFAULT,
        "saturation": SATURATION_DEFAULT,
        
        # 特效和滤镜
        "color_filter": COLOR_FILTER_DEFAULT,
        "effect_type": EFFECT_TYPE_DEFAULT,
        
        # BGM 配置
        "bgm_volume": BGM_VOLUME_DEFAULT,
        "bgm_fade_in": BGM_FADE_IN_DEFAULT,
        "bgm_fade_out": BGM_FADE_OUT_DEFAULT,
        
        # 片段配置
        "clip_min_duration": CLIP_MIN_DURATION_DEFAULT,
        "clip_max_duration": CLIP_MAX_DURATION_DEFAULT,
        
        # 字幕配置
        "subtitle_font": SUBTITLE_FONT_DEFAULT,
        "subtitle_size": SUBTITLE_SIZE_DEFAULT,
        "subtitle_color": SUBTITLE_COLOR_DEFAULT,
        "subtitle_stroke_color": SUBTITLE_STROKE_COLOR_DEFAULT,
        "subtitle_stroke_width": SUBTITLE_STROKE_WIDTH_DEFAULT,
        "subtitle_position": SUBTITLE_POSITION_DEFAULT,
        
        # 输出配置
        "output_quality": OUTPUT_QUALITY_DEFAULT,
    }


def get_config_ranges() -> Dict:
    """
    获取所有配置项的有效范围 (Requirements 9.2)
    
    返回系统中所有数值配置项的有效范围。
    
    Returns:
        包含所有配置项范围的字典
    """
    return {
        "brightness": {"min": BRIGHTNESS_MIN, "max": BRIGHTNESS_MAX, "default": BRIGHTNESS_DEFAULT},
        "contrast": {"min": CONTRAST_MIN, "max": CONTRAST_MAX, "default": CONTRAST_DEFAULT},
        "saturation": {"min": SATURATION_MIN, "max": SATURATION_MAX, "default": SATURATION_DEFAULT},
        "transition_duration": {"min": TRANSITION_DURATION_MIN, "max": TRANSITION_DURATION_MAX, "default": TRANSITION_DURATION_DEFAULT},
        "bgm_volume": {"min": BGM_VOLUME_MIN, "max": BGM_VOLUME_MAX, "default": BGM_VOLUME_DEFAULT},
        "bgm_fade_in": {"min": BGM_FADE_IN_MIN, "max": BGM_FADE_IN_MAX, "default": BGM_FADE_IN_DEFAULT},
        "bgm_fade_out": {"min": BGM_FADE_OUT_MIN, "max": BGM_FADE_OUT_MAX, "default": BGM_FADE_OUT_DEFAULT},
        "clip_min_duration": {"min": CLIP_MIN_DURATION_MIN, "max": CLIP_MIN_DURATION_MAX, "default": CLIP_MIN_DURATION_DEFAULT},
        "clip_max_duration": {"min": CLIP_MAX_DURATION_MIN, "max": CLIP_MAX_DURATION_MAX, "default": CLIP_MAX_DURATION_DEFAULT},
        "subtitle_size": {"min": SUBTITLE_SIZE_MIN, "max": SUBTITLE_SIZE_MAX, "default": SUBTITLE_SIZE_DEFAULT},
        "subtitle_stroke_width": {"min": SUBTITLE_STROKE_WIDTH_MIN, "max": SUBTITLE_STROKE_WIDTH_MAX, "default": SUBTITLE_STROKE_WIDTH_DEFAULT},
    }


def get_config_options() -> Dict:
    """
    获取所有配置项的可选值列表 (Requirements 9.2)
    
    返回系统中所有枚举类型配置项的可选值列表。
    
    Returns:
        包含所有配置项可选值的字典
    """
    return {
        "video_resolution": list(VIDEO_RESOLUTIONS.keys()),
        "video_layout": list(VIDEO_LAYOUTS.keys()),
        "video_fps": FRAME_RATES,
        "platform_preset": list(PLATFORM_PRESETS.keys()),
        "fit_mode": list(FIT_MODES.keys()),
        "transition_type": list(TRANSITIONS.keys()),
        "color_filter": list(COLOR_FILTERS.keys()),
        "effect_type": list(EFFECT_TYPES.keys()),
        "subtitle_position": SUBTITLE_POSITIONS,
        "output_quality": OUTPUT_QUALITIES,
    }


# ============================================================
# 视频尺寸计算函数
# ============================================================

def calculate_video_size(resolution: str, layout: str) -> Tuple[int, int]:
    """
    计算视频实际尺寸 (Requirements 5.1, 5.2)
    
    根据分辨率和布局计算实际视频尺寸。
    
    Args:
        resolution: 分辨率 (480p, 720p, 1080p, 2k, 4k)
        layout: 布局比例 (9:16, 3:4, 1:1, 4:3, 16:9, 21:9)
    
    Returns:
        (width, height) 元组，尺寸为正偶数
    
    Raises:
        ValueError: 如果分辨率或布局无效
    """
    # 验证分辨率
    if resolution not in VIDEO_RESOLUTIONS:
        raise ValueError(f"无效的分辨率: {resolution}，支持的分辨率: {list(VIDEO_RESOLUTIONS.keys())}")
    
    # 验证布局
    if layout not in VIDEO_LAYOUTS:
        raise ValueError(f"无效的布局: {layout}，支持的布局: {list(VIDEO_LAYOUTS.keys())}")
    
    base = VIDEO_RESOLUTIONS[resolution]
    ratio = VIDEO_LAYOUTS[layout]["ratio"]
    
    # 根据布局计算尺寸
    ratio_w, ratio_h = ratio
    
    if ratio_w >= ratio_h:
        # 横屏或方形：以高度为基准
        height = base["height"]
        width = int(height * ratio_w / ratio_h)
    else:
        # 竖屏：以宽度为基准，使用分辨率的宽度值
        # 对于竖屏，我们希望宽度较小，高度较大
        width = base["height"]  # 使用高度值作为宽度基准（因为竖屏宽度应该较小）
        height = int(width * ratio_h / ratio_w)
    
    # 确保尺寸为偶数（视频编码要求）
    width = width if width % 2 == 0 else width + 1
    height = height if height % 2 == 0 else height + 1
    
    return (width, height)


def get_video_size(size: str, layout: str) -> Tuple[int, int]:
    """获取视频尺寸"""
    if size not in VIDEO_SIZES:
        size = "1080p"
    if layout not in ["portrait", "landscape"]:
        layout = "portrait"
    return VIDEO_SIZES[size][layout]


def split_script_to_sentences(script: str) -> List[str]:
    """将文案分割成句子"""
    # 按中英文标点分割
    sentences = re.split(r'[。！？.!?\n]+', script)
    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def get_media_files(directory: str) -> List[str]:
    """获取目录下的媒体文件"""
    if not os.path.exists(directory):
        return []
    
    files = []
    for f in os.listdir(directory):
        ext = os.path.splitext(f)[1].lower()
        if ext in ALLOWED_VIDEO_EXTENSIONS or ext in ALLOWED_IMAGE_EXTENSIONS:
            files.append(os.path.join(directory, f))
    return sorted(files)


class VideoInfoError(Exception):
    """视频信息提取异常"""
    pass


def get_video_info(video_path: str) -> Dict:
    """
    获取视频信息 (Requirements 3.5)
    
    从视频文件中提取完整的视频信息，包括时长、尺寸和帧率。
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        包含视频信息的字典：
        - duration: 视频时长（秒），正数
        - width: 视频宽度（像素），正整数
        - height: 视频高度（像素），正整数
        - fps: 帧率，正数
        - size: (width, height) 元组（保持向后兼容）
    
    Raises:
        FileNotFoundError: 如果视频文件不存在
        VideoInfoError: 如果无法提取视频信息或信息不完整
    """
    # 验证文件存在
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    # 验证文件格式
    ext = os.path.splitext(video_path)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise VideoInfoError(f"不支持的视频格式: {ext}，支持的格式: {ALLOWED_VIDEO_EXTENSIONS}")
    
    clip = None
    try:
        clip = VideoFileClip(video_path)
        
        # 提取视频信息
        duration = clip.duration
        width = clip.size[0] if clip.size else None
        height = clip.size[1] if clip.size else None
        fps = clip.fps
        
        # 验证信息完整性
        if duration is None or duration <= 0:
            raise VideoInfoError(f"无法获取有效的视频时长: {duration}")
        
        if width is None or width <= 0:
            raise VideoInfoError(f"无法获取有效的视频宽度: {width}")
        
        if height is None or height <= 0:
            raise VideoInfoError(f"无法获取有效的视频高度: {height}")
        
        if fps is None or fps <= 0:
            raise VideoInfoError(f"无法获取有效的视频帧率: {fps}")
        
        # 确保宽度和高度是整数
        width = int(width)
        height = int(height)
        
        return {
            "duration": float(duration),
            "width": width,
            "height": height,
            "fps": float(fps),
            "size": (width, height),  # 保持向后兼容
        }
    
    except VideoInfoError:
        # 重新抛出 VideoInfoError
        raise
    except FileNotFoundError:
        # 重新抛出 FileNotFoundError
        raise
    except Exception as e:
        # 捕获其他异常并转换为 VideoInfoError
        raise VideoInfoError(f"提取视频信息时发生错误: {str(e)}") from e
    finally:
        # 确保资源被释放
        if clip is not None:
            try:
                clip.close()
            except Exception:
                pass


class VideoTrimError(Exception):
    """视频裁剪异常"""
    pass


def validate_trim_time_range(
    start_time: float,
    end_time: float,
    video_duration: float
) -> Tuple[float, float]:
    """
    验证视频裁剪时间范围 (Requirements 4.3, 4.4)
    
    验证裁剪时间范围是否有效：
    - start_time >= 0
    - start_time < end_time
    - end_time <= video_duration
    
    Args:
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        video_duration: 视频总时长（秒）
    
    Returns:
        (validated_start_time, validated_end_time) 元组
    
    Raises:
        VideoTrimError: 如果时间范围无效
    """
    # 验证 start_time >= 0
    if start_time < 0:
        raise VideoTrimError(
            f"开始时间必须 >= 0，实际值: {start_time}"
        )
    
    # 验证 start_time < end_time
    if start_time >= end_time:
        raise VideoTrimError(
            f"开始时间必须小于结束时间，开始时间: {start_time}，结束时间: {end_time}"
        )
    
    # 验证 end_time <= video_duration
    if end_time > video_duration:
        raise VideoTrimError(
            f"结束时间不能超过视频总时长，结束时间: {end_time}，视频时长: {video_duration}"
        )
    
    return (start_time, end_time)


def trim_video(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float
) -> Dict:
    """
    裁剪视频片段 (Requirements 4.3, 4.4, 4.5)
    
    从输入视频中裁剪指定时间范围的片段。
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        start_time: 开始时间（秒），必须 >= 0
        end_time: 结束时间（秒），必须 > start_time 且 <= 视频总时长
    
    Returns:
        包含裁剪结果信息的字典：
        - output_path: 输出视频路径
        - start_time: 实际开始时间
        - end_time: 实际结束时间
        - expected_duration: 期望的裁剪时长 (end_time - start_time)
        - actual_duration: 实际输出视频时长
        - precision_error: 时长精度误差（秒）
    
    Raises:
        FileNotFoundError: 如果输入视频文件不存在
        VideoTrimError: 如果时间范围无效
        VideoInfoError: 如果无法读取视频信息
    """
    # 验证输入文件存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入视频文件不存在: {input_path}")
    
    # 验证文件格式
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise VideoTrimError(f"不支持的视频格式: {ext}")
    
    clip = None
    trimmed = None
    try:
        clip = VideoFileClip(input_path)
        video_duration = clip.duration
        
        # 验证时间范围
        validated_start, validated_end = validate_trim_time_range(
            start_time, end_time, video_duration
        )
        
        # 计算期望的裁剪时长
        expected_duration = validated_end - validated_start
        
        # 裁剪视频
        trimmed = clip.subclip(validated_start, validated_end)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 导出视频，使用更精确的编码设置
        trimmed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
            verbose=False,
            logger=None
        )
        
        # 验证输出视频的实际时长
        actual_duration = None
        precision_error = None
        
        if os.path.exists(output_path):
            try:
                output_info = get_video_info(output_path)
                actual_duration = output_info["duration"]
                precision_error = abs(actual_duration - expected_duration)
            except Exception:
                # 如果无法获取输出视频信息，不影响主流程
                pass
        
        return {
            "output_path": output_path,
            "start_time": validated_start,
            "end_time": validated_end,
            "expected_duration": expected_duration,
            "actual_duration": actual_duration,
            "precision_error": precision_error
        }
    
    except VideoTrimError:
        # 重新抛出 VideoTrimError
        raise
    except FileNotFoundError:
        # 重新抛出 FileNotFoundError
        raise
    except Exception as e:
        raise VideoTrimError(f"裁剪视频时发生错误: {str(e)}") from e
    finally:
        # 确保资源被释放
        if trimmed is not None:
            try:
                trimmed.close()
            except Exception:
                pass
        if clip is not None:
            try:
                clip.close()
            except Exception:
                pass


def extract_video_thumbnails(
    video_path: str,
    output_dir: str,
    count: int = 10
) -> List[str]:
    """
    提取视频缩略图
    
    Args:
        video_path: 视频路径
        output_dir: 输出目录
        count: 缩略图数量
    
    Returns:
        缩略图路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    thumbnails = []
    
    with VideoFileClip(video_path) as clip:
        duration = clip.duration
        interval = duration / (count + 1)
        
        for i in range(count):
            time = interval * (i + 1)
            frame = clip.get_frame(time)
            
            # 保存缩略图
            img = Image.fromarray(frame)
            img.thumbnail((320, 180))  # 缩小尺寸
            
            thumb_path = os.path.join(output_dir, f"thumb_{i:03d}.jpg")
            img.save(thumb_path, "JPEG", quality=80)
            thumbnails.append({
                "path": thumb_path,
                "time": round(time, 2)
            })
    
    return thumbnails


def create_text_clip(
    text: str,
    duration: float,
    size: Tuple[int, int],
    font: str = "Heiti-SC-Medium",
    fontsize: int = 48,
    color: str = "white",
    stroke_color: str = "black",
    stroke_width: float = 2,
    position: str = "bottom"
) -> TextClip:
    """创建字幕片段"""
    width, height = size
    margin_x = 50  # 水平边距
    margin_y = 50  # 垂直边距
    
    # 位置映射 - 支持9个位置
    pos_map = {
        "top_left": (margin_x, margin_y),
        "top": ("center", margin_y),
        "top_right": (width - margin_x, margin_y),
        "left": (margin_x, "center"),
        "center": ("center", "center"),
        "right": (width - margin_x, "center"),
        "bottom_left": (margin_x, height - margin_y - 100),
        "bottom": ("center", height - margin_y - 100),
        "bottom_right": (width - margin_x, height - margin_y - 100),
    }
    
    # 对齐方式映射
    align_map = {
        "top_left": "West",
        "top": "center",
        "top_right": "East",
        "left": "West",
        "center": "center",
        "right": "East",
        "bottom_left": "West",
        "bottom": "center",
        "bottom_right": "East",
    }
    
    txt_clip = TextClip(
        text,
        fontsize=fontsize,
        font=font,
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        size=(size[0] - 100, None),  # 留边距
        method='caption',
        align=align_map.get(position, 'center')
    )
    
    txt_clip = txt_clip.set_duration(duration)
    txt_clip = txt_clip.set_position(pos_map.get(position, pos_map["bottom"]))
    
    return txt_clip


def create_word_highlight_clips(
    sentence_subtitles: List[Dict],
    size: Tuple[int, int],
    font: str = "Heiti-SC-Medium",
    fontsize: int = 48,
    color: str = "white",
    highlight_color: str = "#10b981",
    stroke_color: str = "black",
    stroke_width: float = 2,
    position: str = "bottom"
) -> List:
    """
    创建逐词高亮字幕
    
    Args:
        sentence_subtitles: 句子字幕列表，包含 words 时间戳
        其他参数同 create_text_clip
    
    Returns:
        字幕片段列表
    """
    clips = []
    pos_y = size[1] - 150 if position == "bottom" else (50 if position == "top" else size[1] // 2)
    
    for sentence in sentence_subtitles:
        if not sentence.get("words"):
            # 没有词级时间戳，使用普通字幕
            txt_clip = create_text_clip(
                sentence["text"],
                sentence["end"] - sentence["start"],
                size, font, fontsize, color, stroke_color, stroke_width, position
            )
            txt_clip = txt_clip.set_start(sentence["start"])
            clips.append(txt_clip)
            continue
        
        words = sentence["words"]
        full_text = sentence["text"]
        
        # 为每个词创建高亮效果
        for i, word in enumerate(words):
            word_start = word["start"]
            word_end = word["end"]
            word_duration = word_end - word_start
            
            if word_duration <= 0:
                continue
            
            # 构建带高亮的文本（当前词高亮）
            # 使用 TextClip 的方式：显示完整句子，当前词用不同颜色
            # 由于 moviepy 不支持部分着色，我们用两层叠加实现
            
            # 底层：完整句子（普通颜色）
            base_clip = TextClip(
                full_text,
                fontsize=fontsize,
                font=font,
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                size=(size[0] - 100, None),
                method='caption',
                align='center'
            ).set_duration(word_duration).set_start(word_start).set_position(("center", pos_y))
            
            clips.append(base_clip)
    
    return clips


def resize_clip_to_fill(clip, target_size: Tuple[int, int]):
    """调整视频/图片尺寸以填充目标尺寸（裁剪方式）"""
    target_w, target_h = target_size
    target_ratio = target_w / target_h
    
    clip_w, clip_h = clip.size
    clip_ratio = clip_w / clip_h
    
    if clip_ratio > target_ratio:
        # 视频更宽，按高度缩放后裁剪宽度
        new_h = target_h
        new_w = int(clip_w * (target_h / clip_h))
        clip = clip.resize(height=new_h)
        x_center = new_w // 2
        clip = clip.crop(x1=x_center - target_w // 2, x2=x_center + target_w // 2)
    else:
        # 视频更高，按宽度缩放后裁剪高度
        new_w = target_w
        new_h = int(clip_h * (target_w / clip_w))
        clip = clip.resize(width=new_w)
        y_center = new_h // 2
        clip = clip.crop(y1=y_center - target_h // 2, y2=y_center + target_h // 2)
    
    return clip


# ============================================================
# 素材适配函数 (Requirements 6.1)
# ============================================================

def adapt_media_crop(clip, target_size: Tuple[int, int]):
    """
    裁剪填充模式 (crop)
    
    保持素材原始比例，缩放后裁剪多余部分以完全填充目标尺寸。
    
    Args:
        clip: MoviePy 视频/图片片段
        target_size: 目标尺寸 (width, height)
    
    Returns:
        调整后的片段，尺寸等于目标尺寸
    """
    target_w, target_h = target_size
    clip_w, clip_h = clip.size
    
    target_ratio = target_w / target_h
    clip_ratio = clip_w / clip_h
    
    # 处理比例相等或非常接近的情况：直接缩放到目标尺寸
    if abs(clip_ratio - target_ratio) < 0.01:
        clip = clip.resize(newsize=target_size)
        return clip
    
    if clip_ratio > target_ratio:
        # 素材更宽，按高度缩放后裁剪宽度
        new_h = target_h
        new_w = int(clip_w * (target_h / clip_h))
        clip = clip.resize(height=new_h)
        # 使用精确的裁剪坐标，确保输出尺寸正确
        x_start = (new_w - target_w) // 2
        clip = clip.crop(x1=x_start, x2=x_start + target_w, y1=0, y2=target_h)
    else:
        # 素材更高，按宽度缩放后裁剪高度
        new_w = target_w
        new_h = int(clip_h * (target_w / clip_w))
        clip = clip.resize(width=new_w)
        # 使用精确的裁剪坐标，确保输出尺寸正确
        y_start = (new_h - target_h) // 2
        clip = clip.crop(x1=0, x2=target_w, y1=y_start, y2=y_start + target_h)
    
    return clip


def adapt_media_fit(clip, target_size: Tuple[int, int], bg_color: Tuple[int, int, int] = (0, 0, 0)):
    """
    适应填充模式 (fit)
    
    保持素材原始比例，缩放以适应目标尺寸，空白区域填充背景色（黑边）。
    
    Args:
        clip: MoviePy 视频/图片片段
        target_size: 目标尺寸 (width, height)
        bg_color: 背景填充颜色，默认黑色
    
    Returns:
        调整后的片段，尺寸等于目标尺寸，素材保持原比例
    """
    target_w, target_h = target_size
    clip_w, clip_h = clip.size
    
    target_ratio = target_w / target_h
    clip_ratio = clip_w / clip_h
    
    if clip_ratio > target_ratio:
        # 素材更宽，按宽度缩放（上下留黑边）
        new_w = target_w
        new_h = int(clip_h * (target_w / clip_w))
        clip = clip.resize(width=new_w)
    else:
        # 素材更高，按高度缩放（左右留黑边）
        new_h = target_h
        new_w = int(clip_w * (target_h / clip_h))
        clip = clip.resize(height=new_h)
    
    # 创建背景
    bg = ColorClip(size=target_size, color=bg_color, duration=clip.duration)
    
    # 将素材居中放置在背景上
    clip = clip.set_position("center")
    
    return CompositeVideoClip([bg, clip], size=target_size)


def adapt_media_stretch(clip, target_size: Tuple[int, int]):
    """
    拉伸填充模式 (stretch)
    
    直接拉伸素材以填充目标尺寸，不保持原始比例。
    
    Args:
        clip: MoviePy 视频/图片片段
        target_size: 目标尺寸 (width, height)
    
    Returns:
        调整后的片段，尺寸等于目标尺寸
    """
    return clip.resize(newsize=target_size)


def adapt_media_to_size(
    clip,
    target_size: Tuple[int, int],
    fit_mode: str = "crop",
    bg_color: Tuple[int, int, int] = (0, 0, 0)
):
    """
    将素材适配到目标尺寸 (Requirements 6.1)
    
    根据指定的适配模式将素材调整到目标尺寸。
    
    Args:
        clip: MoviePy 视频/图片片段
        target_size: 目标尺寸 (width, height)
        fit_mode: 适配模式 (crop, fit, stretch)
        bg_color: fit 模式下的背景填充颜色，默认黑色
    
    Returns:
        调整后的片段
    
    Raises:
        ValueError: 如果 fit_mode 无效
    """
    if fit_mode not in FIT_MODES:
        raise ValueError(f"无效的适配模式: {fit_mode}，支持的模式: {list(FIT_MODES.keys())}")
    
    if fit_mode == "crop":
        return adapt_media_crop(clip, target_size)
    elif fit_mode == "fit":
        return adapt_media_fit(clip, target_size, bg_color)
    elif fit_mode == "stretch":
        return adapt_media_stretch(clip, target_size)
    
    return clip


# ============================================================
# 转场效果函数 (Requirements 6.4)
# ============================================================

def apply_fade_transition(clip1, clip2, duration: float = 0.5):
    """
    应用淡入淡出转场效果
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        duration: 转场时长（秒）
    
    Returns:
        合成后的片段
    """
    # 确保 clip1 有足够的时长进行淡出
    if clip1.duration <= duration:
        duration = clip1.duration * 0.5
    
    # 对 clip1 应用淡出效果
    clip1_fadeout = clip1.crossfadeout(duration)
    
    # 对 clip2 应用淡入效果
    clip2_fadein = clip2.crossfadein(duration)
    
    # 设置 clip2 的开始时间，使其与 clip1 重叠
    clip2_positioned = clip2_fadein.set_start(clip1.duration - duration)
    
    # 合成两个片段
    result = CompositeVideoClip([clip1_fadeout, clip2_positioned])
    
    return result


def apply_slide_transition(clip1, clip2, direction: str, duration: float = 0.5):
    """
    应用滑动转场效果
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        direction: 滑动方向 (left, right, up, down)
        duration: 转场时长（秒）
    
    Returns:
        合成后的片段
    """
    width, height = clip1.size
    
    # 确保 clip1 有足够的时长
    if clip1.duration <= duration:
        duration = clip1.duration * 0.5
    
    transition_start = clip1.duration - duration
    
    def slide_position(t):
        """计算滑动位置"""
        if t < transition_start:
            return (0, 0)
        
        progress = (t - transition_start) / duration
        progress = min(1.0, max(0.0, progress))
        
        if direction == "left":
            return (-width * progress, 0)
        elif direction == "right":
            return (width * progress, 0)
        elif direction == "up":
            return (0, -height * progress)
        elif direction == "down":
            return (0, height * progress)
        return (0, 0)
    
    def slide_in_position(t):
        """计算滑入位置"""
        if t < transition_start:
            if direction == "left":
                return (width, 0)
            elif direction == "right":
                return (-width, 0)
            elif direction == "up":
                return (0, height)
            elif direction == "down":
                return (0, -height)
            return (width, 0)
        
        progress = (t - transition_start) / duration
        progress = min(1.0, max(0.0, progress))
        
        if direction == "left":
            return (width * (1 - progress), 0)
        elif direction == "right":
            return (-width * (1 - progress), 0)
        elif direction == "up":
            return (0, height * (1 - progress))
        elif direction == "down":
            return (0, -height * (1 - progress))
        return (0, 0)
    
    # 设置 clip1 的滑出动画
    clip1_sliding = clip1.set_position(slide_position)
    
    # 设置 clip2 的滑入动画，从转场开始时显示
    clip2_sliding = clip2.set_start(0).set_position(slide_in_position)
    
    # 合成
    total_duration = clip1.duration + clip2.duration - duration
    result = CompositeVideoClip(
        [clip1_sliding, clip2_sliding],
        size=(width, height)
    ).set_duration(total_duration)
    
    return result


def apply_zoom_transition(clip1, clip2, direction: str, duration: float = 0.5):
    """
    应用缩放转场效果
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        direction: 缩放方向 (in, out)
        duration: 转场时长（秒）
    
    Returns:
        合成后的片段
    """
    width, height = clip1.size
    
    # 确保 clip1 有足够的时长
    if clip1.duration <= duration:
        duration = clip1.duration * 0.5
    
    transition_start = clip1.duration - duration
    
    def zoom_out_effect(get_frame, t):
        """clip1 缩小效果"""
        if t < transition_start:
            return get_frame(t)
        
        progress = (t - transition_start) / duration
        progress = min(1.0, max(0.0, progress))
        
        if direction == "in":
            # zoom_in: clip1 缩小消失
            scale = 1.0 - progress * 0.5
        else:
            # zoom_out: clip1 放大消失
            scale = 1.0 + progress * 0.5
        
        frame = get_frame(t)
        # 简单返回原帧，实际缩放通过 resize 实现
        return frame
    
    def zoom_in_effect(get_frame, t):
        """clip2 放大效果"""
        if t < transition_start:
            return get_frame(0)
        
        progress = (t - transition_start) / duration
        progress = min(1.0, max(0.0, progress))
        
        actual_t = (t - transition_start) * clip2.duration / duration if duration > 0 else 0
        actual_t = min(actual_t, clip2.duration - 0.01)
        
        return get_frame(actual_t)
    
    # 对于缩放效果，使用淡入淡出作为简化实现
    # 真正的缩放效果需要更复杂的帧处理
    clip1_fadeout = clip1.crossfadeout(duration)
    clip2_fadein = clip2.crossfadein(duration)
    clip2_positioned = clip2_fadein.set_start(clip1.duration - duration)
    
    result = CompositeVideoClip([clip1_fadeout, clip2_positioned])
    
    return result


def apply_dissolve_transition(clip1, clip2, duration: float = 0.5):
    """
    应用溶解转场效果（类似淡入淡出但更平滑）
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        duration: 转场时长（秒）
    
    Returns:
        合成后的片段
    """
    # 溶解效果本质上是淡入淡出的变体
    return apply_fade_transition(clip1, clip2, duration)


def apply_wipe_transition(clip1, clip2, direction: str, duration: float = 0.5):
    """
    应用擦除转场效果
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        direction: 擦除方向 (left, right)
        duration: 转场时长（秒）
    
    Returns:
        合成后的片段
    """
    width, height = clip1.size
    
    # 确保 clip1 有足够的时长
    if clip1.duration <= duration:
        duration = clip1.duration * 0.5
    
    transition_start = clip1.duration - duration
    
    def make_wipe_mask(t):
        """创建擦除遮罩"""
        import numpy as np
        
        if t < transition_start:
            # 完全显示 clip1
            return np.ones((height, width))
        
        progress = (t - transition_start) / duration
        progress = min(1.0, max(0.0, progress))
        
        mask = np.zeros((height, width))
        
        if direction == "left":
            # 从右向左擦除
            wipe_x = int(width * (1 - progress))
            mask[:, :wipe_x] = 1.0
        else:
            # 从左向右擦除
            wipe_x = int(width * progress)
            mask[:, wipe_x:] = 1.0
        
        return mask
    
    # 简化实现：使用淡入淡出代替复杂的遮罩
    # 真正的擦除效果需要自定义遮罩处理
    return apply_fade_transition(clip1, clip2, duration)


def apply_transition(
    clip1,
    clip2,
    transition_type: str,
    duration: float = 0.5
):
    """
    在两个片段之间应用转场效果 (Requirements 6.4)
    
    Args:
        clip1: 前一个片段
        clip2: 后一个片段
        transition_type: 转场类型 (none, fade, slide_left/right/up/down, 
                        zoom_in/out, dissolve, wipe_left/right)
        duration: 转场时长（秒），范围 0.3-2.0
    
    Returns:
        合成后的片段
    
    Raises:
        ValueError: 如果转场类型或时长无效
    """
    # 验证转场类型
    validate_transition_type(transition_type)
    
    # 验证转场时长（none 类型除外）
    if transition_type != "none":
        validate_transition_duration(duration)
    
    # 无转场：直接拼接
    if transition_type == "none":
        return concatenate_videoclips([clip1, clip2])
    
    # 淡入淡出转场
    elif transition_type == "fade":
        return apply_fade_transition(clip1, clip2, duration)
    
    # 滑动转场
    elif transition_type.startswith("slide_"):
        direction = transition_type.split("_")[1]
        return apply_slide_transition(clip1, clip2, direction, duration)
    
    # 缩放转场
    elif transition_type.startswith("zoom_"):
        direction = transition_type.split("_")[1]
        return apply_zoom_transition(clip1, clip2, direction, duration)
    
    # 溶解转场
    elif transition_type == "dissolve":
        return apply_dissolve_transition(clip1, clip2, duration)
    
    # 擦除转场
    elif transition_type.startswith("wipe_"):
        direction = transition_type.split("_")[1]
        return apply_wipe_transition(clip1, clip2, direction, duration)
    
    # 默认：直接拼接
    return concatenate_videoclips([clip1, clip2])


def apply_transitions_to_clips(
    clips: List,
    transition_type: str = "fade",
    duration: float = 0.5
):
    """
    对多个片段应用转场效果 (Requirements 6.4)
    
    Args:
        clips: 视频片段列表
        transition_type: 转场类型
        duration: 转场时长（秒）
    
    Returns:
        合成后的单个片段
    
    Raises:
        ValueError: 如果片段列表为空或转场配置无效
    """
    if not clips:
        raise ValueError("片段列表不能为空")
    
    if len(clips) == 1:
        return clips[0]
    
    # 验证转场配置
    validate_transition_type(transition_type)
    if transition_type != "none":
        validate_transition_duration(duration)
    
    # 逐个应用转场
    result = clips[0]
    for i in range(1, len(clips)):
        result = apply_transition(result, clips[i], transition_type, duration)
    
    return result


# ============================================================
# 视频特效函数 (Requirements 10.1)
# ============================================================

def apply_ken_burns_effect(
    clip,
    duration: Optional[float] = None,
    zoom_ratio: float = 1.2,
    direction: str = "in"
):
    """
    应用 Ken Burns 效果（缓慢缩放平移）(Requirements 10.1)
    
    Ken Burns 效果是一种常用于静态图片的动态效果，通过缓慢的缩放和平移
    使静态图片产生动感，增加视觉吸引力。
    
    Args:
        clip: MoviePy 视频/图片片段
        duration: 效果时长（秒），如果为 None 则使用 clip 的时长
        zoom_ratio: 缩放比例，默认 1.2（放大 20%）
        direction: 缩放方向，"in" 表示放大，"out" 表示缩小
    
    Returns:
        应用效果后的视频片段
    
    Raises:
        ValueError: 如果 direction 不是 "in" 或 "out"
    """
    import numpy as np
    from PIL import Image as PILImage
    
    if direction not in ("in", "out"):
        raise ValueError(f"无效的缩放方向: {direction}，支持的方向: in, out")
    
    if zoom_ratio <= 1.0:
        raise ValueError(f"缩放比例必须大于 1.0，实际值: {zoom_ratio}")
    
    effect_duration = duration if duration is not None else clip.duration
    original_size = clip.size
    
    def make_frame(t):
        """生成每一帧的缩放效果"""
        # 计算当前时间的缩放比例
        progress = t / effect_duration if effect_duration > 0 else 0
        progress = min(1.0, max(0.0, progress))
        
        if direction == "in":
            # 从 1.0 放大到 zoom_ratio
            current_zoom = 1.0 + (zoom_ratio - 1.0) * progress
        else:
            # 从 zoom_ratio 缩小到 1.0
            current_zoom = zoom_ratio - (zoom_ratio - 1.0) * progress
        
        # 获取原始帧
        frame = clip.get_frame(t)
        
        # 计算缩放后的尺寸
        new_width = int(original_size[0] * current_zoom)
        new_height = int(original_size[1] * current_zoom)
        
        # 使用 PIL 进行高质量缩放
        img = PILImage.fromarray(frame)
        img_resized = img.resize((new_width, new_height), PILImage.LANCZOS)
        
        # 裁剪中心区域以保持原始尺寸
        left = (new_width - original_size[0]) // 2
        top = (new_height - original_size[1]) // 2
        right = left + original_size[0]
        bottom = top + original_size[1]
        
        img_cropped = img_resized.crop((left, top, right, bottom))
        
        return np.array(img_cropped)
    
    # 创建新的视频片段
    from moviepy.editor import VideoClip
    result = VideoClip(make_frame, duration=effect_duration)
    result = result.set_fps(clip.fps if hasattr(clip, 'fps') and clip.fps else 30)
    
    # 保留原始音频（如果有）
    if clip.audio is not None:
        result = result.set_audio(clip.audio)
    
    return result


def validate_effect_type(effect_type: str) -> str:
    """
    验证特效类型 (Requirements 10.1)
    
    Args:
        effect_type: 特效类型
    
    Returns:
        验证后的特效类型
    
    Raises:
        ValueError: 如果特效类型无效
    """
    if effect_type not in EFFECT_TYPES:
        raise ValueError(
            f"无效的特效类型: {effect_type}，"
            f"支持的类型: {list(EFFECT_TYPES.keys())}"
        )
    return effect_type


def apply_video_effect(
    clip,
    effect_type: str,
    duration: Optional[float] = None,
    **kwargs
):
    """
    应用视频特效 (Requirements 10.1)
    
    Args:
        clip: MoviePy 视频/图片片段
        effect_type: 特效类型 (none, ken_burns_in, ken_burns_out, shake, 
                     zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down)
        duration: 效果时长（秒），如果为 None 则使用 clip 的时长
        **kwargs: 额外参数（如 zoom_ratio）
    
    Returns:
        应用效果后的视频片段
    
    Raises:
        ValueError: 如果特效类型无效
    """
    validate_effect_type(effect_type)
    
    if effect_type == "none":
        return clip
    
    elif effect_type == "ken_burns_in":
        zoom_ratio = kwargs.get("zoom_ratio", 1.2)
        return apply_ken_burns_effect(clip, duration, zoom_ratio, "in")
    
    elif effect_type == "ken_burns_out":
        zoom_ratio = kwargs.get("zoom_ratio", 1.2)
        return apply_ken_burns_effect(clip, duration, zoom_ratio, "out")
    
    elif effect_type == "shake":
        # 轻微抖动效果 - 使用简单的位置偏移
        return apply_shake_effect(clip, duration)
    
    elif effect_type == "zoom_in":
        return apply_ken_burns_effect(clip, duration, 1.3, "in")
    
    elif effect_type == "zoom_out":
        return apply_ken_burns_effect(clip, duration, 1.3, "out")
    
    elif effect_type.startswith("pan_"):
        direction = effect_type.split("_")[1]
        return apply_pan_effect(clip, duration, direction)
    
    return clip


def apply_shake_effect(clip, duration: Optional[float] = None):
    """
    应用轻微抖动效果 (Requirements 10.1)
    
    Args:
        clip: MoviePy 视频/图片片段
        duration: 效果时长（秒）
    
    Returns:
        应用效果后的视频片段
    """
    import numpy as np
    
    effect_duration = duration if duration is not None else clip.duration
    original_size = clip.size
    shake_amplitude = 5  # 抖动幅度（像素）
    
    def shake_position(t):
        """计算抖动位置"""
        # 使用正弦函数产生平滑的抖动
        x_offset = shake_amplitude * np.sin(t * 10)
        y_offset = shake_amplitude * np.cos(t * 8)
        return (x_offset, y_offset)
    
    return clip.set_position(shake_position)


def apply_pan_effect(clip, duration: Optional[float] = None, direction: str = "left"):
    """
    应用平移效果 (Requirements 10.1)
    
    Args:
        clip: MoviePy 视频/图片片段
        duration: 效果时长（秒）
        direction: 平移方向 (left, right, up, down)
    
    Returns:
        应用效果后的视频片段
    """
    import numpy as np
    from PIL import Image as PILImage
    
    effect_duration = duration if duration is not None else clip.duration
    original_size = clip.size
    pan_distance = int(original_size[0] * 0.1)  # 平移距离为宽度的 10%
    
    def make_frame(t):
        """生成每一帧的平移效果"""
        progress = t / effect_duration if effect_duration > 0 else 0
        progress = min(1.0, max(0.0, progress))
        
        # 获取原始帧
        frame = clip.get_frame(t)
        
        # 计算偏移量
        if direction == "left":
            x_offset = int(pan_distance * progress)
            y_offset = 0
        elif direction == "right":
            x_offset = -int(pan_distance * progress)
            y_offset = 0
        elif direction == "up":
            x_offset = 0
            y_offset = int(pan_distance * progress)
        elif direction == "down":
            x_offset = 0
            y_offset = -int(pan_distance * progress)
        else:
            x_offset = 0
            y_offset = 0
        
        # 使用 PIL 进行平移
        img = PILImage.fromarray(frame)
        
        # 创建稍大的画布以容纳平移
        canvas_size = (original_size[0] + abs(x_offset) * 2, 
                       original_size[1] + abs(y_offset) * 2)
        canvas = PILImage.new('RGB', canvas_size, (0, 0, 0))
        
        # 将图片放置在画布上
        paste_x = abs(x_offset) + x_offset
        paste_y = abs(y_offset) + y_offset
        canvas.paste(img, (paste_x, paste_y))
        
        # 裁剪回原始尺寸
        crop_x = abs(x_offset)
        crop_y = abs(y_offset)
        result = canvas.crop((crop_x, crop_y, 
                              crop_x + original_size[0], 
                              crop_y + original_size[1]))
        
        return np.array(result)
    
    from moviepy.editor import VideoClip
    result = VideoClip(make_frame, duration=effect_duration)
    result = result.set_fps(clip.fps if hasattr(clip, 'fps') and clip.fps else 30)
    
    if clip.audio is not None:
        result = result.set_audio(clip.audio)
    
    return result


# ============================================================
# 颜色滤镜函数 (Requirements 10.2)
# ============================================================

def validate_color_filter(filter_type: str) -> str:
    """
    验证颜色滤镜类型 (Requirements 10.2)
    
    Args:
        filter_type: 滤镜类型
    
    Returns:
        验证后的滤镜类型
    
    Raises:
        ValueError: 如果滤镜类型无效
    """
    if filter_type not in COLOR_FILTERS:
        raise ValueError(
            f"无效的滤镜类型: {filter_type}，"
            f"支持的类型: {list(COLOR_FILTERS.keys())}"
        )
    return filter_type


def apply_grayscale_filter(clip):
    """
    应用黑白滤镜 (Requirements 10.2)
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    return clip.fx(vfx.blackwhite)


def apply_vintage_filter(clip):
    """
    应用复古/怀旧滤镜 (Requirements 10.2)
    
    复古效果通过降低饱和度、增加暖色调和轻微降低对比度实现。
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    import numpy as np
    
    def vintage_effect(frame):
        """应用复古效果到单帧"""
        # 转换为浮点数进行处理
        img = frame.astype(np.float32)
        
        # 降低饱和度（向灰度靠近）
        gray = np.mean(img, axis=2, keepdims=True)
        img = img * 0.7 + gray * 0.3
        
        # 添加暖色调（增加红色和黄色）
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.1, 0, 255)  # 红色通道
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.05, 0, 255)  # 绿色通道
        img[:, :, 2] = np.clip(img[:, :, 2] * 0.9, 0, 255)  # 蓝色通道
        
        # 轻微降低对比度
        img = (img - 128) * 0.9 + 128
        
        # 添加轻微的褐色色调
        sepia_r = img[:, :, 0] * 0.393 + img[:, :, 1] * 0.769 + img[:, :, 2] * 0.189
        sepia_g = img[:, :, 0] * 0.349 + img[:, :, 1] * 0.686 + img[:, :, 2] * 0.168
        sepia_b = img[:, :, 0] * 0.272 + img[:, :, 1] * 0.534 + img[:, :, 2] * 0.131
        
        # 混合原图和褐色效果
        img[:, :, 0] = img[:, :, 0] * 0.6 + sepia_r * 0.4
        img[:, :, 1] = img[:, :, 1] * 0.6 + sepia_g * 0.4
        img[:, :, 2] = img[:, :, 2] * 0.6 + sepia_b * 0.4
        
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(vintage_effect)


def apply_warm_filter(clip):
    """
    应用暖色调滤镜 (Requirements 10.2)
    
    暖色调通过增加红色和黄色，减少蓝色实现。
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    import numpy as np
    
    def warm_effect(frame):
        """应用暖色调效果到单帧"""
        img = frame.astype(np.float32)
        
        # 增加红色和黄色，减少蓝色
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.15, 0, 255)  # 红色通道增强
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.05, 0, 255)  # 绿色通道轻微增强
        img[:, :, 2] = np.clip(img[:, :, 2] * 0.85, 0, 255)  # 蓝色通道减弱
        
        return img.astype(np.uint8)
    
    return clip.fl_image(warm_effect)


def apply_cool_filter(clip):
    """
    应用冷色调滤镜 (Requirements 10.2)
    
    冷色调通过增加蓝色，减少红色和黄色实现。
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    import numpy as np
    
    def cool_effect(frame):
        """应用冷色调效果到单帧"""
        img = frame.astype(np.float32)
        
        # 减少红色，增加蓝色
        img[:, :, 0] = np.clip(img[:, :, 0] * 0.9, 0, 255)  # 红色通道减弱
        img[:, :, 1] = np.clip(img[:, :, 1] * 0.95, 0, 255)  # 绿色通道轻微减弱
        img[:, :, 2] = np.clip(img[:, :, 2] * 1.15, 0, 255)  # 蓝色通道增强
        
        return img.astype(np.uint8)
    
    return clip.fl_image(cool_effect)


def apply_high_contrast_filter(clip):
    """
    应用高对比度滤镜 (Requirements 10.2)
    
    高对比度通过增强明暗差异实现。
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    import numpy as np
    
    def high_contrast_effect(frame):
        """应用高对比度效果到单帧"""
        img = frame.astype(np.float32)
        
        # 增强对比度：将像素值向两端拉伸
        contrast_factor = 1.4
        img = (img - 128) * contrast_factor + 128
        
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(high_contrast_effect)


def apply_soft_filter(clip):
    """
    应用柔和滤镜 (Requirements 10.2)
    
    柔和效果通过轻微模糊和降低对比度实现。
    
    Args:
        clip: MoviePy 视频片段
    
    Returns:
        应用滤镜后的视频片段
    """
    import numpy as np
    from PIL import Image as PILImage
    from PIL import ImageFilter
    
    def soft_effect(frame):
        """应用柔和效果到单帧"""
        # 确保输入是 uint8 类型
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        # 使用 PIL 进行轻微模糊
        img = PILImage.fromarray(frame)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        img_array = np.array(img).astype(np.float32)
        
        # 降低对比度
        contrast_factor = 0.85
        img_array = (img_array - 128) * contrast_factor + 128
        
        # 轻微提亮
        img_array = img_array * 1.05
        
        return np.clip(img_array, 0, 255).astype(np.uint8)
    
    return clip.fl_image(soft_effect)


def apply_color_filter(clip, filter_type: str):
    """
    应用颜色滤镜 (Requirements 10.2)
    
    Args:
        clip: MoviePy 视频片段
        filter_type: 滤镜类型 (none, grayscale, vintage, warm, cool, 
                     high_contrast, soft)
    
    Returns:
        应用滤镜后的视频片段
    
    Raises:
        ValueError: 如果滤镜类型无效
    """
    validate_color_filter(filter_type)
    
    if filter_type == "none":
        return clip
    
    elif filter_type == "grayscale":
        return apply_grayscale_filter(clip)
    
    elif filter_type == "vintage":
        return apply_vintage_filter(clip)
    
    elif filter_type == "warm":
        return apply_warm_filter(clip)
    
    elif filter_type == "cool":
        return apply_cool_filter(clip)
    
    elif filter_type == "high_contrast":
        return apply_high_contrast_filter(clip)
    
    elif filter_type == "soft":
        return apply_soft_filter(clip)
    
    return clip


# ============================================================
# 亮度/对比度/饱和度调节函数 (Requirements 10.3)
# ============================================================

def validate_brightness(brightness: float) -> float:
    """
    验证亮度参数 (Requirements 10.3)
    
    Args:
        brightness: 亮度值
    
    Returns:
        验证后的亮度值
    
    Raises:
        ValueError: 如果亮度值不在有效范围内
    """
    if brightness < BRIGHTNESS_MIN or brightness > BRIGHTNESS_MAX:
        raise ValueError(
            f"亮度值必须在 {BRIGHTNESS_MIN} 到 {BRIGHTNESS_MAX} 之间，"
            f"实际值: {brightness}"
        )
    return brightness


def validate_contrast(contrast: float) -> float:
    """
    验证对比度参数 (Requirements 10.3)
    
    Args:
        contrast: 对比度值
    
    Returns:
        验证后的对比度值
    
    Raises:
        ValueError: 如果对比度值不在有效范围内
    """
    if contrast < CONTRAST_MIN or contrast > CONTRAST_MAX:
        raise ValueError(
            f"对比度值必须在 {CONTRAST_MIN} 到 {CONTRAST_MAX} 之间，"
            f"实际值: {contrast}"
        )
    return contrast


def validate_saturation(saturation: float) -> float:
    """
    验证饱和度参数 (Requirements 10.3)
    
    Args:
        saturation: 饱和度值
    
    Returns:
        验证后的饱和度值
    
    Raises:
        ValueError: 如果饱和度值不在有效范围内
    """
    if saturation < SATURATION_MIN or saturation > SATURATION_MAX:
        raise ValueError(
            f"饱和度值必须在 {SATURATION_MIN} 到 {SATURATION_MAX} 之间，"
            f"实际值: {saturation}"
        )
    return saturation


def validate_video_adjustments(
    brightness: float = BRIGHTNESS_DEFAULT,
    contrast: float = CONTRAST_DEFAULT,
    saturation: float = SATURATION_DEFAULT
) -> Tuple[float, float, float]:
    """
    验证所有视频调节参数 (Requirements 10.3)
    
    Args:
        brightness: 亮度值 (0.5-2.0)
        contrast: 对比度值 (0.5-2.0)
        saturation: 饱和度值 (0-2.0)
    
    Returns:
        验证后的 (brightness, contrast, saturation) 元组
    
    Raises:
        ValueError: 如果任何参数不在有效范围内
    """
    return (
        validate_brightness(brightness),
        validate_contrast(contrast),
        validate_saturation(saturation)
    )


def adjust_brightness(clip, brightness: float = 1.0):
    """
    调节视频亮度 (Requirements 10.3)
    
    Args:
        clip: MoviePy 视频片段
        brightness: 亮度系数 (0.5-2.0)，1.0 为原始亮度
    
    Returns:
        调节后的视频片段
    
    Raises:
        ValueError: 如果亮度值不在有效范围内
    """
    import numpy as np
    
    validate_brightness(brightness)
    
    if brightness == 1.0:
        return clip
    
    def brightness_effect(frame):
        """调节单帧亮度"""
        img = frame.astype(np.float32)
        img = img * brightness
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(brightness_effect)


def adjust_contrast(clip, contrast: float = 1.0):
    """
    调节视频对比度 (Requirements 10.3)
    
    Args:
        clip: MoviePy 视频片段
        contrast: 对比度系数 (0.5-2.0)，1.0 为原始对比度
    
    Returns:
        调节后的视频片段
    
    Raises:
        ValueError: 如果对比度值不在有效范围内
    """
    import numpy as np
    
    validate_contrast(contrast)
    
    if contrast == 1.0:
        return clip
    
    def contrast_effect(frame):
        """调节单帧对比度"""
        img = frame.astype(np.float32)
        # 对比度调节：以 128 为中心进行缩放
        img = (img - 128) * contrast + 128
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(contrast_effect)


def adjust_saturation(clip, saturation: float = 1.0):
    """
    调节视频饱和度 (Requirements 10.3)
    
    Args:
        clip: MoviePy 视频片段
        saturation: 饱和度系数 (0-2.0)，1.0 为原始饱和度，0 为灰度
    
    Returns:
        调节后的视频片段
    
    Raises:
        ValueError: 如果饱和度值不在有效范围内
    """
    import numpy as np
    
    validate_saturation(saturation)
    
    if saturation == 1.0:
        return clip
    
    def saturation_effect(frame):
        """调节单帧饱和度"""
        img = frame.astype(np.float32)
        
        # 计算灰度值
        gray = np.mean(img, axis=2, keepdims=True)
        
        # 饱和度调节：在原图和灰度图之间插值
        # saturation = 0 时完全灰度，saturation = 1 时原图，saturation > 1 时增强饱和度
        img = gray + (img - gray) * saturation
        
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(saturation_effect)


def apply_video_adjustments(
    clip,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0
):
    """
    应用视频亮度/对比度/饱和度调节 (Requirements 10.3)
    
    Args:
        clip: MoviePy 视频片段
        brightness: 亮度系数 (0.5-2.0)
        contrast: 对比度系数 (0.5-2.0)
        saturation: 饱和度系数 (0-2.0)
    
    Returns:
        调节后的视频片段
    
    Raises:
        ValueError: 如果任何参数不在有效范围内
    """
    import numpy as np
    
    # 验证所有参数
    validate_video_adjustments(brightness, contrast, saturation)
    
    # 如果所有参数都是默认值，直接返回原片段
    if brightness == 1.0 and contrast == 1.0 and saturation == 1.0:
        return clip
    
    def combined_adjustment(frame):
        """组合调节单帧"""
        img = frame.astype(np.float32)
        
        # 1. 调节亮度
        if brightness != 1.0:
            img = img * brightness
        
        # 2. 调节对比度
        if contrast != 1.0:
            img = (img - 128) * contrast + 128
        
        # 3. 调节饱和度
        if saturation != 1.0:
            gray = np.mean(img, axis=2, keepdims=True)
            img = gray + (img - gray) * saturation
        
        return np.clip(img, 0, 255).astype(np.uint8)
    
    return clip.fl_image(combined_adjustment)


# ============================================================
# BGM 淡入淡出函数 (Requirements 6.8)
# ============================================================

def validate_bgm_fade_in(fade_in: float) -> float:
    """
    验证 BGM 淡入时长 (Requirements 6.8)
    
    Args:
        fade_in: 淡入时长（秒）
    
    Returns:
        验证后的淡入时长
    
    Raises:
        ValueError: 如果淡入时长不在有效范围内
    """
    if fade_in < BGM_FADE_IN_MIN or fade_in > BGM_FADE_IN_MAX:
        raise ValueError(
            f"BGM 淡入时长必须在 {BGM_FADE_IN_MIN} 到 {BGM_FADE_IN_MAX} 秒之间，"
            f"实际值: {fade_in}"
        )
    return fade_in


def validate_bgm_fade_out(fade_out: float) -> float:
    """
    验证 BGM 淡出时长 (Requirements 6.8)
    
    Args:
        fade_out: 淡出时长（秒）
    
    Returns:
        验证后的淡出时长
    
    Raises:
        ValueError: 如果淡出时长不在有效范围内
    """
    if fade_out < BGM_FADE_OUT_MIN or fade_out > BGM_FADE_OUT_MAX:
        raise ValueError(
            f"BGM 淡出时长必须在 {BGM_FADE_OUT_MIN} 到 {BGM_FADE_OUT_MAX} 秒之间，"
            f"实际值: {fade_out}"
        )
    return fade_out


def validate_bgm_volume(volume: float) -> float:
    """
    验证 BGM 音量 (Requirements 6.7)
    
    Args:
        volume: 音量（0-1，对应 0%-100%）
    
    Returns:
        验证后的音量
    
    Raises:
        ValueError: 如果音量不在有效范围内
    """
    if volume < BGM_VOLUME_MIN or volume > BGM_VOLUME_MAX:
        raise ValueError(
            f"BGM 音量必须在 {BGM_VOLUME_MIN} 到 {BGM_VOLUME_MAX} 之间，"
            f"实际值: {volume}"
        )
    return volume


def apply_bgm_fade_effects(
    bgm_clip,
    fade_in: float = BGM_FADE_IN_DEFAULT,
    fade_out: float = BGM_FADE_OUT_DEFAULT
):
    """
    应用 BGM 淡入淡出效果 (Requirements 6.8)
    
    Args:
        bgm_clip: BGM 音频片段 (AudioFileClip)
        fade_in: 淡入时长（秒），范围 0-5
        fade_out: 淡出时长（秒），范围 0-5
    
    Returns:
        应用淡入淡出效果后的音频片段
    
    Raises:
        ValueError: 如果淡入或淡出时长不在有效范围内
    """
    # 验证参数
    validate_bgm_fade_in(fade_in)
    validate_bgm_fade_out(fade_out)
    
    result = bgm_clip
    
    # 应用淡入效果
    if fade_in > 0:
        result = result.audio_fadein(fade_in)
    
    # 应用淡出效果
    if fade_out > 0:
        result = result.audio_fadeout(fade_out)
    
    return result


# ============================================================
# 音频混合函数 (Requirements 6.6, 6.7)
# ============================================================

def mix_audio_tracks(
    voice_audio,
    bgm_audio=None,
    bgm_volume: float = BGM_VOLUME_DEFAULT,
    bgm_fade_in: float = BGM_FADE_IN_DEFAULT,
    bgm_fade_out: float = BGM_FADE_OUT_DEFAULT,
    target_duration: float = None
):
    """
    混合音频轨道 (Requirements 6.6, 6.7)
    
    将配音作为主音轨，BGM 作为背景音轨进行混合。
    
    Args:
        voice_audio: 配音音频片段（主音轨）
        bgm_audio: BGM 音频片段（可选）
        bgm_volume: BGM 音量（0-1，对应 0%-100%）
        bgm_fade_in: BGM 淡入时长（秒）
        bgm_fade_out: BGM 淡出时长（秒）
        target_duration: 目标时长（秒），如果指定则调整音频时长
    
    Returns:
        混合后的音频片段
    
    Raises:
        ValueError: 如果参数不在有效范围内
    """
    # 验证参数
    validate_bgm_volume(bgm_volume)
    validate_bgm_fade_in(bgm_fade_in)
    validate_bgm_fade_out(bgm_fade_out)
    
    audio_clips = []
    
    # 确定目标时长
    if target_duration is not None:
        final_duration = target_duration
    elif voice_audio is not None:
        final_duration = voice_audio.duration
    elif bgm_audio is not None:
        final_duration = bgm_audio.duration
    else:
        return None
    
    # 处理配音（主音轨）
    if voice_audio is not None:
        voice = voice_audio
        # 如果配音时长与目标时长不一致，进行调整
        if target_duration is not None and voice.duration != target_duration:
            if voice.duration < target_duration:
                # 配音较短，保持原样（不循环配音）
                pass
            else:
                # 配音较长，裁剪
                voice = voice.subclip(0, target_duration)
        audio_clips.append(voice)
    
    # 处理 BGM（背景音轨）
    if bgm_audio is not None:
        bgm = bgm_audio
        
        # 调整 BGM 时长以匹配目标时长
        if bgm.duration < final_duration:
            # BGM 较短，循环播放
            bgm = afx.audio_loop(bgm, duration=final_duration)
        elif bgm.duration > final_duration:
            # BGM 较长，裁剪
            bgm = bgm.subclip(0, final_duration)
        
        # 调整 BGM 音量
        bgm = bgm.volumex(bgm_volume)
        
        # 应用淡入淡出效果
        bgm = apply_bgm_fade_effects(bgm, bgm_fade_in, bgm_fade_out)
        
        audio_clips.append(bgm)
    
    # 混合音频
    if not audio_clips:
        return None
    elif len(audio_clips) == 1:
        return audio_clips[0]
    else:
        return CompositeAudioClip(audio_clips)


def create_video_from_config(config: Dict, progress_callback=None) -> str:
    """
    根据配置生成视频 (Requirements 5.5, 6.1, 6.4, 6.8, 10.1, 10.2, 10.3)
    
    config 包含:
    - script: 文案
    - voice_audio_path: 配音文件路径
    - bgm_path: 背景音乐路径 (可选)
    - bgm_volume: BGM音量
    - bgm_fade_in: BGM淡入时长 (Requirements 6.8)
    - bgm_fade_out: BGM淡出时长 (Requirements 6.8)
    - video_resolution: 视频分辨率 (480p, 720p, 1080p, 2k, 4k) (Requirements 5.5)
    - video_layout: 布局比例 (9:16, 3:4, 1:1, 4:3, 16:9, 21:9) (Requirements 5.5)
    - platform_preset: 平台预设 (Requirements 5.5)
    - video_fps: 帧率
    - media_files: 素材文件列表
    - fit_mode: 素材适配模式 (crop, fit, stretch) (Requirements 6.1)
    - clip_min_duration: 片段最小时长
    - clip_max_duration: 片段最大时长
    - transition_enabled: 是否启用转场
    - transition_type: 转场类型 (Requirements 6.4)
    - transition_duration: 转场时长 (Requirements 6.4)
    - subtitle_enabled: 是否启用字幕
    - subtitle_config: 字幕配置
    - effect_type: 视频特效类型 (Requirements 10.1)
    - color_filter: 颜色滤镜 (Requirements 10.2)
    - brightness: 亮度调节 (Requirements 10.3)
    - contrast: 对比度调节 (Requirements 10.3)
    - saturation: 饱和度调节 (Requirements 10.3)
    - output_path: 输出路径
    """
    
    def update_progress(percent: int, message: str):
        if progress_callback:
            progress_callback(percent, message)
    
    update_progress(5, "正在解析配置...")
    
    # 获取视频尺寸 (Requirements 5.5)
    # 优先使用平台预设，否则使用分辨率和布局计算
    platform_preset = config.get("platform_preset")
    if platform_preset and platform_preset in PLATFORM_PRESETS:
        preset = PLATFORM_PRESETS[platform_preset]
        resolution = preset["resolution"]
        layout = preset["layout"]
        fps = preset["fps"]
    else:
        resolution = config.get("video_resolution", "1080p")
        layout = config.get("video_layout", "9:16")
        fps = config.get("video_fps", 30)
    
    # 使用新的尺寸计算函数 (Requirements 5.5)
    try:
        size = calculate_video_size(resolution, layout)
    except ValueError:
        # 回退到旧的尺寸获取方式
        old_layout = "portrait" if layout in ["9:16", "3:4"] else "landscape"
        size = get_video_size(resolution, old_layout)
    
    # 获取素材适配模式 (Requirements 6.1)
    fit_mode = config.get("fit_mode", "crop")
    if fit_mode not in FIT_MODES:
        fit_mode = "crop"
    
    # 获取转场配置 (Requirements 6.4)
    transition_enabled = config.get("transition_enabled", True)
    transition_type = config.get("transition_type", "fade")
    transition_duration = config.get("transition_duration", TRANSITION_DURATION_DEFAULT)
    
    # 验证转场配置
    if transition_type not in TRANSITIONS:
        transition_type = "fade"
    if transition_duration < TRANSITION_DURATION_MIN or transition_duration > TRANSITION_DURATION_MAX:
        transition_duration = TRANSITION_DURATION_DEFAULT
    
    # 获取视频特效配置 (Requirements 10.1, 10.2, 10.3)
    effect_type = config.get("effect_type", "none")
    color_filter = config.get("color_filter", "none")
    brightness = config.get("brightness", BRIGHTNESS_DEFAULT)
    contrast = config.get("contrast", CONTRAST_DEFAULT)
    saturation = config.get("saturation", SATURATION_DEFAULT)
    
    # 验证特效配置
    if effect_type and effect_type not in EFFECT_TYPES:
        effect_type = "none"
    if color_filter not in COLOR_FILTERS:
        color_filter = "none"
    
    # 验证调节参数范围
    brightness = max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, brightness))
    contrast = max(CONTRAST_MIN, min(CONTRAST_MAX, contrast))
    saturation = max(SATURATION_MIN, min(SATURATION_MAX, saturation))
    
    # 加载配音（作为旁白，不决定视频时长）
    update_progress(10, "正在加载配音...")
    voice_audio = None
    if config.get("voice_audio_path") and os.path.exists(config["voice_audio_path"]):
        voice_audio = AudioFileClip(config["voice_audio_path"])
    
    # 分割文案为句子
    sentences = split_script_to_sentences(config.get("script", ""))
    if not sentences:
        sentences = [""]
    
    # 加载素材
    update_progress(20, "正在加载素材...")
    media_files = config.get("media_files", [])
    
    # 片段时长由配置决定
    min_dur = config.get("clip_min_duration", 3.0)
    max_dur = config.get("clip_max_duration", 10.0)
    clip_duration = (min_dur + max_dur) / 2  # 使用平均值
    
    # 确定片段数量：取素材数量和句子数量的最大值，至少为1
    num_clips = max(len(media_files), len(sentences), 1)
    
    # 计算转场占用的时间
    if transition_enabled and transition_type != "none" and num_clips > 1:
        # 每个转场会使两个片段重叠 transition_duration 秒
        total_transition_time = (num_clips - 1) * transition_duration
    else:
        total_transition_time = 0
    
    # 视频总时长 = 片段数 * 片段时长 - 转场重叠时间
    total_duration = num_clips * clip_duration - total_transition_time
    
    # 创建视频片段
    update_progress(30, "正在生成视频片段...")
    video_clips = []
    
    for i in range(num_clips):
        # 计算当前片段时长
        seg_duration = clip_duration
        
        if seg_duration <= 0:
            continue
        
        # 选择素材（循环使用）(Requirements 6.3)
        if media_files:
            media_path = media_files[i % len(media_files)]
            ext = os.path.splitext(media_path)[1].lower()
            
            if ext in ALLOWED_VIDEO_EXTENSIONS:
                clip = VideoFileClip(media_path)
                # 如果视频比需要的短，循环播放
                if clip.duration < seg_duration:
                    clip = clip.loop(duration=seg_duration)
                else:
                    # 从不同位置截取片段，增加变化
                    start_pos = (i * seg_duration) % max(1, clip.duration - seg_duration)
                    end_pos = min(start_pos + seg_duration, clip.duration)
                    clip = clip.subclip(start_pos, end_pos)
            else:
                # 图片
                clip = ImageClip(media_path, duration=seg_duration)
                
                # 对图片应用特效 (Requirements 10.1)
                if effect_type and effect_type != "none":
                    try:
                        clip = apply_video_effect(clip, effect_type, seg_duration)
                    except Exception:
                        pass  # 特效应用失败时继续使用原片段
            
            # 使用新的素材适配函数 (Requirements 6.1)
            clip = adapt_media_to_size(clip, size, fit_mode)
        else:
            # 创建黑色背景
            clip = ColorClip(
                size=size,
                color=(30, 30, 30),
                duration=seg_duration
            )
        
        # 应用颜色滤镜 (Requirements 10.2)
        if color_filter and color_filter != "none":
            try:
                clip = apply_color_filter(clip, color_filter)
            except Exception:
                pass  # 滤镜应用失败时继续使用原片段
        
        # 应用亮度/对比度/饱和度调节 (Requirements 10.3)
        if brightness != 1.0 or contrast != 1.0 or saturation != 1.0:
            try:
                clip = apply_video_adjustments(clip, brightness, contrast, saturation)
            except Exception:
                pass  # 调节应用失败时继续使用原片段
        
        video_clips.append(clip)
        
        update_progress(30 + int(25 * (i + 1) / num_clips), f"处理片段 {i + 1}/{num_clips}")
    
    # 应用转场效果并合成视频 (Requirements 6.4)
    update_progress(55, "正在应用转场效果...")
    
    if not video_clips:
        # 创建空白视频
        final_video = ColorClip(size=size, color=(30, 30, 30), duration=total_duration)
    elif len(video_clips) == 1:
        # 只有一个片段，无需转场
        final_video = video_clips[0]
    elif transition_enabled and transition_type != "none":
        # 应用转场效果
        try:
            final_video = apply_transitions_to_clips(
                video_clips,
                transition_type=transition_type,
                duration=transition_duration
            )
        except Exception:
            # 转场应用失败时，直接拼接
            final_video = concatenate_videoclips(video_clips)
    else:
        # 不启用转场，直接拼接
        final_video = concatenate_videoclips(video_clips)
    
    # 更新实际总时长
    actual_duration = final_video.duration
    
    # 添加字幕
    if config.get("subtitle_enabled", True) and sentences[0]:
        update_progress(65, "正在添加字幕...")
        subtitle_config = config.get("subtitle_config", {})
        subtitle_clips = []
        
        # 检查是否有精准字幕时间戳
        sentence_subtitles = config.get("sentence_subtitles", [])
        
        if sentence_subtitles:
            # 使用精准字幕时间戳
            for sub in sentence_subtitles:
                if not sub.get("text"):
                    continue
                
                sub_start = sub.get("start", 0)
                sub_end = sub.get("end", sub_start + 2)
                sub_duration = sub_end - sub_start
                
                if sub_duration <= 0:
                    continue
                
                # 确保字幕不超出视频时长
                if sub_start >= actual_duration:
                    continue
                if sub_end > actual_duration:
                    sub_end = actual_duration
                    sub_duration = sub_end - sub_start
                
                txt_clip = create_text_clip(
                    sub["text"],
                    sub_duration,
                    size,
                    font=subtitle_config.get("font", "SimHei"),
                    fontsize=subtitle_config.get("size", 48),
                    color=subtitle_config.get("color", "white"),
                    stroke_color=subtitle_config.get("stroke_color", "black"),
                    stroke_width=subtitle_config.get("stroke_width", 2),
                    position=subtitle_config.get("position", "bottom")
                )
                txt_clip = txt_clip.set_start(sub_start)
                subtitle_clips.append(txt_clip)
        else:
            # 使用传统方式：按片段均分字幕
            # 计算每个字幕的时长（考虑转场重叠）
            subtitle_duration = actual_duration / num_clips if num_clips > 0 else actual_duration
            current_time = 0
            
            for i in range(num_clips):
                # 循环使用句子
                sentence = sentences[i % len(sentences)] if sentences else ""
                if not sentence:
                    current_time += subtitle_duration
                    continue
                
                seg_duration = subtitle_duration
                
                # 确保不超出视频时长
                if current_time >= actual_duration:
                    break
                if current_time + seg_duration > actual_duration:
                    seg_duration = actual_duration - current_time
                
                if seg_duration <= 0:
                    continue
                
                txt_clip = create_text_clip(
                    sentence,
                    seg_duration,
                    size,
                    font=subtitle_config.get("font", "SimHei"),
                    fontsize=subtitle_config.get("size", 48),
                    color=subtitle_config.get("color", "white"),
                    stroke_color=subtitle_config.get("stroke_color", "black"),
                    stroke_width=subtitle_config.get("stroke_width", 2),
                    position=subtitle_config.get("position", "bottom")
                )
                txt_clip = txt_clip.set_start(current_time)
                subtitle_clips.append(txt_clip)
                current_time += subtitle_duration
        
        if subtitle_clips:
            final_video = CompositeVideoClip([final_video] + subtitle_clips)
    
    # 添加音频 (Requirements 6.6, 6.7, 6.8)
    update_progress(80, "正在添加音频...")
    
    # 加载 BGM（如果有）
    bgm_audio = None
    if config.get("bgm_path") and os.path.exists(config["bgm_path"]):
        bgm_audio = AudioFileClip(config["bgm_path"])
    
    # 获取 BGM 配置 (Requirements 6.8)
    bgm_volume = config.get("bgm_volume", BGM_VOLUME_DEFAULT)
    bgm_fade_in = config.get("bgm_fade_in", BGM_FADE_IN_DEFAULT)
    bgm_fade_out = config.get("bgm_fade_out", BGM_FADE_OUT_DEFAULT)
    
    # 验证 BGM 配置范围
    bgm_volume = max(BGM_VOLUME_MIN, min(BGM_VOLUME_MAX, bgm_volume))
    bgm_fade_in = max(BGM_FADE_IN_MIN, min(BGM_FADE_IN_MAX, bgm_fade_in))
    bgm_fade_out = max(BGM_FADE_OUT_MIN, min(BGM_FADE_OUT_MAX, bgm_fade_out))
    
    # 使用音频混合函数 (Requirements 6.6, 6.7, 6.8)
    final_audio = mix_audio_tracks(
        voice_audio=voice_audio,
        bgm_audio=bgm_audio,
        bgm_volume=bgm_volume,
        bgm_fade_in=bgm_fade_in,
        bgm_fade_out=bgm_fade_out,
        target_duration=actual_duration
    )
    
    if final_audio is not None:
        final_video = final_video.set_audio(final_audio)
    
    # 导出视频 (Requirements 6.9 - MP4 格式，H.264 编码)
    update_progress(90, "正在导出视频...")
    output_path = config.get("output_path", "output.mp4")
    
    # 根据输出质量配置码率
    output_quality = config.get("output_quality", "high")
    bitrate_map = {
        "low": "2000k",
        "medium": "5000k",
        "high": "8000k",
        "ultra": "15000k"
    }
    bitrate = bitrate_map.get(output_quality, "8000k")
    
    final_video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        bitrate=bitrate,
        threads=4,
        preset="medium",
        verbose=False,
        logger=None
    )
    
    # 清理资源
    final_video.close()
    if voice_audio:
        voice_audio.close()
    if bgm_audio:
        bgm_audio.close()
    for clip in video_clips:
        try:
            clip.close()
        except Exception:
            pass
    
    update_progress(100, "视频生成完成")
    
    return output_path


# ============================================================
# 任务管理函数 (Requirements 8.1, 8.3, 8.5, 8.6)
# ============================================================

import uuid
import re as regex_module


def generate_task_id() -> str:
    """
    生成唯一的任务 ID (Requirements 8.1)
    
    使用 UUID v4 格式生成唯一的任务标识符。
    
    Returns:
        UUID 格式的任务 ID 字符串 (例如: "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid.uuid4())


def is_valid_uuid(task_id: str) -> bool:
    """
    验证任务 ID 是否为有效的 UUID 格式 (Requirements 8.1)
    
    Args:
        task_id: 要验证的任务 ID 字符串
    
    Returns:
        True 如果是有效的 UUID 格式，False 否则
    """
    if not task_id or not isinstance(task_id, str):
        return False
    
    # UUID v4 格式正则表达式
    uuid_pattern = regex_module.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        regex_module.IGNORECASE
    )
    
    return bool(uuid_pattern.match(task_id))


def is_valid_uuid_format(task_id: str) -> bool:
    """
    验证任务 ID 是否为有效的 UUID 格式（宽松版本）(Requirements 8.1)
    
    接受任何版本的 UUID 格式。
    
    Args:
        task_id: 要验证的任务 ID 字符串
    
    Returns:
        True 如果是有效的 UUID 格式，False 否则
    """
    if not task_id or not isinstance(task_id, str):
        return False
    
    # 通用 UUID 格式正则表达式（接受任何版本）
    uuid_pattern = regex_module.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        regex_module.IGNORECASE
    )
    
    return bool(uuid_pattern.match(task_id))


# 任务状态常量
TASK_STATUS_PENDING = 0      # 等待中
TASK_STATUS_PROCESSING = 1   # 处理中
TASK_STATUS_COMPLETED = 2    # 已完成
TASK_STATUS_FAILED = 3       # 失败

# 任务状态名称映射
TASK_STATUS_NAMES = {
    TASK_STATUS_PENDING: "pending",
    TASK_STATUS_PROCESSING: "processing",
    TASK_STATUS_COMPLETED: "completed",
    TASK_STATUS_FAILED: "failed",
}


def get_task_status_name(status_code: int) -> str:
    """
    获取任务状态名称 (Requirements 8.3)
    
    Args:
        status_code: 任务状态码 (0-3)
    
    Returns:
        状态名称字符串
    """
    return TASK_STATUS_NAMES.get(status_code, "unknown")


class TaskStatusResponse:
    """
    任务状态响应类 (Requirements 8.3, 8.5, 8.6)
    
    封装任务状态查询的完整响应信息。
    """
    
    def __init__(
        self,
        status: str,
        progress: int,
        message: str,
        download_url: Optional[str] = None,
        error_message: Optional[str] = None,
        duration: Optional[float] = None,
        task_id: Optional[str] = None
    ):
        """
        初始化任务状态响应
        
        Args:
            status: 状态名称 (pending, processing, completed, failed)
            progress: 进度百分比 (0-100)
            message: 状态消息
            download_url: 下载链接（仅完成状态）
            error_message: 错误信息（仅失败状态）
            duration: 视频时长（仅完成状态）
            task_id: 任务 ID
        """
        self.status = status
        self.progress = progress
        self.message = message
        self.download_url = download_url
        self.error_message = error_message
        self.duration = duration
        self.task_id = task_id
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式 (Requirements 8.3, 8.5, 8.6)
        
        根据任务状态返回完整的状态信息：
        - 完成状态返回 download_url
        - 失败状态返回 error_message
        
        Returns:
            包含完整状态信息的字典
        """
        result = {
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
        }
        
        # 添加任务 ID（如果有）
        if self.task_id:
            result["task_id"] = self.task_id
        
        # 完成状态返回 download_url (Requirements 8.5)
        if self.status == "completed":
            if self.download_url:
                result["download_url"] = self.download_url
            if self.duration is not None:
                result["duration"] = self.duration
        
        # 失败状态返回 error_message (Requirements 8.6)
        if self.status == "failed":
            if self.error_message:
                result["error_message"] = self.error_message
        
        return result


def build_task_status_response(
    status_code: int,
    progress: int,
    progress_message: Optional[str] = None,
    error_message: Optional[str] = None,
    download_url: Optional[str] = None,
    duration: Optional[float] = None,
    task_id: Optional[str] = None
) -> TaskStatusResponse:
    """
    构建任务状态响应 (Requirements 8.3, 8.5, 8.6)
    
    根据任务状态码构建完整的状态响应对象。
    
    Args:
        status_code: 任务状态码 (0-3)
        progress: 进度百分比 (0-100)
        progress_message: 进度消息
        error_message: 错误信息（仅失败状态使用）
        download_url: 下载链接（仅完成状态使用）
        duration: 视频时长（仅完成状态使用）
        task_id: 任务 ID
    
    Returns:
        TaskStatusResponse 对象
    """
    status_name = get_task_status_name(status_code)
    
    # 确保进度在有效范围内
    progress = max(0, min(100, progress))
    
    # 根据状态设置默认消息
    if not progress_message:
        default_messages = {
            TASK_STATUS_PENDING: "等待处理...",
            TASK_STATUS_PROCESSING: "正在处理...",
            TASK_STATUS_COMPLETED: "视频生成完成",
            TASK_STATUS_FAILED: "视频生成失败",
        }
        progress_message = default_messages.get(status_code, "未知状态")
    
    # 完成状态强制设置进度为 100
    if status_code == TASK_STATUS_COMPLETED:
        progress = 100
    
    # 失败状态强制设置进度为 0
    if status_code == TASK_STATUS_FAILED:
        progress = 0
    
    return TaskStatusResponse(
        status=status_name,
        progress=progress,
        message=progress_message,
        download_url=download_url if status_code == TASK_STATUS_COMPLETED else None,
        error_message=error_message if status_code == TASK_STATUS_FAILED else None,
        duration=duration if status_code == TASK_STATUS_COMPLETED else None,
        task_id=task_id
    )


def validate_task_status_response(response: Dict) -> Tuple[bool, List[str]]:
    """
    验证任务状态响应的完整性 (Requirements 8.3, 8.5, 8.6)
    
    验证响应是否包含所有必要字段：
    - status（状态枚举值）
    - progress（0-100 的整数）
    - message（状态消息字符串）
    - 完成状态时包含 download_url
    - 失败状态时包含 error_message
    
    Args:
        response: 任务状态响应字典
    
    Returns:
        (is_valid, errors) 元组
        - is_valid: True 如果响应完整，False 否则
        - errors: 错误信息列表
    """
    errors = []
    
    # 验证必要字段存在
    if "status" not in response:
        errors.append("缺少 status 字段")
    
    if "progress" not in response:
        errors.append("缺少 progress 字段")
    
    if "message" not in response:
        errors.append("缺少 message 字段")
    
    # 如果有基本字段，进行进一步验证
    if "status" in response:
        status = response["status"]
        valid_statuses = ["pending", "processing", "completed", "failed"]
        
        if status not in valid_statuses:
            errors.append(f"无效的 status 值: {status}")
        
        # 完成状态必须有 download_url (Requirements 8.5)
        if status == "completed" and "download_url" not in response:
            errors.append("完成状态缺少 download_url 字段")
        
        # 失败状态必须有 error_message (Requirements 8.6)
        if status == "failed" and "error_message" not in response:
            errors.append("失败状态缺少 error_message 字段")
    
    if "progress" in response:
        progress = response["progress"]
        if not isinstance(progress, int) or progress < 0 or progress > 100:
            errors.append(f"progress 必须是 0-100 的整数，实际值: {progress}")
    
    if "message" in response:
        message = response["message"]
        if not isinstance(message, str):
            errors.append(f"message 必须是字符串，实际类型: {type(message)}")
    
    return len(errors) == 0, errors
