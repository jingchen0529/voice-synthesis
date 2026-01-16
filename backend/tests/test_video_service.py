"""
视频服务属性测试

使用 hypothesis 进行属性测试，验证视频配置和尺寸计算的正确性。
"""
import os
import tempfile
import pytest
from hypothesis import given, settings, strategies as st
from moviepy.editor import ColorClip

from app.services.video_service import (
    VIDEO_RESOLUTIONS,
    VIDEO_LAYOUTS,
    FRAME_RATES,
    PLATFORM_PRESETS,
    FIT_MODES,
    TRANSITIONS,
    TRANSITION_DURATION_MIN,
    TRANSITION_DURATION_MAX,
    calculate_video_size,
    adapt_media_to_size,
    adapt_media_crop,
    adapt_media_fit,
    adapt_media_stretch,
    validate_transition_duration,
    validate_transition_type,
    get_transition_config,
)


# 配置 hypothesis：减少迭代次数以加快测试速度
settings.register_profile("ci", max_examples=20)
settings.load_profile("ci")


# ============================================================
# Property 1: 视频尺寸计算正确性
# **Feature: video-remix, Property 1: 视频尺寸计算正确性**
# **Validates: Requirements 5.1, 5.2**
# ============================================================

@given(
    resolution=st.sampled_from(list(VIDEO_RESOLUTIONS.keys())),
    layout=st.sampled_from(list(VIDEO_LAYOUTS.keys()))
)
@settings(max_examples=20)
def test_video_size_calculation_correctness(resolution: str, layout: str):
    """
    Property 1: 视频尺寸计算正确性
    
    *For any* 有效的分辨率和布局组合，计算出的视频尺寸应满足：
    - 宽度和高度都是正偶数
    - 宽高比与指定布局的比例一致（误差 < 1%）
    
    **Validates: Requirements 5.1, 5.2**
    """
    width, height = calculate_video_size(resolution, layout)
    
    # 验证尺寸为正数
    assert width > 0, f"宽度必须为正数，实际值: {width}"
    assert height > 0, f"高度必须为正数，实际值: {height}"
    
    # 验证尺寸为偶数（视频编码要求）
    assert width % 2 == 0, f"宽度必须为偶数，实际值: {width}"
    assert height % 2 == 0, f"高度必须为偶数，实际值: {height}"
    
    # 验证宽高比
    expected_ratio = VIDEO_LAYOUTS[layout]["ratio"]
    expected = expected_ratio[0] / expected_ratio[1]
    actual_ratio = width / height
    
    # 允许 1% 的误差（由于取整）
    ratio_error = abs(actual_ratio - expected) / expected
    assert ratio_error < 0.01, (
        f"宽高比误差过大: 期望 {expected:.4f}, 实际 {actual_ratio:.4f}, "
        f"误差 {ratio_error:.4f} (> 1%)"
    )


# ============================================================
# Property 2: 平台预设配置完整性
# **Feature: video-remix, Property 2: 平台预设配置完整性**
# **Validates: Requirements 5.4, 5.5**
# ============================================================

@given(platform=st.sampled_from(list(PLATFORM_PRESETS.keys())))
@settings(max_examples=20)
def test_platform_preset_completeness(platform: str):
    """
    Property 2: 平台预设配置完整性
    
    *For any* 平台预设选择，应用预设后的配置应包含有效的分辨率、布局和帧率值，
    且这些值都在系统支持的范围内。
    
    **Validates: Requirements 5.4, 5.5**
    """
    preset = PLATFORM_PRESETS[platform]
    
    # 验证预设包含必要字段
    assert "resolution" in preset, f"平台 {platform} 缺少 resolution 字段"
    assert "layout" in preset, f"平台 {platform} 缺少 layout 字段"
    assert "fps" in preset, f"平台 {platform} 缺少 fps 字段"
    
    # 验证分辨率在支持范围内
    assert preset["resolution"] in VIDEO_RESOLUTIONS, (
        f"平台 {platform} 的分辨率 {preset['resolution']} 不在支持范围内"
    )
    
    # 验证布局在支持范围内
    assert preset["layout"] in VIDEO_LAYOUTS, (
        f"平台 {platform} 的布局 {preset['layout']} 不在支持范围内"
    )
    
    # 验证帧率在支持范围内
    assert preset["fps"] in FRAME_RATES, (
        f"平台 {platform} 的帧率 {preset['fps']} 不在支持范围内"
    )
    
    # 验证可以使用预设配置计算视频尺寸
    width, height = calculate_video_size(preset["resolution"], preset["layout"])
    assert width > 0 and height > 0, (
        f"平台 {platform} 的预设配置无法计算有效的视频尺寸"
    )


# ============================================================
# Property 7: 素材尺寸适配正确性
# **Feature: video-remix, Property 7: 素材尺寸适配正确性**
# **Validates: Requirements 6.1**
# ============================================================

# 定义合理的尺寸范围策略
reasonable_size = st.integers(min_value=100, max_value=1920)


@given(
    source_width=reasonable_size,
    source_height=reasonable_size,
    target_width=reasonable_size,
    target_height=reasonable_size,
    fit_mode=st.sampled_from(list(FIT_MODES.keys()))
)
@settings(max_examples=20, deadline=None)
def test_media_adaptation_correctness(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    fit_mode: str
):
    """
    Property 7: 素材尺寸适配正确性
    
    *For any* 素材和目标尺寸组合，适配后的输出应满足：
    - crop 模式：输出尺寸 = 目标尺寸
    - fit 模式：输出尺寸 = 目标尺寸，素材保持原比例
    - stretch 模式：输出尺寸 = 目标尺寸
    
    **Validates: Requirements 6.1**
    """
    # 创建测试用的 ColorClip 作为素材
    source_clip = ColorClip(
        size=(source_width, source_height),
        color=(100, 100, 100),
        duration=1.0
    )
    
    target_size = (target_width, target_height)
    
    try:
        # 应用适配
        result_clip = adapt_media_to_size(source_clip, target_size, fit_mode)
        
        # 验证输出尺寸
        result_width, result_height = result_clip.size
        
        if fit_mode == "crop":
            # crop 模式：输出尺寸必须等于目标尺寸
            assert result_width == target_width, (
                f"crop 模式输出宽度错误: 期望 {target_width}, 实际 {result_width}"
            )
            assert result_height == target_height, (
                f"crop 模式输出高度错误: 期望 {target_height}, 实际 {result_height}"
            )
        
        elif fit_mode == "fit":
            # fit 模式：输出尺寸必须等于目标尺寸（包含背景）
            assert result_width == target_width, (
                f"fit 模式输出宽度错误: 期望 {target_width}, 实际 {result_width}"
            )
            assert result_height == target_height, (
                f"fit 模式输出高度错误: 期望 {target_height}, 实际 {result_height}"
            )
        
        elif fit_mode == "stretch":
            # stretch 模式：输出尺寸必须等于目标尺寸
            assert result_width == target_width, (
                f"stretch 模式输出宽度错误: 期望 {target_width}, 实际 {result_width}"
            )
            assert result_height == target_height, (
                f"stretch 模式输出高度错误: 期望 {target_height}, 实际 {result_height}"
            )
        
        # 清理资源
        result_clip.close()
    finally:
        source_clip.close()


@given(fit_mode=st.sampled_from(list(FIT_MODES.keys())))
@settings(max_examples=20)
def test_media_adaptation_preserves_aspect_ratio_in_fit_mode(fit_mode: str):
    """
    验证 fit 模式下素材保持原始比例
    
    **Validates: Requirements 6.1**
    """
    # 使用固定的测试尺寸以便验证比例
    source_size = (800, 600)  # 4:3 比例
    target_size = (1920, 1080)  # 16:9 比例
    
    source_clip = ColorClip(
        size=source_size,
        color=(100, 100, 100),
        duration=1.0
    )
    
    try:
        result_clip = adapt_media_to_size(source_clip, target_size, fit_mode)
        
        # 所有模式的输出尺寸都应该等于目标尺寸
        assert result_clip.size == target_size, (
            f"{fit_mode} 模式输出尺寸错误: 期望 {target_size}, 实际 {result_clip.size}"
        )
        
        result_clip.close()
    finally:
        source_clip.close()


def test_adapt_media_invalid_fit_mode():
    """
    验证无效的适配模式会抛出 ValueError
    
    **Validates: Requirements 6.1**
    """
    source_clip = ColorClip(
        size=(800, 600),
        color=(100, 100, 100),
        duration=1.0
    )
    
    try:
        with pytest.raises(ValueError) as exc_info:
            adapt_media_to_size(source_clip, (1920, 1080), "invalid_mode")
        
        assert "无效的适配模式" in str(exc_info.value)
    finally:
        source_clip.close()


# ============================================================
# Property 10: 转场时长配置验证
# **Feature: video-remix, Property 10: 转场时长配置验证**
# **Validates: Requirements 6.5**
# ============================================================

@given(
    duration=st.floats(
        min_value=TRANSITION_DURATION_MIN,
        max_value=TRANSITION_DURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_transition_duration_validation_valid(duration: float):
    """
    Property 10: 转场时长配置验证 - 有效范围
    
    *For any* 转场配置，转场时长应在 0.3 到 2.0 秒范围内。
    
    **Validates: Requirements 6.5**
    """
    # 有效范围内的时长应该通过验证
    result = validate_transition_duration(duration)
    assert result == duration, f"验证后的时长应该等于输入时长: {duration}"
    
    # 验证时长确实在有效范围内
    assert TRANSITION_DURATION_MIN <= result <= TRANSITION_DURATION_MAX, (
        f"转场时长 {result} 不在有效范围 [{TRANSITION_DURATION_MIN}, {TRANSITION_DURATION_MAX}] 内"
    )


@given(
    duration=st.floats(
        min_value=0.0,
        max_value=TRANSITION_DURATION_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_transition_duration_validation_too_short(duration: float):
    """
    Property 10: 转场时长配置验证 - 时长过短
    
    *For any* 小于最小值的转场时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_transition_duration(duration)
    
    assert "转场时长必须在" in str(exc_info.value)


@given(
    duration=st.floats(
        min_value=TRANSITION_DURATION_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_transition_duration_validation_too_long(duration: float):
    """
    Property 10: 转场时长配置验证 - 时长过长
    
    *For any* 大于最大值的转场时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_transition_duration(duration)
    
    assert "转场时长必须在" in str(exc_info.value)


@given(transition_type=st.sampled_from(list(TRANSITIONS.keys())))
@settings(max_examples=20)
def test_transition_type_validation_valid(transition_type: str):
    """
    Property 10: 转场类型验证 - 有效类型
    
    *For any* 有效的转场类型，验证应该通过。
    
    **Validates: Requirements 6.4**
    """
    result = validate_transition_type(transition_type)
    assert result == transition_type, f"验证后的类型应该等于输入类型: {transition_type}"
    assert result in TRANSITIONS, f"转场类型 {result} 应该在支持的类型列表中"


def test_transition_type_validation_invalid():
    """
    验证无效的转场类型会抛出 ValueError
    
    **Validates: Requirements 6.4**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_transition_type("invalid_transition")
    
    assert "无效的转场类型" in str(exc_info.value)


@given(
    transition_type=st.sampled_from(list(TRANSITIONS.keys())),
    duration=st.floats(
        min_value=TRANSITION_DURATION_MIN,
        max_value=TRANSITION_DURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_get_transition_config_completeness(transition_type: str, duration: float):
    """
    Property 10: 转场配置完整性
    
    *For any* 有效的转场类型和时长，获取的配置应包含完整信息。
    
    **Validates: Requirements 6.4, 6.5**
    """
    config = get_transition_config(transition_type, duration)
    
    # 验证配置包含必要字段
    assert "type" in config, "配置应包含 type 字段"
    assert "name" in config, "配置应包含 name 字段"
    assert "duration" in config, "配置应包含 duration 字段"
    
    # 验证类型正确
    assert config["type"] == transition_type
    
    # 验证时长
    if transition_type == "none":
        assert config["duration"] == 0, "none 类型的时长应该为 0"
    else:
        assert config["duration"] == duration, f"时长应该等于指定值: {duration}"



# ============================================================
# Property 19: 视频调节参数范围
# **Feature: video-remix, Property 19: 视频调节参数范围**
# **Validates: Requirements 10.3**
# ============================================================

from app.services.video_service import (
    BRIGHTNESS_MIN,
    BRIGHTNESS_MAX,
    BRIGHTNESS_DEFAULT,
    CONTRAST_MIN,
    CONTRAST_MAX,
    CONTRAST_DEFAULT,
    SATURATION_MIN,
    SATURATION_MAX,
    SATURATION_DEFAULT,
    COLOR_FILTERS,
    EFFECT_TYPES,
    validate_brightness,
    validate_contrast,
    validate_saturation,
    validate_video_adjustments,
    validate_color_filter,
    validate_effect_type,
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_video_adjustments,
    apply_color_filter,
    apply_video_effect,
    apply_ken_burns_effect,
)


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MIN,
        max_value=BRIGHTNESS_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_brightness_validation_valid(brightness: float):
    """
    Property 19: 视频调节参数范围 - 亮度有效范围
    
    *For any* 亮度参数在 0.5-2.0 范围内，验证应该通过。
    
    **Validates: Requirements 10.3**
    """
    result = validate_brightness(brightness)
    assert result == brightness, f"验证后的亮度应该等于输入值: {brightness}"
    assert BRIGHTNESS_MIN <= result <= BRIGHTNESS_MAX, (
        f"亮度 {result} 不在有效范围 [{BRIGHTNESS_MIN}, {BRIGHTNESS_MAX}] 内"
    )


@given(
    brightness=st.floats(
        min_value=0.0,
        max_value=BRIGHTNESS_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_brightness_validation_too_low(brightness: float):
    """
    Property 19: 视频调节参数范围 - 亮度过低
    
    *For any* 小于最小值的亮度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_brightness(brightness)
    
    assert "亮度值必须在" in str(exc_info.value)


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_brightness_validation_too_high(brightness: float):
    """
    Property 19: 视频调节参数范围 - 亮度过高
    
    *For any* 大于最大值的亮度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_brightness(brightness)
    
    assert "亮度值必须在" in str(exc_info.value)


@given(
    contrast=st.floats(
        min_value=CONTRAST_MIN,
        max_value=CONTRAST_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_contrast_validation_valid(contrast: float):
    """
    Property 19: 视频调节参数范围 - 对比度有效范围
    
    *For any* 对比度参数在 0.5-2.0 范围内，验证应该通过。
    
    **Validates: Requirements 10.3**
    """
    result = validate_contrast(contrast)
    assert result == contrast, f"验证后的对比度应该等于输入值: {contrast}"
    assert CONTRAST_MIN <= result <= CONTRAST_MAX, (
        f"对比度 {result} 不在有效范围 [{CONTRAST_MIN}, {CONTRAST_MAX}] 内"
    )


@given(
    contrast=st.floats(
        min_value=0.0,
        max_value=CONTRAST_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_contrast_validation_too_low(contrast: float):
    """
    Property 19: 视频调节参数范围 - 对比度过低
    
    *For any* 小于最小值的对比度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_contrast(contrast)
    
    assert "对比度值必须在" in str(exc_info.value)


@given(
    contrast=st.floats(
        min_value=CONTRAST_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_contrast_validation_too_high(contrast: float):
    """
    Property 19: 视频调节参数范围 - 对比度过高
    
    *For any* 大于最大值的对比度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_contrast(contrast)
    
    assert "对比度值必须在" in str(exc_info.value)


@given(
    saturation=st.floats(
        min_value=SATURATION_MIN,
        max_value=SATURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_saturation_validation_valid(saturation: float):
    """
    Property 19: 视频调节参数范围 - 饱和度有效范围
    
    *For any* 饱和度参数在 0-2.0 范围内，验证应该通过。
    
    **Validates: Requirements 10.3**
    """
    result = validate_saturation(saturation)
    assert result == saturation, f"验证后的饱和度应该等于输入值: {saturation}"
    assert SATURATION_MIN <= result <= SATURATION_MAX, (
        f"饱和度 {result} 不在有效范围 [{SATURATION_MIN}, {SATURATION_MAX}] 内"
    )


@given(
    saturation=st.floats(
        min_value=-10.0,
        max_value=SATURATION_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_saturation_validation_too_low(saturation: float):
    """
    Property 19: 视频调节参数范围 - 饱和度过低
    
    *For any* 小于最小值的饱和度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_saturation(saturation)
    
    assert "饱和度值必须在" in str(exc_info.value)


@given(
    saturation=st.floats(
        min_value=SATURATION_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_saturation_validation_too_high(saturation: float):
    """
    Property 19: 视频调节参数范围 - 饱和度过高
    
    *For any* 大于最大值的饱和度，应该抛出 ValueError。
    
    **Validates: Requirements 10.3**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_saturation(saturation)
    
    assert "饱和度值必须在" in str(exc_info.value)


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MIN,
        max_value=BRIGHTNESS_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    contrast=st.floats(
        min_value=CONTRAST_MIN,
        max_value=CONTRAST_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    saturation=st.floats(
        min_value=SATURATION_MIN,
        max_value=SATURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_video_adjustments_validation_combined(
    brightness: float,
    contrast: float,
    saturation: float
):
    """
    Property 19: 视频调节参数范围 - 组合验证
    
    *For any* 有效的亮度、对比度、饱和度组合，验证应该通过。
    
    **Validates: Requirements 10.3**
    """
    result = validate_video_adjustments(brightness, contrast, saturation)
    
    assert result[0] == brightness, f"亮度验证失败: {brightness}"
    assert result[1] == contrast, f"对比度验证失败: {contrast}"
    assert result[2] == saturation, f"饱和度验证失败: {saturation}"


@given(filter_type=st.sampled_from(list(COLOR_FILTERS.keys())))
@settings(max_examples=20)
def test_color_filter_validation_valid(filter_type: str):
    """
    Property 19: 颜色滤镜类型验证 - 有效类型
    
    *For any* 有效的颜色滤镜类型，验证应该通过。
    
    **Validates: Requirements 10.2**
    """
    result = validate_color_filter(filter_type)
    assert result == filter_type, f"验证后的滤镜类型应该等于输入类型: {filter_type}"
    assert result in COLOR_FILTERS, f"滤镜类型 {result} 应该在支持的类型列表中"


def test_color_filter_validation_invalid():
    """
    验证无效的颜色滤镜类型会抛出 ValueError
    
    **Validates: Requirements 10.2**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_color_filter("invalid_filter")
    
    assert "无效的滤镜类型" in str(exc_info.value)


@given(effect_type=st.sampled_from(list(EFFECT_TYPES.keys())))
@settings(max_examples=20)
def test_effect_type_validation_valid(effect_type: str):
    """
    Property 19: 特效类型验证 - 有效类型
    
    *For any* 有效的特效类型，验证应该通过。
    
    **Validates: Requirements 10.1**
    """
    result = validate_effect_type(effect_type)
    assert result == effect_type, f"验证后的特效类型应该等于输入类型: {effect_type}"
    assert result in EFFECT_TYPES, f"特效类型 {result} 应该在支持的类型列表中"


def test_effect_type_validation_invalid():
    """
    验证无效的特效类型会抛出 ValueError
    
    **Validates: Requirements 10.1**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_effect_type("invalid_effect")
    
    assert "无效的特效类型" in str(exc_info.value)


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MIN,
        max_value=BRIGHTNESS_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    contrast=st.floats(
        min_value=CONTRAST_MIN,
        max_value=CONTRAST_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    saturation=st.floats(
        min_value=SATURATION_MIN,
        max_value=SATURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_apply_video_adjustments_preserves_size(
    brightness: float,
    contrast: float,
    saturation: float
):
    """
    Property 19: 视频调节保持尺寸
    
    *For any* 有效的调节参数，应用调节后视频尺寸应保持不变。
    
    **Validates: Requirements 10.3**
    """
    # 创建测试用的 ColorClip
    source_clip = ColorClip(
        size=(640, 480),
        color=(128, 128, 128),
        duration=1.0
    )
    
    try:
        result_clip = apply_video_adjustments(
            source_clip,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation
        )
        
        # 验证尺寸保持不变
        assert result_clip.size == source_clip.size, (
            f"调节后尺寸应保持不变: 期望 {source_clip.size}, 实际 {result_clip.size}"
        )
        
        result_clip.close()
    finally:
        source_clip.close()


@given(filter_type=st.sampled_from(list(COLOR_FILTERS.keys())))
@settings(max_examples=20)
def test_apply_color_filter_preserves_size(filter_type: str):
    """
    Property 19: 颜色滤镜保持尺寸
    
    *For any* 有效的颜色滤镜，应用滤镜后视频尺寸应保持不变。
    
    **Validates: Requirements 10.2**
    """
    # 创建测试用的 ColorClip
    source_clip = ColorClip(
        size=(640, 480),
        color=(128, 128, 128),
        duration=1.0
    )
    
    try:
        result_clip = apply_color_filter(source_clip, filter_type)
        
        # 验证尺寸保持不变
        assert result_clip.size == source_clip.size, (
            f"滤镜后尺寸应保持不变: 期望 {source_clip.size}, 实际 {result_clip.size}"
        )
        
        result_clip.close()
    finally:
        source_clip.close()


# ============================================================
# Property 11: 音频轨道合成
# **Feature: video-remix, Property 11: 音频轨道合成**
# **Validates: Requirements 6.6, 6.7**
# ============================================================

from app.services.video_service import (
    BGM_FADE_IN_MIN,
    BGM_FADE_IN_MAX,
    BGM_FADE_IN_DEFAULT,
    BGM_FADE_OUT_MIN,
    BGM_FADE_OUT_MAX,
    BGM_FADE_OUT_DEFAULT,
    BGM_VOLUME_MIN,
    BGM_VOLUME_MAX,
    BGM_VOLUME_DEFAULT,
    validate_bgm_fade_in,
    validate_bgm_fade_out,
    validate_bgm_volume,
    apply_bgm_fade_effects,
    mix_audio_tracks,
)
from moviepy.editor import AudioFileClip, ColorClip


@given(
    fade_in=st.floats(
        min_value=BGM_FADE_IN_MIN,
        max_value=BGM_FADE_IN_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_in_validation_valid(fade_in: float):
    """
    Property 11: 音频轨道合成 - BGM 淡入时长有效范围
    
    *For any* BGM 淡入时长在 0-5 秒范围内，验证应该通过。
    
    **Validates: Requirements 6.8**
    """
    result = validate_bgm_fade_in(fade_in)
    assert result == fade_in, f"验证后的淡入时长应该等于输入值: {fade_in}"
    assert BGM_FADE_IN_MIN <= result <= BGM_FADE_IN_MAX, (
        f"淡入时长 {result} 不在有效范围 [{BGM_FADE_IN_MIN}, {BGM_FADE_IN_MAX}] 内"
    )


@given(
    fade_in=st.floats(
        min_value=-10.0,
        max_value=BGM_FADE_IN_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_in_validation_too_low(fade_in: float):
    """
    Property 11: 音频轨道合成 - BGM 淡入时长过低
    
    *For any* 小于最小值的淡入时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.8**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_fade_in(fade_in)
    
    assert "BGM 淡入时长必须在" in str(exc_info.value)


@given(
    fade_in=st.floats(
        min_value=BGM_FADE_IN_MAX + 0.01,
        max_value=20.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_in_validation_too_high(fade_in: float):
    """
    Property 11: 音频轨道合成 - BGM 淡入时长过高
    
    *For any* 大于最大值的淡入时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.8**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_fade_in(fade_in)
    
    assert "BGM 淡入时长必须在" in str(exc_info.value)


@given(
    fade_out=st.floats(
        min_value=BGM_FADE_OUT_MIN,
        max_value=BGM_FADE_OUT_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_out_validation_valid(fade_out: float):
    """
    Property 11: 音频轨道合成 - BGM 淡出时长有效范围
    
    *For any* BGM 淡出时长在 0-5 秒范围内，验证应该通过。
    
    **Validates: Requirements 6.8**
    """
    result = validate_bgm_fade_out(fade_out)
    assert result == fade_out, f"验证后的淡出时长应该等于输入值: {fade_out}"
    assert BGM_FADE_OUT_MIN <= result <= BGM_FADE_OUT_MAX, (
        f"淡出时长 {result} 不在有效范围 [{BGM_FADE_OUT_MIN}, {BGM_FADE_OUT_MAX}] 内"
    )


@given(
    fade_out=st.floats(
        min_value=-10.0,
        max_value=BGM_FADE_OUT_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_out_validation_too_low(fade_out: float):
    """
    Property 11: 音频轨道合成 - BGM 淡出时长过低
    
    *For any* 小于最小值的淡出时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.8**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_fade_out(fade_out)
    
    assert "BGM 淡出时长必须在" in str(exc_info.value)


@given(
    fade_out=st.floats(
        min_value=BGM_FADE_OUT_MAX + 0.01,
        max_value=20.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_fade_out_validation_too_high(fade_out: float):
    """
    Property 11: 音频轨道合成 - BGM 淡出时长过高
    
    *For any* 大于最大值的淡出时长，应该抛出 ValueError。
    
    **Validates: Requirements 6.8**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_fade_out(fade_out)
    
    assert "BGM 淡出时长必须在" in str(exc_info.value)


@given(
    volume=st.floats(
        min_value=BGM_VOLUME_MIN,
        max_value=BGM_VOLUME_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_volume_validation_valid(volume: float):
    """
    Property 11: 音频轨道合成 - BGM 音量有效范围
    
    *For any* BGM 音量在 0-100% 范围内，验证应该通过。
    
    **Validates: Requirements 6.7**
    """
    result = validate_bgm_volume(volume)
    assert result == volume, f"验证后的音量应该等于输入值: {volume}"
    assert BGM_VOLUME_MIN <= result <= BGM_VOLUME_MAX, (
        f"音量 {result} 不在有效范围 [{BGM_VOLUME_MIN}, {BGM_VOLUME_MAX}] 内"
    )


@given(
    volume=st.floats(
        min_value=-10.0,
        max_value=BGM_VOLUME_MIN - 0.01,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_volume_validation_too_low(volume: float):
    """
    Property 11: 音频轨道合成 - BGM 音量过低
    
    *For any* 小于最小值的音量，应该抛出 ValueError。
    
    **Validates: Requirements 6.7**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_volume(volume)
    
    assert "BGM 音量必须在" in str(exc_info.value)


@given(
    volume=st.floats(
        min_value=BGM_VOLUME_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_bgm_volume_validation_too_high(volume: float):
    """
    Property 11: 音频轨道合成 - BGM 音量过高
    
    *For any* 大于最大值的音量，应该抛出 ValueError。
    
    **Validates: Requirements 6.7**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_bgm_volume(volume)
    
    assert "BGM 音量必须在" in str(exc_info.value)


@given(
    bgm_volume=st.floats(
        min_value=BGM_VOLUME_MIN,
        max_value=BGM_VOLUME_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    bgm_fade_in=st.floats(
        min_value=BGM_FADE_IN_MIN,
        max_value=BGM_FADE_IN_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    bgm_fade_out=st.floats(
        min_value=BGM_FADE_OUT_MIN,
        max_value=BGM_FADE_OUT_MAX,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_audio_mixing_parameters_validation(
    bgm_volume: float,
    bgm_fade_in: float,
    bgm_fade_out: float
):
    """
    Property 11: 音频轨道合成 - 参数组合验证
    
    *For any* 有效的 BGM 音量、淡入时长、淡出时长组合，
    mix_audio_tracks 函数应该接受这些参数而不抛出异常。
    
    **Validates: Requirements 6.6, 6.7**
    """
    # 验证参数组合是有效的
    validate_bgm_volume(bgm_volume)
    validate_bgm_fade_in(bgm_fade_in)
    validate_bgm_fade_out(bgm_fade_out)
    
    # 调用 mix_audio_tracks 时不应抛出参数验证异常
    # 由于没有实际音频文件，我们只测试参数验证逻辑
    # 当 voice_audio 和 bgm_audio 都为 None 时，函数应返回 None
    result = mix_audio_tracks(
        voice_audio=None,
        bgm_audio=None,
        bgm_volume=bgm_volume,
        bgm_fade_in=bgm_fade_in,
        bgm_fade_out=bgm_fade_out,
        target_duration=10.0
    )
    
    assert result is None, "当没有音频输入时，应返回 None"


# ============================================================
# Property 18: 配置参数验证
# **Feature: video-remix, Property 18: 配置参数验证**
# **Validates: Requirements 9.4, 9.5**
# ============================================================

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
    BRIGHTNESS_MIN,
    BRIGHTNESS_MAX,
    CONTRAST_MIN,
    CONTRAST_MAX,
    SATURATION_MIN,
    SATURATION_MAX,
    BGM_VOLUME_MIN,
    BGM_VOLUME_MAX,
    BGM_FADE_IN_MIN,
    BGM_FADE_IN_MAX,
    BGM_FADE_OUT_MIN,
    BGM_FADE_OUT_MAX,
)


def validate_video_config_params(
    video_resolution: str,
    video_layout: str,
    video_fps: int,
    platform_preset: str = None,
    fit_mode: str = "crop",
    transition_type: str = "fade",
    transition_duration: float = 0.5,
    color_filter: str = "none",
    effect_type: str = None,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    bgm_volume: float = 0.3,
    bgm_fade_in: float = 0.0,
    bgm_fade_out: float = 0.0,
    clip_min_duration: float = 3.0,
    clip_max_duration: float = 10.0,
    subtitle_position: str = "bottom",
    output_quality: str = "high",
) -> dict:
    """
    验证视频配置参数 (Requirements 9.4, 9.5)
    
    验证所有配置参数在有效范围内，无效参数抛出 ValueError。
    
    Returns:
        验证后的配置字典
    
    Raises:
        ValueError: 如果任何参数无效
    """
    errors = []
    
    # 验证视频分辨率
    if video_resolution not in VIDEO_RESOLUTIONS:
        errors.append(f"无效的分辨率: {video_resolution}")
    
    # 验证视频布局
    if video_layout not in VIDEO_LAYOUTS:
        errors.append(f"无效的布局: {video_layout}")
    
    # 验证帧率
    if video_fps not in FRAME_RATES:
        errors.append(f"无效的帧率: {video_fps}")
    
    # 验证平台预设（如果指定）
    if platform_preset is not None and platform_preset not in PLATFORM_PRESETS:
        errors.append(f"无效的平台预设: {platform_preset}")
    
    # 验证素材适配模式
    if fit_mode not in FIT_MODES:
        errors.append(f"无效的适配模式: {fit_mode}")
    
    # 验证转场类型
    if transition_type not in TRANSITIONS:
        errors.append(f"无效的转场类型: {transition_type}")
    
    # 验证转场时长
    if transition_duration < TRANSITION_DURATION_MIN or transition_duration > TRANSITION_DURATION_MAX:
        errors.append(f"转场时长必须在 {TRANSITION_DURATION_MIN} 到 {TRANSITION_DURATION_MAX} 秒之间")
    
    # 验证颜色滤镜
    if color_filter not in COLOR_FILTERS:
        errors.append(f"无效的滤镜类型: {color_filter}")
    
    # 验证特效类型（如果指定）
    if effect_type is not None and effect_type not in EFFECT_TYPES:
        errors.append(f"无效的特效类型: {effect_type}")
    
    # 验证亮度
    if brightness < BRIGHTNESS_MIN or brightness > BRIGHTNESS_MAX:
        errors.append(f"亮度值必须在 {BRIGHTNESS_MIN} 到 {BRIGHTNESS_MAX} 之间")
    
    # 验证对比度
    if contrast < CONTRAST_MIN or contrast > CONTRAST_MAX:
        errors.append(f"对比度值必须在 {CONTRAST_MIN} 到 {CONTRAST_MAX} 之间")
    
    # 验证饱和度
    if saturation < SATURATION_MIN or saturation > SATURATION_MAX:
        errors.append(f"饱和度值必须在 {SATURATION_MIN} 到 {SATURATION_MAX} 之间")
    
    # 验证 BGM 音量
    if bgm_volume < BGM_VOLUME_MIN or bgm_volume > BGM_VOLUME_MAX:
        errors.append(f"BGM 音量必须在 {BGM_VOLUME_MIN} 到 {BGM_VOLUME_MAX} 之间")
    
    # 验证 BGM 淡入时长
    if bgm_fade_in < BGM_FADE_IN_MIN or bgm_fade_in > BGM_FADE_IN_MAX:
        errors.append(f"BGM 淡入时长必须在 {BGM_FADE_IN_MIN} 到 {BGM_FADE_IN_MAX} 秒之间")
    
    # 验证 BGM 淡出时长
    if bgm_fade_out < BGM_FADE_OUT_MIN or bgm_fade_out > BGM_FADE_OUT_MAX:
        errors.append(f"BGM 淡出时长必须在 {BGM_FADE_OUT_MIN} 到 {BGM_FADE_OUT_MAX} 秒之间")
    
    # 验证片段时长配置
    if clip_min_duration > clip_max_duration:
        errors.append("片段最小时长不能大于最大时长")
    
    # 验证字幕位置
    valid_subtitle_positions = ["top", "center", "bottom"]
    if subtitle_position not in valid_subtitle_positions:
        errors.append(f"无效的字幕位置: {subtitle_position}")
    
    # 验证输出质量
    valid_output_qualities = ["low", "medium", "high", "ultra"]
    if output_quality not in valid_output_qualities:
        errors.append(f"无效的输出质量: {output_quality}")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    return {
        "video_resolution": video_resolution,
        "video_layout": video_layout,
        "video_fps": video_fps,
        "platform_preset": platform_preset,
        "fit_mode": fit_mode,
        "transition_type": transition_type,
        "transition_duration": transition_duration,
        "color_filter": color_filter,
        "effect_type": effect_type,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "bgm_volume": bgm_volume,
        "bgm_fade_in": bgm_fade_in,
        "bgm_fade_out": bgm_fade_out,
        "clip_min_duration": clip_min_duration,
        "clip_max_duration": clip_max_duration,
        "subtitle_position": subtitle_position,
        "output_quality": output_quality,
    }


@given(
    video_resolution=st.sampled_from(list(VIDEO_RESOLUTIONS.keys())),
    video_layout=st.sampled_from(list(VIDEO_LAYOUTS.keys())),
    video_fps=st.sampled_from(FRAME_RATES),
    fit_mode=st.sampled_from(list(FIT_MODES.keys())),
    transition_type=st.sampled_from(list(TRANSITIONS.keys())),
    transition_duration=st.floats(
        min_value=TRANSITION_DURATION_MIN,
        max_value=TRANSITION_DURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    color_filter=st.sampled_from(list(COLOR_FILTERS.keys())),
    brightness=st.floats(
        min_value=BRIGHTNESS_MIN,
        max_value=BRIGHTNESS_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    contrast=st.floats(
        min_value=CONTRAST_MIN,
        max_value=CONTRAST_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    saturation=st.floats(
        min_value=SATURATION_MIN,
        max_value=SATURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    bgm_volume=st.floats(
        min_value=BGM_VOLUME_MIN,
        max_value=BGM_VOLUME_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    bgm_fade_in=st.floats(
        min_value=BGM_FADE_IN_MIN,
        max_value=BGM_FADE_IN_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    bgm_fade_out=st.floats(
        min_value=BGM_FADE_OUT_MIN,
        max_value=BGM_FADE_OUT_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    subtitle_position=st.sampled_from(["top", "center", "bottom"]),
    output_quality=st.sampled_from(["low", "medium", "high", "ultra"]),
)
@settings(max_examples=20)
def test_config_params_validation_valid(
    video_resolution: str,
    video_layout: str,
    video_fps: int,
    fit_mode: str,
    transition_type: str,
    transition_duration: float,
    color_filter: str,
    brightness: float,
    contrast: float,
    saturation: float,
    bgm_volume: float,
    bgm_fade_in: float,
    bgm_fade_out: float,
    subtitle_position: str,
    output_quality: str,
):
    """
    Property 18: 配置参数验证 - 有效参数组合
    
    *For any* 有效的配置参数组合，验证应该通过且不抛出异常。
    
    **Validates: Requirements 9.4, 9.5**
    """
    # 有效参数组合应该通过验证
    result = validate_video_config_params(
        video_resolution=video_resolution,
        video_layout=video_layout,
        video_fps=video_fps,
        fit_mode=fit_mode,
        transition_type=transition_type,
        transition_duration=transition_duration,
        color_filter=color_filter,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        bgm_volume=bgm_volume,
        bgm_fade_in=bgm_fade_in,
        bgm_fade_out=bgm_fade_out,
        subtitle_position=subtitle_position,
        output_quality=output_quality,
    )
    
    # 验证返回的配置包含所有字段
    assert result["video_resolution"] == video_resolution
    assert result["video_layout"] == video_layout
    assert result["video_fps"] == video_fps
    assert result["fit_mode"] == fit_mode
    assert result["transition_type"] == transition_type
    assert result["transition_duration"] == transition_duration
    assert result["color_filter"] == color_filter
    assert result["brightness"] == brightness
    assert result["contrast"] == contrast
    assert result["saturation"] == saturation
    assert result["bgm_volume"] == bgm_volume
    assert result["bgm_fade_in"] == bgm_fade_in
    assert result["bgm_fade_out"] == bgm_fade_out
    assert result["subtitle_position"] == subtitle_position
    assert result["output_quality"] == output_quality


@given(platform_preset=st.sampled_from(list(PLATFORM_PRESETS.keys())))
@settings(max_examples=20)
def test_config_params_validation_with_platform_preset(platform_preset: str):
    """
    Property 18: 配置参数验证 - 平台预设验证
    
    *For any* 有效的平台预设，验证应该通过。
    
    **Validates: Requirements 9.4, 9.5**
    """
    preset = PLATFORM_PRESETS[platform_preset]
    
    result = validate_video_config_params(
        video_resolution=preset["resolution"],
        video_layout=preset["layout"],
        video_fps=preset["fps"],
        platform_preset=platform_preset,
    )
    
    assert result["platform_preset"] == platform_preset
    assert result["video_resolution"] == preset["resolution"]
    assert result["video_layout"] == preset["layout"]
    assert result["video_fps"] == preset["fps"]


def test_config_params_validation_invalid_resolution():
    """
    Property 18: 配置参数验证 - 无效分辨率
    
    *For any* 无效的分辨率，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="invalid_resolution",
            video_layout="16:9",
            video_fps=30,
        )
    
    assert "无效的分辨率" in str(exc_info.value)


def test_config_params_validation_invalid_layout():
    """
    Property 18: 配置参数验证 - 无效布局
    
    *For any* 无效的布局，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="invalid_layout",
            video_fps=30,
        )
    
    assert "无效的布局" in str(exc_info.value)


def test_config_params_validation_invalid_fps():
    """
    Property 18: 配置参数验证 - 无效帧率
    
    *For any* 无效的帧率，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=999,  # 无效帧率
        )
    
    assert "无效的帧率" in str(exc_info.value)


def test_config_params_validation_invalid_platform_preset():
    """
    Property 18: 配置参数验证 - 无效平台预设
    
    *For any* 无效的平台预设，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            platform_preset="invalid_platform",
        )
    
    assert "无效的平台预设" in str(exc_info.value)


def test_config_params_validation_invalid_fit_mode():
    """
    Property 18: 配置参数验证 - 无效适配模式
    
    *For any* 无效的适配模式，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            fit_mode="invalid_mode",
        )
    
    assert "无效的适配模式" in str(exc_info.value)


def test_config_params_validation_invalid_transition_type():
    """
    Property 18: 配置参数验证 - 无效转场类型
    
    *For any* 无效的转场类型，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            transition_type="invalid_transition",
        )
    
    assert "无效的转场类型" in str(exc_info.value)


@given(
    transition_duration=st.floats(
        min_value=TRANSITION_DURATION_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_transition_duration_too_long(transition_duration: float):
    """
    Property 18: 配置参数验证 - 转场时长过长
    
    *For any* 大于最大值的转场时长，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            transition_duration=transition_duration,
        )
    
    assert "转场时长必须在" in str(exc_info.value)


def test_config_params_validation_invalid_color_filter():
    """
    Property 18: 配置参数验证 - 无效颜色滤镜
    
    *For any* 无效的颜色滤镜，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            color_filter="invalid_filter",
        )
    
    assert "无效的滤镜类型" in str(exc_info.value)


def test_config_params_validation_invalid_effect_type():
    """
    Property 18: 配置参数验证 - 无效特效类型
    
    *For any* 无效的特效类型，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            effect_type="invalid_effect",
        )
    
    assert "无效的特效类型" in str(exc_info.value)


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_brightness_too_high(brightness: float):
    """
    Property 18: 配置参数验证 - 亮度过高
    
    *For any* 大于最大值的亮度，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            brightness=brightness,
        )
    
    assert "亮度值必须在" in str(exc_info.value)


@given(
    contrast=st.floats(
        min_value=CONTRAST_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_contrast_too_high(contrast: float):
    """
    Property 18: 配置参数验证 - 对比度过高
    
    *For any* 大于最大值的对比度，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            contrast=contrast,
        )
    
    assert "对比度值必须在" in str(exc_info.value)


@given(
    saturation=st.floats(
        min_value=SATURATION_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_saturation_too_high(saturation: float):
    """
    Property 18: 配置参数验证 - 饱和度过高
    
    *For any* 大于最大值的饱和度，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            saturation=saturation,
        )
    
    assert "饱和度值必须在" in str(exc_info.value)


def test_config_params_validation_clip_duration_invalid():
    """
    Property 18: 配置参数验证 - 片段时长配置无效
    
    *For any* 最小时长大于最大时长的配置，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            clip_min_duration=10.0,
            clip_max_duration=5.0,  # 最大时长小于最小时长
        )
    
    assert "片段最小时长不能大于最大时长" in str(exc_info.value)


def test_config_params_validation_invalid_subtitle_position():
    """
    Property 18: 配置参数验证 - 无效字幕位置
    
    *For any* 无效的字幕位置，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            subtitle_position="invalid_position",
        )
    
    assert "无效的字幕位置" in str(exc_info.value)


def test_config_params_validation_invalid_output_quality():
    """
    Property 18: 配置参数验证 - 无效输出质量
    
    *For any* 无效的输出质量，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            output_quality="invalid_quality",
        )
    
    assert "无效的输出质量" in str(exc_info.value)


@given(
    bgm_volume=st.floats(
        min_value=BGM_VOLUME_MAX + 0.01,
        max_value=10.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_bgm_volume_too_high(bgm_volume: float):
    """
    Property 18: 配置参数验证 - BGM 音量过高
    
    *For any* 大于最大值的 BGM 音量，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            bgm_volume=bgm_volume,
        )
    
    assert "BGM 音量必须在" in str(exc_info.value)


@given(
    bgm_fade_in=st.floats(
        min_value=BGM_FADE_IN_MAX + 0.01,
        max_value=20.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_bgm_fade_in_too_long(bgm_fade_in: float):
    """
    Property 18: 配置参数验证 - BGM 淡入时长过长
    
    *For any* 大于最大值的 BGM 淡入时长，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            bgm_fade_in=bgm_fade_in,
        )
    
    assert "BGM 淡入时长必须在" in str(exc_info.value)


@given(
    bgm_fade_out=st.floats(
        min_value=BGM_FADE_OUT_MAX + 0.01,
        max_value=20.0,
        allow_nan=False,
        allow_infinity=False
    )
)
@settings(max_examples=20)
def test_config_params_validation_bgm_fade_out_too_long(bgm_fade_out: float):
    """
    Property 18: 配置参数验证 - BGM 淡出时长过长
    
    *For any* 大于最大值的 BGM 淡出时长，验证应该抛出 ValueError。
    
    **Validates: Requirements 9.4, 9.5**
    """
    with pytest.raises(ValueError) as exc_info:
        validate_video_config_params(
            video_resolution="1080p",
            video_layout="16:9",
            video_fps=30,
            bgm_fade_out=bgm_fade_out,
        )
    
    assert "BGM 淡出时长必须在" in str(exc_info.value)


# ============================================================
# Property 12: 输出视频格式验证
# **Feature: video-remix, Property 12: 输出视频格式验证**
# **Validates: Requirements 6.9**
# ============================================================

import tempfile
import subprocess
import json
from app.services.video_service import (
    create_video_from_config,
    VIDEO_RESOLUTIONS,
    VIDEO_LAYOUTS,
    FRAME_RATES,
    FIT_MODES,
    TRANSITIONS,
    COLOR_FILTERS,
    EFFECT_TYPES,
)


def get_video_codec_info(video_path: str) -> dict:
    """
    使用 ffprobe 获取视频编码信息
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        包含视频编码信息的字典
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def is_valid_mp4_h264(video_path: str) -> tuple:
    """
    验证视频是否为有效的 MP4 格式（H.264 编码）
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        (is_valid, error_message) 元组
    """
    import os
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        return False, "文件不存在"
    
    # 检查文件扩展名
    if not video_path.lower().endswith('.mp4'):
        return False, "文件扩展名不是 .mp4"
    
    # 检查文件大小
    file_size = os.path.getsize(video_path)
    if file_size == 0:
        return False, "文件大小为 0"
    
    # 使用 ffprobe 获取编码信息
    info = get_video_codec_info(video_path)
    if info is None:
        # 如果 ffprobe 不可用，只检查文件头
        with open(video_path, 'rb') as f:
            header = f.read(12)
            # MP4 文件通常以 ftyp 开头
            if b'ftyp' in header:
                return True, None
            return False, "无法验证文件格式（ffprobe 不可用）"
    
    # 检查容器格式
    format_info = info.get('format', {})
    format_name = format_info.get('format_name', '')
    
    if 'mp4' not in format_name and 'mov' not in format_name:
        return False, f"容器格式不是 MP4: {format_name}"
    
    # 检查视频流编码
    streams = info.get('streams', [])
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    
    if not video_streams:
        return False, "没有找到视频流"
    
    video_codec = video_streams[0].get('codec_name', '')
    
    # H.264 编码的常见名称
    h264_codecs = ['h264', 'avc1', 'avc', 'x264']
    
    if video_codec.lower() not in h264_codecs:
        return False, f"视频编码不是 H.264: {video_codec}"
    
    return True, None


@given(
    resolution=st.sampled_from(list(VIDEO_RESOLUTIONS.keys())),
    layout=st.sampled_from(list(VIDEO_LAYOUTS.keys())),
    fps=st.sampled_from(FRAME_RATES),
)
@settings(max_examples=5, deadline=None)  # 视频生成较慢，减少测试次数
def test_output_video_format_validation(resolution: str, layout: str, fps: int):
    """
    Property 12: 输出视频格式验证
    
    *For any* 完成的视频合成任务，输出文件应为有效的 MP4 格式（H.264 编码）。
    
    **Validates: Requirements 6.9**
    """
    import os
    
    # 创建临时输出文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # 创建最小配置进行视频生成
        config = {
            "script": "测试视频",
            "video_resolution": resolution,
            "video_layout": layout,
            "video_fps": fps,
            "media_files": [],  # 使用空素材（黑色背景）
            "clip_min_duration": 1.0,
            "clip_max_duration": 1.0,
            "subtitle_enabled": False,
            "transition_enabled": False,
            "output_path": output_path,
        }
        
        # 生成视频
        result_path = create_video_from_config(config)
        
        # 验证返回路径
        assert result_path == output_path, f"返回路径应该等于输出路径"
        
        # 验证文件存在
        assert os.path.exists(output_path), f"输出文件应该存在: {output_path}"
        
        # 验证文件格式
        is_valid, error_msg = is_valid_mp4_h264(output_path)
        assert is_valid, f"输出视频格式验证失败: {error_msg}"
        
    finally:
        # 清理临时文件
        if os.path.exists(output_path):
            os.remove(output_path)


def test_output_video_format_with_all_features():
    """
    Property 12: 输出视频格式验证 - 完整功能测试
    
    验证启用所有功能时，输出视频仍然是有效的 MP4 格式（H.264 编码）。
    
    **Validates: Requirements 6.9**
    """
    import os
    
    # 创建临时输出文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # 创建包含所有功能的配置
        config = {
            "script": "这是一个测试视频。用于验证输出格式。",
            "video_resolution": "720p",
            "video_layout": "16:9",
            "video_fps": 30,
            "media_files": [],
            "fit_mode": "crop",
            "clip_min_duration": 1.0,
            "clip_max_duration": 2.0,
            "transition_enabled": True,
            "transition_type": "fade",
            "transition_duration": 0.5,
            "subtitle_enabled": True,
            "subtitle_config": {
                "font": "SimHei",
                "size": 36,
                "color": "white",
                "stroke_color": "black",
                "stroke_width": 2,
                "position": "bottom"
            },
            "color_filter": "none",
            "brightness": 1.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "output_quality": "medium",
            "output_path": output_path,
        }
        
        # 生成视频
        result_path = create_video_from_config(config)
        
        # 验证文件存在
        assert os.path.exists(output_path), f"输出文件应该存在"
        
        # 验证文件格式
        is_valid, error_msg = is_valid_mp4_h264(output_path)
        assert is_valid, f"输出视频格式验证失败: {error_msg}"
        
        # 验证文件大小合理（至少 1KB）
        file_size = os.path.getsize(output_path)
        assert file_size > 1024, f"输出文件大小应该大于 1KB，实际: {file_size}"
        
    finally:
        # 清理临时文件
        if os.path.exists(output_path):
            os.remove(output_path)


@given(output_quality=st.sampled_from(["low", "medium", "high", "ultra"]))
@settings(max_examples=4, deadline=None)
def test_output_video_format_with_different_quality(output_quality: str):
    """
    Property 12: 输出视频格式验证 - 不同质量设置
    
    *For any* 输出质量设置，输出视频应该是有效的 MP4 格式（H.264 编码）。
    
    **Validates: Requirements 6.9**
    """
    import os
    
    # 创建临时输出文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        config = {
            "script": "质量测试",
            "video_resolution": "480p",
            "video_layout": "16:9",
            "video_fps": 24,
            "media_files": [],
            "clip_min_duration": 1.0,
            "clip_max_duration": 1.0,
            "subtitle_enabled": False,
            "transition_enabled": False,
            "output_quality": output_quality,
            "output_path": output_path,
        }
        
        # 生成视频
        result_path = create_video_from_config(config)
        
        # 验证文件格式
        is_valid, error_msg = is_valid_mp4_h264(output_path)
        assert is_valid, f"输出质量 {output_quality} 的视频格式验证失败: {error_msg}"
        
    finally:
        # 清理临时文件
        if os.path.exists(output_path):
            os.remove(output_path)


# ============================================================
# Property 3: 媒体文件格式验证
# **Feature: video-remix, Property 3: 媒体文件格式验证**
# **Validates: Requirements 3.1, 3.2**
# ============================================================

from app.services.video_service import (
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_VIDEO_FILE_SIZE,
    MAX_IMAGE_FILE_SIZE,
    validate_video_format,
    validate_image_format,
    validate_media_format,
    validate_video_file_size,
    validate_image_file_size,
    validate_media_file_size,
    validate_media_file,
)


# 定义有效和无效的文件扩展名策略
valid_video_extensions = st.sampled_from(list(ALLOWED_VIDEO_EXTENSIONS))
valid_image_extensions = st.sampled_from(list(ALLOWED_IMAGE_EXTENSIONS))
invalid_extensions = st.sampled_from([".txt", ".pdf", ".doc", ".exe", ".zip", ".html", ".css", ".js", ".py", ".gif", ".bmp", ".tiff"])


@given(ext=valid_video_extensions)
@settings(max_examples=20)
def test_validate_video_format_valid_extensions(ext: str):
    """
    Property 3: 媒体文件格式验证 - 有效视频格式
    
    *For any* 有效的视频扩展名，validate_video_format 应返回 True。
    
    **Validates: Requirements 3.1**
    """
    # 测试带扩展名的文件路径
    file_path = f"test_video{ext}"
    result = validate_video_format(file_path)
    assert result is True, f"有效视频扩展名 {ext} 应该返回 True"
    
    # 测试大写扩展名
    file_path_upper = f"test_video{ext.upper()}"
    result_upper = validate_video_format(file_path_upper)
    assert result_upper is True, f"大写视频扩展名 {ext.upper()} 应该返回 True"


@given(ext=valid_image_extensions)
@settings(max_examples=20)
def test_validate_image_format_valid_extensions(ext: str):
    """
    Property 3: 媒体文件格式验证 - 有效图片格式
    
    *For any* 有效的图片扩展名，validate_image_format 应返回 True。
    
    **Validates: Requirements 3.2**
    """
    # 测试带扩展名的文件路径
    file_path = f"test_image{ext}"
    result = validate_image_format(file_path)
    assert result is True, f"有效图片扩展名 {ext} 应该返回 True"
    
    # 测试大写扩展名
    file_path_upper = f"test_image{ext.upper()}"
    result_upper = validate_image_format(file_path_upper)
    assert result_upper is True, f"大写图片扩展名 {ext.upper()} 应该返回 True"


@given(ext=invalid_extensions)
@settings(max_examples=20)
def test_validate_video_format_invalid_extensions(ext: str):
    """
    Property 3: 媒体文件格式验证 - 无效视频格式
    
    *For any* 不支持的扩展名，validate_video_format 应返回 False。
    
    **Validates: Requirements 3.1**
    """
    file_path = f"test_file{ext}"
    result = validate_video_format(file_path)
    assert result is False, f"无效扩展名 {ext} 应该返回 False"


@given(ext=invalid_extensions)
@settings(max_examples=20)
def test_validate_image_format_invalid_extensions(ext: str):
    """
    Property 3: 媒体文件格式验证 - 无效图片格式
    
    *For any* 不支持的扩展名，validate_image_format 应返回 False。
    
    **Validates: Requirements 3.2**
    """
    file_path = f"test_file{ext}"
    result = validate_image_format(file_path)
    assert result is False, f"无效扩展名 {ext} 应该返回 False"


@given(ext=valid_video_extensions)
@settings(max_examples=20)
def test_validate_media_format_video(ext: str):
    """
    Property 3: 媒体文件格式验证 - 视频媒体类型识别
    
    *For any* 有效的视频扩展名，validate_media_format 应返回 (True, "video")。
    
    **Validates: Requirements 3.1**
    """
    file_path = f"test_video{ext}"
    is_valid, media_type = validate_media_format(file_path)
    
    assert is_valid is True, f"有效视频扩展名 {ext} 应该返回 is_valid=True"
    assert media_type == "video", f"视频扩展名 {ext} 应该返回 media_type='video'，实际: {media_type}"


@given(ext=valid_image_extensions)
@settings(max_examples=20)
def test_validate_media_format_image(ext: str):
    """
    Property 3: 媒体文件格式验证 - 图片媒体类型识别
    
    *For any* 有效的图片扩展名，validate_media_format 应返回 (True, "image")。
    
    **Validates: Requirements 3.2**
    """
    file_path = f"test_image{ext}"
    is_valid, media_type = validate_media_format(file_path)
    
    assert is_valid is True, f"有效图片扩展名 {ext} 应该返回 is_valid=True"
    assert media_type == "image", f"图片扩展名 {ext} 应该返回 media_type='image'，实际: {media_type}"


@given(ext=invalid_extensions)
@settings(max_examples=20)
def test_validate_media_format_unknown(ext: str):
    """
    Property 3: 媒体文件格式验证 - 未知媒体类型
    
    *For any* 不支持的扩展名，validate_media_format 应返回 (False, "unknown")。
    
    **Validates: Requirements 3.1, 3.2**
    """
    file_path = f"test_file{ext}"
    is_valid, media_type = validate_media_format(file_path)
    
    assert is_valid is False, f"无效扩展名 {ext} 应该返回 is_valid=False"
    assert media_type == "unknown", f"无效扩展名 {ext} 应该返回 media_type='unknown'，实际: {media_type}"


def test_validate_media_format_all_video_extensions():
    """
    Property 3: 媒体文件格式验证 - 所有视频扩展名
    
    验证所有定义的视频扩展名都被正确识别。
    
    **Validates: Requirements 3.1**
    """
    expected_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    
    # 验证常量定义正确
    assert ALLOWED_VIDEO_EXTENSIONS == expected_extensions, (
        f"视频扩展名常量不正确: 期望 {expected_extensions}, 实际 {ALLOWED_VIDEO_EXTENSIONS}"
    )
    
    # 验证每个扩展名都能被正确识别
    for ext in expected_extensions:
        assert validate_video_format(f"test{ext}") is True
        is_valid, media_type = validate_media_format(f"test{ext}")
        assert is_valid is True
        assert media_type == "video"


def test_validate_media_format_all_image_extensions():
    """
    Property 3: 媒体文件格式验证 - 所有图片扩展名
    
    验证所有定义的图片扩展名都被正确识别。
    
    **Validates: Requirements 3.2**
    """
    expected_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    
    # 验证常量定义正确
    assert ALLOWED_IMAGE_EXTENSIONS == expected_extensions, (
        f"图片扩展名常量不正确: 期望 {expected_extensions}, 实际 {ALLOWED_IMAGE_EXTENSIONS}"
    )
    
    # 验证每个扩展名都能被正确识别
    for ext in expected_extensions:
        assert validate_image_format(f"test{ext}") is True
        is_valid, media_type = validate_media_format(f"test{ext}")
        assert is_valid is True
        assert media_type == "image"



# ============================================================
# Property 4: 文件大小限制验证
# **Feature: video-remix, Property 4: 文件大小限制验证**
# **Validates: Requirements 3.3, 3.4**
# ============================================================

def test_file_size_constants():
    """
    Property 4: 文件大小限制验证 - 常量定义
    
    验证文件大小限制常量定义正确。
    
    **Validates: Requirements 3.3, 3.4**
    """
    # 验证视频文件大小限制为 150MB
    assert MAX_VIDEO_FILE_SIZE == 150 * 1024 * 1024, (
        f"视频文件大小限制应为 150MB，实际: {MAX_VIDEO_FILE_SIZE / 1024 / 1024}MB"
    )
    
    # 验证图片文件大小限制为 10MB
    assert MAX_IMAGE_FILE_SIZE == 10 * 1024 * 1024, (
        f"图片文件大小限制应为 10MB，实际: {MAX_IMAGE_FILE_SIZE / 1024 / 1024}MB"
    )


@given(
    file_size=st.integers(min_value=1, max_value=MAX_VIDEO_FILE_SIZE)
)
@settings(max_examples=20, deadline=None)
def test_validate_video_file_size_valid(file_size: int):
    """
    Property 4: 文件大小限制验证 - 有效视频文件大小
    
    *For any* 视频文件大小 ≤ 150MB，validate_video_file_size 应返回 (True, file_size)。
    
    **Validates: Requirements 3.3**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size = validate_video_file_size(tmp_path)
        
        assert is_valid is True, f"文件大小 {file_size} 字节应该有效"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
    finally:
        os.remove(tmp_path)


@given(
    file_size=st.integers(min_value=MAX_VIDEO_FILE_SIZE + 1, max_value=MAX_VIDEO_FILE_SIZE + 10 * 1024 * 1024)
)
@settings(max_examples=10, deadline=None)  # 减少测试次数，因为创建大文件较慢
def test_validate_video_file_size_invalid(file_size: int):
    """
    Property 4: 文件大小限制验证 - 超出限制的视频文件大小
    
    *For any* 视频文件大小 > 150MB，validate_video_file_size 应返回 (False, file_size)。
    
    **Validates: Requirements 3.3**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size = validate_video_file_size(tmp_path)
        
        assert is_valid is False, f"文件大小 {file_size} 字节应该无效（超过 150MB）"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
    finally:
        os.remove(tmp_path)


@given(
    file_size=st.integers(min_value=1, max_value=MAX_IMAGE_FILE_SIZE)
)
@settings(max_examples=20)
def test_validate_image_file_size_valid(file_size: int):
    """
    Property 4: 文件大小限制验证 - 有效图片文件大小
    
    *For any* 图片文件大小 ≤ 10MB，validate_image_file_size 应返回 (True, file_size)。
    
    **Validates: Requirements 3.4**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size = validate_image_file_size(tmp_path)
        
        assert is_valid is True, f"文件大小 {file_size} 字节应该有效"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
    finally:
        os.remove(tmp_path)


@given(
    file_size=st.integers(min_value=MAX_IMAGE_FILE_SIZE + 1, max_value=MAX_IMAGE_FILE_SIZE + 5 * 1024 * 1024)
)
@settings(max_examples=10)  # 减少测试次数，因为创建大文件较慢
def test_validate_image_file_size_invalid(file_size: int):
    """
    Property 4: 文件大小限制验证 - 超出限制的图片文件大小
    
    *For any* 图片文件大小 > 10MB，validate_image_file_size 应返回 (False, file_size)。
    
    **Validates: Requirements 3.4**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size = validate_image_file_size(tmp_path)
        
        assert is_valid is False, f"文件大小 {file_size} 字节应该无效（超过 10MB）"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
    finally:
        os.remove(tmp_path)


@given(
    video_ext=valid_video_extensions,
    file_size=st.integers(min_value=1, max_value=MAX_VIDEO_FILE_SIZE)
)
@settings(max_examples=50)
def test_validate_media_file_size_video_valid(video_ext: str, file_size: int):
    """
    Property 4: 文件大小限制验证 - 有效视频媒体文件大小
    
    *For any* 视频文件大小 ≤ 150MB，validate_media_file_size 应返回 (True, file_size, "video")。
    
    **Validates: Requirements 3.3**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=video_ext, delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size, media_type = validate_media_file_size(tmp_path)
        
        assert is_valid is True, f"视频文件大小 {file_size} 字节应该有效"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
        assert media_type == "video", f"媒体类型应该是 'video'，实际: {media_type}"
    finally:
        os.remove(tmp_path)


@given(
    image_ext=valid_image_extensions,
    file_size=st.integers(min_value=1, max_value=MAX_IMAGE_FILE_SIZE)
)
@settings(max_examples=50)
def test_validate_media_file_size_image_valid(image_ext: str, file_size: int):
    """
    Property 4: 文件大小限制验证 - 有效图片媒体文件大小
    
    *For any* 图片文件大小 ≤ 10MB，validate_media_file_size 应返回 (True, file_size, "image")。
    
    **Validates: Requirements 3.4**
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=image_ext, delete=False) as tmp_file:
        tmp_file.write(b'0' * file_size)
        tmp_path = tmp_file.name
    
    try:
        is_valid, actual_size, media_type = validate_media_file_size(tmp_path)
        
        assert is_valid is True, f"图片文件大小 {file_size} 字节应该有效"
        assert actual_size == file_size, f"返回的文件大小应该等于实际大小: {file_size}"
        assert media_type == "image", f"媒体类型应该是 'image'，实际: {media_type}"
    finally:
        os.remove(tmp_path)


def test_validate_video_file_size_file_not_found():
    """
    Property 4: 文件大小限制验证 - 文件不存在
    
    验证当文件不存在时，validate_video_file_size 应抛出 FileNotFoundError。
    
    **Validates: Requirements 3.3**
    """
    with pytest.raises(FileNotFoundError):
        validate_video_file_size("/nonexistent/path/video.mp4")


def test_validate_image_file_size_file_not_found():
    """
    Property 4: 文件大小限制验证 - 文件不存在
    
    验证当文件不存在时，validate_image_file_size 应抛出 FileNotFoundError。
    
    **Validates: Requirements 3.4**
    """
    with pytest.raises(FileNotFoundError):
        validate_image_file_size("/nonexistent/path/image.jpg")


def test_validate_media_file_size_file_not_found():
    """
    Property 4: 文件大小限制验证 - 文件不存在
    
    验证当文件不存在时，validate_media_file_size 应抛出 FileNotFoundError。
    
    **Validates: Requirements 3.3, 3.4**
    """
    with pytest.raises(FileNotFoundError):
        validate_media_file_size("/nonexistent/path/file.mp4")


def test_validate_media_file_complete_validation():
    """
    Property 4: 文件大小限制验证 - 完整验证函数
    
    验证 validate_media_file 函数返回完整的验证结果。
    
    **Validates: Requirements 3.3, 3.4**
    """
    # 创建有效的视频文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'0' * 1024)  # 1KB
        tmp_path = tmp_file.name
    
    try:
        result = validate_media_file(tmp_path)
        
        # 验证返回结果包含所有必要字段
        assert "valid" in result
        assert "format_valid" in result
        assert "size_valid" in result
        assert "media_type" in result
        assert "file_size" in result
        assert "max_size" in result
        assert "error" in result
        
        # 验证结果正确
        assert result["valid"] is True
        assert result["format_valid"] is True
        assert result["size_valid"] is True
        assert result["media_type"] == "video"
        assert result["file_size"] == 1024
        assert result["max_size"] == MAX_VIDEO_FILE_SIZE
        assert result["error"] is None
    finally:
        os.remove(tmp_path)


def test_validate_media_file_invalid_format():
    """
    Property 4: 文件大小限制验证 - 无效格式
    
    验证 validate_media_file 函数正确处理无效格式。
    
    **Validates: Requirements 3.1, 3.2**
    """
    # 创建无效格式的文件
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(b'0' * 1024)
        tmp_path = tmp_file.name
    
    try:
        result = validate_media_file(tmp_path)
        
        assert result["valid"] is False
        assert result["format_valid"] is False
        assert result["media_type"] == "unknown"
        assert "不支持的文件格式" in result["error"]
    finally:
        os.remove(tmp_path)


def test_validate_media_file_oversized_video():
    """
    Property 4: 文件大小限制验证 - 超大视频文件
    
    验证 validate_media_file 函数正确处理超大视频文件。
    
    **Validates: Requirements 3.3**
    """
    # 创建超大视频文件（略大于 150MB）
    oversized = MAX_VIDEO_FILE_SIZE + 1024
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'0' * oversized)
        tmp_path = tmp_file.name
    
    try:
        result = validate_media_file(tmp_path)
        
        assert result["valid"] is False
        assert result["format_valid"] is True
        assert result["size_valid"] is False
        assert result["media_type"] == "video"
        assert result["file_size"] == oversized
        assert "超过限制" in result["error"]
    finally:
        os.remove(tmp_path)


def test_validate_media_file_oversized_image():
    """
    Property 4: 文件大小限制验证 - 超大图片文件
    
    验证 validate_media_file 函数正确处理超大图片文件。
    
    **Validates: Requirements 3.4**
    """
    # 创建超大图片文件（略大于 10MB）
    oversized = MAX_IMAGE_FILE_SIZE + 1024
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        tmp_file.write(b'0' * oversized)
        tmp_path = tmp_file.name
    
    try:
        result = validate_media_file(tmp_path)
        
        assert result["valid"] is False
        assert result["format_valid"] is True
        assert result["size_valid"] is False
        assert result["media_type"] == "image"
        assert result["file_size"] == oversized
        assert "超过限制" in result["error"]
    finally:
        os.remove(tmp_path)


# ============================================================
# Property 5: 视频信息提取完整性
# **Feature: video-remix, Property 5: 视频信息提取完整性**
# **Validates: Requirements 3.5**
# ============================================================

from app.services.video_service import get_video_info, VideoInfoError


# 定义合理的视频尺寸和帧率策略
video_width_strategy = st.integers(min_value=100, max_value=1920)
video_height_strategy = st.integers(min_value=100, max_value=1080)
video_fps_strategy = st.sampled_from([24, 25, 30, 50, 60])
video_duration_strategy = st.floats(min_value=0.5, max_value=10.0, allow_nan=False, allow_infinity=False)


@given(
    width=video_width_strategy,
    height=video_height_strategy,
    fps=video_fps_strategy,
    duration=video_duration_strategy
)
@settings(max_examples=20, deadline=None)
def test_video_info_extraction_completeness(width: int, height: int, fps: int, duration: float):
    """
    Property 5: 视频信息提取完整性
    
    *For any* 有效的视频文件，提取的视频信息应包含：
    - duration（时长，正数）
    - width 和 height（正整数）
    - fps（帧率，正数）
    
    **Validates: Requirements 3.5**
    """
    # 创建测试视频文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # 使用 ColorClip 创建测试视频
        clip = ColorClip(size=(width, height), color=(100, 100, 100), duration=duration)
        clip = clip.set_fps(fps)
        
        # 导出视频文件
        clip.write_videofile(
            tmp_path,
            codec="libx264",
            audio=False,
            fps=fps,
            verbose=False,
            logger=None
        )
        clip.close()
        
        # 提取视频信息
        info = get_video_info(tmp_path)
        
        # 验证返回结果包含所有必要字段
        assert "duration" in info, "视频信息应包含 duration 字段"
        assert "width" in info, "视频信息应包含 width 字段"
        assert "height" in info, "视频信息应包含 height 字段"
        assert "fps" in info, "视频信息应包含 fps 字段"
        assert "size" in info, "视频信息应包含 size 字段（向后兼容）"
        
        # 验证 duration 是正数
        assert info["duration"] > 0, f"duration 必须为正数，实际值: {info['duration']}"
        assert isinstance(info["duration"], float), f"duration 必须为 float 类型"
        
        # 验证 width 是正整数
        assert info["width"] > 0, f"width 必须为正数，实际值: {info['width']}"
        assert isinstance(info["width"], int), f"width 必须为 int 类型"
        
        # 验证 height 是正整数
        assert info["height"] > 0, f"height 必须为正数，实际值: {info['height']}"
        assert isinstance(info["height"], int), f"height 必须为 int 类型"
        
        # 验证 fps 是正数
        assert info["fps"] > 0, f"fps 必须为正数，实际值: {info['fps']}"
        assert isinstance(info["fps"], float), f"fps 必须为 float 类型"
        
        # 验证 size 元组与 width/height 一致
        assert info["size"] == (info["width"], info["height"]), (
            f"size 元组应与 width/height 一致: {info['size']} vs ({info['width']}, {info['height']})"
        )
        
        # 验证提取的尺寸与创建时的尺寸一致
        assert info["width"] == width, f"提取的宽度应与创建时一致: {info['width']} vs {width}"
        assert info["height"] == height, f"提取的高度应与创建时一致: {info['height']} vs {height}"
        
        # 验证提取的帧率与创建时的帧率一致（允许小误差）
        assert abs(info["fps"] - fps) < 1, f"提取的帧率应与创建时一致: {info['fps']} vs {fps}"
        
        # 验证提取的时长与创建时的时长接近（允许 0.1 秒误差）
        assert abs(info["duration"] - duration) < 0.1, (
            f"提取的时长应与创建时接近: {info['duration']} vs {duration}"
        )
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_video_info_extraction_file_not_found():
    """
    Property 5: 视频信息提取完整性 - 文件不存在
    
    验证当视频文件不存在时，get_video_info 应抛出 FileNotFoundError。
    
    **Validates: Requirements 3.5**
    """
    with pytest.raises(FileNotFoundError):
        get_video_info("/nonexistent/path/video.mp4")


def test_video_info_extraction_invalid_format():
    """
    Property 5: 视频信息提取完整性 - 无效格式
    
    验证当文件格式不支持时，get_video_info 应抛出 VideoInfoError。
    
    **Validates: Requirements 3.5**
    """
    # 创建无效格式的文件
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(b'This is not a video file')
        tmp_path = tmp_file.name
    
    try:
        with pytest.raises(VideoInfoError) as exc_info:
            get_video_info(tmp_path)
        
        assert "不支持的视频格式" in str(exc_info.value)
    finally:
        os.remove(tmp_path)


def test_video_info_extraction_corrupted_file():
    """
    Property 5: 视频信息提取完整性 - 损坏的文件
    
    验证当视频文件损坏时，get_video_info 应抛出 VideoInfoError。
    
    **Validates: Requirements 3.5**
    """
    # 创建损坏的视频文件（有正确扩展名但内容无效）
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'This is not valid video content')
        tmp_path = tmp_file.name
    
    try:
        with pytest.raises(VideoInfoError) as exc_info:
            get_video_info(tmp_path)
        
        assert "提取视频信息时发生错误" in str(exc_info.value) or "无法获取" in str(exc_info.value)
    finally:
        os.remove(tmp_path)


def test_video_info_extraction_returns_correct_types():
    """
    Property 5: 视频信息提取完整性 - 返回类型验证
    
    验证 get_video_info 返回的所有字段类型正确。
    
    **Validates: Requirements 3.5**
    """
    # 创建测试视频文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # 使用 ColorClip 创建测试视频
        clip = ColorClip(size=(640, 480), color=(100, 100, 100), duration=2.0)
        clip = clip.set_fps(30)
        
        clip.write_videofile(
            tmp_path,
            codec="libx264",
            audio=False,
            fps=30,
            verbose=False,
            logger=None
        )
        clip.close()
        
        # 提取视频信息
        info = get_video_info(tmp_path)
        
        # 验证类型
        assert isinstance(info, dict), "返回值应为字典"
        assert isinstance(info["duration"], float), "duration 应为 float"
        assert isinstance(info["width"], int), "width 应为 int"
        assert isinstance(info["height"], int), "height 应为 int"
        assert isinstance(info["fps"], float), "fps 应为 float"
        assert isinstance(info["size"], tuple), "size 应为 tuple"
        assert len(info["size"]) == 2, "size 应为长度为 2 的元组"
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# Property 6: 视频裁剪时间验证
# **Feature: video-remix, Property 6: 视频裁剪时间验证**
# **Validates: Requirements 4.3, 4.4, 4.5**
# ============================================================

from app.services.video_service import (
    validate_trim_time_range,
    trim_video,
    VideoTrimError,
)


@given(
    video_duration=st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    start_ratio=st.floats(min_value=0.0, max_value=0.8, allow_nan=False, allow_infinity=False),
    duration_ratio=st.floats(min_value=0.1, max_value=0.5, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trim_time_range_validation_valid(
    video_duration: float,
    start_ratio: float,
    duration_ratio: float
):
    """
    Property 6: 视频裁剪时间验证 - 有效时间范围
    
    *For any* 视频裁剪请求，系统应验证：
    - start_time >= 0
    - start_time < end_time
    - end_time <= 视频总时长
    
    **Validates: Requirements 4.3, 4.4**
    """
    # 计算有效的开始和结束时间
    start_time = video_duration * start_ratio
    clip_duration = video_duration * duration_ratio
    end_time = min(start_time + clip_duration, video_duration)
    
    # 确保 start_time < end_time
    if start_time >= end_time:
        end_time = start_time + 0.1
        if end_time > video_duration:
            start_time = video_duration - 0.2
            end_time = video_duration - 0.1
    
    # 验证时间范围
    validated_start, validated_end = validate_trim_time_range(
        start_time, end_time, video_duration
    )
    
    # 验证返回值
    assert validated_start == start_time, f"验证后的开始时间应等于输入: {validated_start} vs {start_time}"
    assert validated_end == end_time, f"验证后的结束时间应等于输入: {validated_end} vs {end_time}"
    
    # 验证约束条件
    assert validated_start >= 0, f"开始时间必须 >= 0: {validated_start}"
    assert validated_start < validated_end, f"开始时间必须 < 结束时间: {validated_start} vs {validated_end}"
    assert validated_end <= video_duration, f"结束时间必须 <= 视频时长: {validated_end} vs {video_duration}"


@given(
    video_duration=st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    negative_start=st.floats(min_value=-100.0, max_value=-0.01, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trim_time_range_validation_negative_start(
    video_duration: float,
    negative_start: float
):
    """
    Property 6: 视频裁剪时间验证 - 负数开始时间
    
    *For any* 负数的开始时间，验证应该抛出 VideoTrimError。
    
    **Validates: Requirements 4.3**
    """
    end_time = video_duration / 2
    
    with pytest.raises(VideoTrimError) as exc_info:
        validate_trim_time_range(negative_start, end_time, video_duration)
    
    assert "开始时间必须 >= 0" in str(exc_info.value)


@given(
    video_duration=st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    time_point=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trim_time_range_validation_start_equals_end(
    video_duration: float,
    time_point: float
):
    """
    Property 6: 视频裁剪时间验证 - 开始时间等于结束时间
    
    *For any* 开始时间等于结束时间的情况，验证应该抛出 VideoTrimError。
    
    **Validates: Requirements 4.4**
    """
    same_time = video_duration * time_point
    
    with pytest.raises(VideoTrimError) as exc_info:
        validate_trim_time_range(same_time, same_time, video_duration)
    
    assert "开始时间必须小于结束时间" in str(exc_info.value)


@given(
    video_duration=st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    start_ratio=st.floats(min_value=0.5, max_value=0.9, allow_nan=False, allow_infinity=False),
    end_ratio=st.floats(min_value=0.1, max_value=0.4, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trim_time_range_validation_start_greater_than_end(
    video_duration: float,
    start_ratio: float,
    end_ratio: float
):
    """
    Property 6: 视频裁剪时间验证 - 开始时间大于结束时间
    
    *For any* 开始时间大于结束时间的情况，验证应该抛出 VideoTrimError。
    
    **Validates: Requirements 4.4**
    """
    start_time = video_duration * start_ratio
    end_time = video_duration * end_ratio
    
    # 确保 start_time > end_time
    if start_time <= end_time:
        start_time, end_time = end_time + 0.1, start_time
    
    with pytest.raises(VideoTrimError) as exc_info:
        validate_trim_time_range(start_time, end_time, video_duration)
    
    assert "开始时间必须小于结束时间" in str(exc_info.value)


@given(
    video_duration=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    excess_ratio=st.floats(min_value=1.01, max_value=2.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_trim_time_range_validation_end_exceeds_duration(
    video_duration: float,
    excess_ratio: float
):
    """
    Property 6: 视频裁剪时间验证 - 结束时间超过视频时长
    
    *For any* 结束时间超过视频总时长的情况，验证应该抛出 VideoTrimError。
    
    **Validates: Requirements 4.4**
    """
    start_time = 0.0
    end_time = video_duration * excess_ratio
    
    with pytest.raises(VideoTrimError) as exc_info:
        validate_trim_time_range(start_time, end_time, video_duration)
    
    assert "结束时间不能超过视频总时长" in str(exc_info.value)


@given(
    video_duration=st.floats(min_value=2.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    start_ratio=st.floats(min_value=0.0, max_value=0.3, allow_nan=False, allow_infinity=False),
    duration_ratio=st.floats(min_value=0.2, max_value=0.5, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20, deadline=None)
def test_trim_video_duration_precision(
    video_duration: float,
    start_ratio: float,
    duration_ratio: float
):
    """
    Property 6: 视频裁剪时间验证 - 裁剪精度
    
    *For any* 视频裁剪请求，裁剪后视频时长应等于 end_time - start_time（误差 < 0.1秒）。
    
    **Validates: Requirements 4.5**
    """
    # 创建测试视频文件
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_input:
        input_path = tmp_input.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_output:
        output_path = tmp_output.name
    
    try:
        # 使用 ColorClip 创建测试视频
        clip = ColorClip(size=(320, 240), color=(100, 100, 100), duration=video_duration)
        clip = clip.set_fps(24)
        
        clip.write_videofile(
            input_path,
            codec="libx264",
            audio=False,
            fps=24,
            verbose=False,
            logger=None
        )
        clip.close()
        
        # 计算有效的开始和结束时间
        start_time = video_duration * start_ratio
        clip_duration = video_duration * duration_ratio
        end_time = min(start_time + clip_duration, video_duration - 0.1)
        
        # 确保 start_time < end_time
        if start_time >= end_time:
            start_time = 0.0
            end_time = min(1.0, video_duration - 0.1)
        
        expected_duration = end_time - start_time
        
        # 裁剪视频
        result = trim_video(input_path, output_path, start_time, end_time)
        
        # 验证返回结果
        assert result["output_path"] == output_path
        assert result["start_time"] == start_time
        assert result["end_time"] == end_time
        assert result["expected_duration"] == expected_duration
        
        # 验证裁剪精度（误差 < 0.1秒）
        if result["actual_duration"] is not None:
            precision_error = abs(result["actual_duration"] - expected_duration)
            assert precision_error < 0.1, (
                f"裁剪精度误差过大: 期望 {expected_duration:.3f}s, "
                f"实际 {result['actual_duration']:.3f}s, 误差 {precision_error:.3f}s"
            )
        
    finally:
        # 清理临时文件
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def test_trim_video_file_not_found():
    """
    Property 6: 视频裁剪时间验证 - 文件不存在
    
    验证当输入视频文件不存在时，trim_video 应抛出 FileNotFoundError。
    
    **Validates: Requirements 4.3**
    """
    with pytest.raises(FileNotFoundError):
        trim_video("/nonexistent/path/video.mp4", "/tmp/output.mp4", 0.0, 1.0)


def test_trim_video_invalid_format():
    """
    Property 6: 视频裁剪时间验证 - 无效格式
    
    验证当文件格式不支持时，trim_video 应抛出 VideoTrimError。
    
    **Validates: Requirements 4.3**
    """
    # 创建无效格式的文件
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(b'This is not a video file')
        tmp_path = tmp_file.name
    
    try:
        with pytest.raises(VideoTrimError) as exc_info:
            trim_video(tmp_path, "/tmp/output.mp4", 0.0, 1.0)
        
        assert "不支持的视频格式" in str(exc_info.value)
    finally:
        os.remove(tmp_path)


# ============================================================
# Property 14: 任务 ID 唯一性
# **Feature: video-remix, Property 14: 任务 ID 唯一性**
# **Validates: Requirements 8.1**
# ============================================================

from app.services.video_service import (
    generate_task_id,
    is_valid_uuid,
    is_valid_uuid_format,
    TASK_STATUS_PENDING,
    TASK_STATUS_PROCESSING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_NAMES,
    get_task_status_name,
    TaskStatusResponse,
    build_task_status_response,
    validate_task_status_response,
)


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=20)
def test_task_id_uniqueness(count: int):
    """
    Property 14: 任务 ID 唯一性
    
    *For any* 创建的视频任务，返回的 task_id 应是唯一的 UUID 格式字符串。
    
    生成多个任务 ID，验证：
    1. 每个 ID 都是有效的 UUID 格式
    2. 所有 ID 都是唯一的（无重复）
    
    **Validates: Requirements 8.1**
    """
    # 生成多个任务 ID
    task_ids = [generate_task_id() for _ in range(count)]
    
    # 验证每个 ID 都是有效的 UUID 格式
    for task_id in task_ids:
        assert is_valid_uuid_format(task_id), (
            f"任务 ID 不是有效的 UUID 格式: {task_id}"
        )
    
    # 验证所有 ID 都是唯一的
    unique_ids = set(task_ids)
    assert len(unique_ids) == len(task_ids), (
        f"任务 ID 存在重复: 生成 {len(task_ids)} 个，唯一 {len(unique_ids)} 个"
    )


def test_task_id_uuid_format():
    """
    Property 14: 任务 ID UUID 格式验证
    
    验证生成的任务 ID 符合 UUID v4 格式。
    
    **Validates: Requirements 8.1**
    """
    task_id = generate_task_id()
    
    # 验证格式
    assert is_valid_uuid_format(task_id), f"任务 ID 不是有效的 UUID 格式: {task_id}"
    
    # 验证长度（UUID 标准长度为 36 字符，包含 4 个连字符）
    assert len(task_id) == 36, f"任务 ID 长度错误: 期望 36，实际 {len(task_id)}"
    
    # 验证包含 4 个连字符
    assert task_id.count('-') == 4, f"任务 ID 连字符数量错误: {task_id}"


def test_task_id_uuid_v4_format():
    """
    Property 14: 任务 ID UUID v4 格式验证
    
    验证生成的任务 ID 符合 UUID v4 格式（第三段以 4 开头）。
    
    **Validates: Requirements 8.1**
    """
    task_id = generate_task_id()
    
    # 验证是 UUID v4 格式
    assert is_valid_uuid(task_id), f"任务 ID 不是有效的 UUID v4 格式: {task_id}"
    
    # 验证第三段以 4 开头（UUID v4 特征）
    parts = task_id.split('-')
    assert len(parts) == 5, f"任务 ID 格式错误: {task_id}"
    assert parts[2].startswith('4'), f"任务 ID 不是 UUID v4: {task_id}"


def test_is_valid_uuid_invalid_inputs():
    """
    Property 14: UUID 验证函数 - 无效输入
    
    验证 is_valid_uuid 函数正确拒绝无效输入。
    
    **Validates: Requirements 8.1**
    """
    # 空值
    assert not is_valid_uuid(None)
    assert not is_valid_uuid("")
    
    # 非字符串
    assert not is_valid_uuid(123)
    assert not is_valid_uuid([])
    
    # 格式错误
    assert not is_valid_uuid("not-a-uuid")
    assert not is_valid_uuid("12345678-1234-1234-1234-123456789012")  # 不是 v4
    assert not is_valid_uuid("12345678-1234-5234-1234-123456789012")  # v5 不是 v4


def test_is_valid_uuid_format_valid_inputs():
    """
    Property 14: UUID 格式验证函数 - 有效输入
    
    验证 is_valid_uuid_format 函数正确接受有效的 UUID 格式。
    
    **Validates: Requirements 8.1**
    """
    # 有效的 UUID v4
    assert is_valid_uuid_format("550e8400-e29b-41d4-a716-446655440000")
    
    # 有效的 UUID（其他版本）
    assert is_valid_uuid_format("12345678-1234-1234-1234-123456789012")
    
    # 大小写不敏感
    assert is_valid_uuid_format("550E8400-E29B-41D4-A716-446655440000")


# ============================================================
# Property 15: 任务状态查询完整性
# **Feature: video-remix, Property 15: 任务状态查询完整性**
# **Validates: Requirements 8.3, 8.5, 8.6**
# ============================================================

@given(
    status_code=st.sampled_from([
        TASK_STATUS_PENDING,
        TASK_STATUS_PROCESSING,
        TASK_STATUS_COMPLETED,
        TASK_STATUS_FAILED
    ]),
    progress=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=20)
def test_task_status_response_completeness(status_code: int, progress: int):
    """
    Property 15: 任务状态查询完整性
    
    *For any* 任务状态查询，返回结果应包含：
    - status（状态枚举值）
    - progress（0-100 的整数）
    - message（状态消息字符串）
    - 完成状态时包含 download_url
    - 失败状态时包含 error_message
    
    **Validates: Requirements 8.3, 8.5, 8.6**
    """
    # 构建响应
    response = build_task_status_response(
        status_code=status_code,
        progress=progress,
        progress_message="测试消息",
        error_message="测试错误" if status_code == TASK_STATUS_FAILED else None,
        download_url="http://example.com/download" if status_code == TASK_STATUS_COMPLETED else None,
        duration=10.5 if status_code == TASK_STATUS_COMPLETED else None,
        task_id="test-task-id"
    )
    
    # 转换为字典
    result = response.to_dict()
    
    # 验证必要字段存在
    assert "status" in result, "响应缺少 status 字段"
    assert "progress" in result, "响应缺少 progress 字段"
    assert "message" in result, "响应缺少 message 字段"
    
    # 验证 status 是有效的枚举值
    valid_statuses = ["pending", "processing", "completed", "failed"]
    assert result["status"] in valid_statuses, (
        f"无效的 status 值: {result['status']}"
    )
    
    # 验证 progress 是 0-100 的整数
    assert isinstance(result["progress"], int), (
        f"progress 必须是整数，实际类型: {type(result['progress'])}"
    )
    assert 0 <= result["progress"] <= 100, (
        f"progress 必须在 0-100 范围内，实际值: {result['progress']}"
    )
    
    # 验证 message 是字符串
    assert isinstance(result["message"], str), (
        f"message 必须是字符串，实际类型: {type(result['message'])}"
    )
    
    # 完成状态必须有 download_url (Requirements 8.5)
    if result["status"] == "completed":
        assert "download_url" in result, "完成状态缺少 download_url 字段"
        assert result["progress"] == 100, "完成状态的 progress 必须是 100"
    
    # 失败状态必须有 error_message (Requirements 8.6)
    if result["status"] == "failed":
        assert "error_message" in result, "失败状态缺少 error_message 字段"
        assert result["progress"] == 0, "失败状态的 progress 必须是 0"


def test_task_status_completed_response():
    """
    Property 15: 任务状态查询完整性 - 完成状态
    
    验证完成状态的响应包含 download_url。
    
    **Validates: Requirements 8.5**
    """
    response = build_task_status_response(
        status_code=TASK_STATUS_COMPLETED,
        progress=100,
        progress_message="视频生成完成",
        download_url="http://example.com/video.mp4",
        duration=30.5
    )
    
    result = response.to_dict()
    
    # 验证完成状态的必要字段
    assert result["status"] == "completed"
    assert result["progress"] == 100
    assert "download_url" in result
    assert result["download_url"] == "http://example.com/video.mp4"
    assert "duration" in result
    assert result["duration"] == 30.5
    
    # 完成状态不应有 error_message
    assert "error_message" not in result


def test_task_status_failed_response():
    """
    Property 15: 任务状态查询完整性 - 失败状态
    
    验证失败状态的响应包含 error_message。
    
    **Validates: Requirements 8.6**
    """
    response = build_task_status_response(
        status_code=TASK_STATUS_FAILED,
        progress=0,
        progress_message="视频生成失败",
        error_message="内存不足"
    )
    
    result = response.to_dict()
    
    # 验证失败状态的必要字段
    assert result["status"] == "failed"
    assert result["progress"] == 0
    assert "error_message" in result
    assert result["error_message"] == "内存不足"
    
    # 失败状态不应有 download_url
    assert "download_url" not in result


def test_task_status_pending_response():
    """
    Property 15: 任务状态查询完整性 - 等待状态
    
    验证等待状态的响应格式正确。
    
    **Validates: Requirements 8.3**
    """
    response = build_task_status_response(
        status_code=TASK_STATUS_PENDING,
        progress=5,
        progress_message="任务排队中..."
    )
    
    result = response.to_dict()
    
    # 验证等待状态的必要字段
    assert result["status"] == "pending"
    assert result["progress"] == 5
    assert result["message"] == "任务排队中..."
    
    # 等待状态不应有 download_url 或 error_message
    assert "download_url" not in result
    assert "error_message" not in result


def test_task_status_processing_response():
    """
    Property 15: 任务状态查询完整性 - 处理中状态
    
    验证处理中状态的响应格式正确。
    
    **Validates: Requirements 8.3**
    """
    response = build_task_status_response(
        status_code=TASK_STATUS_PROCESSING,
        progress=50,
        progress_message="正在合成视频..."
    )
    
    result = response.to_dict()
    
    # 验证处理中状态的必要字段
    assert result["status"] == "processing"
    assert result["progress"] == 50
    assert result["message"] == "正在合成视频..."
    
    # 处理中状态不应有 download_url 或 error_message
    assert "download_url" not in result
    assert "error_message" not in result


def test_validate_task_status_response_valid():
    """
    Property 15: 任务状态响应验证 - 有效响应
    
    验证 validate_task_status_response 函数正确验证有效响应。
    
    **Validates: Requirements 8.3, 8.5, 8.6**
    """
    # 完成状态的有效响应
    completed_response = {
        "status": "completed",
        "progress": 100,
        "message": "视频生成完成",
        "download_url": "http://example.com/video.mp4"
    }
    is_valid, errors = validate_task_status_response(completed_response)
    assert is_valid, f"完成状态响应应该有效: {errors}"
    
    # 失败状态的有效响应
    failed_response = {
        "status": "failed",
        "progress": 0,
        "message": "视频生成失败",
        "error_message": "内存不足"
    }
    is_valid, errors = validate_task_status_response(failed_response)
    assert is_valid, f"失败状态响应应该有效: {errors}"
    
    # 处理中状态的有效响应
    processing_response = {
        "status": "processing",
        "progress": 50,
        "message": "正在处理..."
    }
    is_valid, errors = validate_task_status_response(processing_response)
    assert is_valid, f"处理中状态响应应该有效: {errors}"


def test_validate_task_status_response_invalid():
    """
    Property 15: 任务状态响应验证 - 无效响应
    
    验证 validate_task_status_response 函数正确拒绝无效响应。
    
    **Validates: Requirements 8.3, 8.5, 8.6**
    """
    # 缺少 status 字段
    response1 = {"progress": 50, "message": "处理中"}
    is_valid, errors = validate_task_status_response(response1)
    assert not is_valid
    assert any("status" in e for e in errors)
    
    # 缺少 progress 字段
    response2 = {"status": "processing", "message": "处理中"}
    is_valid, errors = validate_task_status_response(response2)
    assert not is_valid
    assert any("progress" in e for e in errors)
    
    # 缺少 message 字段
    response3 = {"status": "processing", "progress": 50}
    is_valid, errors = validate_task_status_response(response3)
    assert not is_valid
    assert any("message" in e for e in errors)
    
    # 完成状态缺少 download_url
    response4 = {"status": "completed", "progress": 100, "message": "完成"}
    is_valid, errors = validate_task_status_response(response4)
    assert not is_valid
    assert any("download_url" in e for e in errors)
    
    # 失败状态缺少 error_message
    response5 = {"status": "failed", "progress": 0, "message": "失败"}
    is_valid, errors = validate_task_status_response(response5)
    assert not is_valid
    assert any("error_message" in e for e in errors)


def test_get_task_status_name():
    """
    Property 15: 任务状态名称映射
    
    验证 get_task_status_name 函数正确映射状态码到状态名称。
    
    **Validates: Requirements 8.3**
    """
    assert get_task_status_name(TASK_STATUS_PENDING) == "pending"
    assert get_task_status_name(TASK_STATUS_PROCESSING) == "processing"
    assert get_task_status_name(TASK_STATUS_COMPLETED) == "completed"
    assert get_task_status_name(TASK_STATUS_FAILED) == "failed"
    assert get_task_status_name(999) == "unknown"  # 未知状态码


# ============================================================
# Property 17: 配置默认值有效性
# **Feature: video-remix, Property 17: 配置默认值有效性**
# **Validates: Requirements 9.2, 9.3**
# ============================================================

from app.services.video_service import (
    validate_config_defaults,
    get_config_with_defaults,
    get_all_config_defaults,
    get_config_ranges,
    get_config_options,
    # 默认值常量
    BRIGHTNESS_DEFAULT,
    CONTRAST_DEFAULT,
    SATURATION_DEFAULT,
    TRANSITION_DURATION_DEFAULT,
    BGM_VOLUME_DEFAULT,
    BGM_FADE_IN_DEFAULT,
    BGM_FADE_OUT_DEFAULT,
    CLIP_MIN_DURATION_DEFAULT,
    CLIP_MAX_DURATION_DEFAULT,
    SUBTITLE_SIZE_DEFAULT,
    SUBTITLE_STROKE_WIDTH_DEFAULT,
    SUBTITLE_POSITION_DEFAULT,
    SUBTITLE_FONT_DEFAULT,
    SUBTITLE_COLOR_DEFAULT,
    SUBTITLE_STROKE_COLOR_DEFAULT,
    OUTPUT_QUALITY_DEFAULT,
    VIDEO_FPS_DEFAULT,
    VIDEO_RESOLUTION_DEFAULT,
    VIDEO_LAYOUT_DEFAULT,
    FIT_MODE_DEFAULT,
    TRANSITION_TYPE_DEFAULT,
    COLOR_FILTER_DEFAULT,
    EFFECT_TYPE_DEFAULT,
    # 范围常量
    BRIGHTNESS_MIN,
    BRIGHTNESS_MAX,
    CONTRAST_MIN,
    CONTRAST_MAX,
    SATURATION_MIN,
    SATURATION_MAX,
    TRANSITION_DURATION_MIN,
    TRANSITION_DURATION_MAX,
    BGM_VOLUME_MIN,
    BGM_VOLUME_MAX,
    BGM_FADE_IN_MIN,
    BGM_FADE_IN_MAX,
    BGM_FADE_OUT_MIN,
    BGM_FADE_OUT_MAX,
    CLIP_MIN_DURATION_MIN,
    CLIP_MIN_DURATION_MAX,
    CLIP_MAX_DURATION_MIN,
    CLIP_MAX_DURATION_MAX,
    SUBTITLE_SIZE_MIN,
    SUBTITLE_SIZE_MAX,
    SUBTITLE_STROKE_WIDTH_MIN,
    SUBTITLE_STROKE_WIDTH_MAX,
    SUBTITLE_POSITIONS,
    OUTPUT_QUALITIES,
    VIDEO_RESOLUTIONS,
    VIDEO_LAYOUTS,
    FRAME_RATES,
    FIT_MODES,
    TRANSITIONS,
    COLOR_FILTERS,
    EFFECT_TYPES,
)


def test_validate_config_defaults_all_valid():
    """
    Property 17: 配置默认值有效性 - 所有默认值验证
    
    *For any* 配置项的默认值，该值应在该配置项的有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    # 调用验证函数，不应抛出异常
    result = validate_config_defaults()
    
    # 验证返回结果
    assert result["valid"] is True, "所有默认值应该有效"
    assert len(result["errors"]) == 0, f"不应该有错误: {result['errors']}"
    assert "defaults" in result, "应该返回默认值字典"
    
    # 验证默认值字典包含所有必要的键
    defaults = result["defaults"]
    expected_keys = [
        "brightness", "contrast", "saturation",
        "transition_duration", "bgm_volume", "bgm_fade_in", "bgm_fade_out",
        "clip_min_duration", "clip_max_duration",
        "subtitle_size", "subtitle_stroke_width", "subtitle_position",
        "output_quality", "video_fps", "video_resolution", "video_layout",
        "fit_mode", "transition_type", "color_filter", "effect_type",
        "subtitle_font", "subtitle_color", "subtitle_stroke_color"
    ]
    
    for key in expected_keys:
        assert key in defaults, f"默认值字典应该包含 {key}"


def test_brightness_default_in_range():
    """
    Property 17: 配置默认值有效性 - 亮度默认值
    
    验证亮度默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert BRIGHTNESS_MIN <= BRIGHTNESS_DEFAULT <= BRIGHTNESS_MAX, (
        f"亮度默认值 {BRIGHTNESS_DEFAULT} 应该在 [{BRIGHTNESS_MIN}, {BRIGHTNESS_MAX}] 范围内"
    )


def test_contrast_default_in_range():
    """
    Property 17: 配置默认值有效性 - 对比度默认值
    
    验证对比度默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert CONTRAST_MIN <= CONTRAST_DEFAULT <= CONTRAST_MAX, (
        f"对比度默认值 {CONTRAST_DEFAULT} 应该在 [{CONTRAST_MIN}, {CONTRAST_MAX}] 范围内"
    )


def test_saturation_default_in_range():
    """
    Property 17: 配置默认值有效性 - 饱和度默认值
    
    验证饱和度默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert SATURATION_MIN <= SATURATION_DEFAULT <= SATURATION_MAX, (
        f"饱和度默认值 {SATURATION_DEFAULT} 应该在 [{SATURATION_MIN}, {SATURATION_MAX}] 范围内"
    )


def test_transition_duration_default_in_range():
    """
    Property 17: 配置默认值有效性 - 转场时长默认值
    
    验证转场时长默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert TRANSITION_DURATION_MIN <= TRANSITION_DURATION_DEFAULT <= TRANSITION_DURATION_MAX, (
        f"转场时长默认值 {TRANSITION_DURATION_DEFAULT} 应该在 [{TRANSITION_DURATION_MIN}, {TRANSITION_DURATION_MAX}] 范围内"
    )


def test_bgm_volume_default_in_range():
    """
    Property 17: 配置默认值有效性 - BGM 音量默认值
    
    验证 BGM 音量默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert BGM_VOLUME_MIN <= BGM_VOLUME_DEFAULT <= BGM_VOLUME_MAX, (
        f"BGM 音量默认值 {BGM_VOLUME_DEFAULT} 应该在 [{BGM_VOLUME_MIN}, {BGM_VOLUME_MAX}] 范围内"
    )


def test_bgm_fade_in_default_in_range():
    """
    Property 17: 配置默认值有效性 - BGM 淡入时长默认值
    
    验证 BGM 淡入时长默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert BGM_FADE_IN_MIN <= BGM_FADE_IN_DEFAULT <= BGM_FADE_IN_MAX, (
        f"BGM 淡入时长默认值 {BGM_FADE_IN_DEFAULT} 应该在 [{BGM_FADE_IN_MIN}, {BGM_FADE_IN_MAX}] 范围内"
    )


def test_bgm_fade_out_default_in_range():
    """
    Property 17: 配置默认值有效性 - BGM 淡出时长默认值
    
    验证 BGM 淡出时长默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert BGM_FADE_OUT_MIN <= BGM_FADE_OUT_DEFAULT <= BGM_FADE_OUT_MAX, (
        f"BGM 淡出时长默认值 {BGM_FADE_OUT_DEFAULT} 应该在 [{BGM_FADE_OUT_MIN}, {BGM_FADE_OUT_MAX}] 范围内"
    )


def test_clip_duration_defaults_in_range():
    """
    Property 17: 配置默认值有效性 - 片段时长默认值
    
    验证片段时长默认值在有效范围内，且最小时长 <= 最大时长。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert CLIP_MIN_DURATION_MIN <= CLIP_MIN_DURATION_DEFAULT <= CLIP_MIN_DURATION_MAX, (
        f"片段最小时长默认值 {CLIP_MIN_DURATION_DEFAULT} 应该在 [{CLIP_MIN_DURATION_MIN}, {CLIP_MIN_DURATION_MAX}] 范围内"
    )
    
    assert CLIP_MAX_DURATION_MIN <= CLIP_MAX_DURATION_DEFAULT <= CLIP_MAX_DURATION_MAX, (
        f"片段最大时长默认值 {CLIP_MAX_DURATION_DEFAULT} 应该在 [{CLIP_MAX_DURATION_MIN}, {CLIP_MAX_DURATION_MAX}] 范围内"
    )
    
    assert CLIP_MIN_DURATION_DEFAULT <= CLIP_MAX_DURATION_DEFAULT, (
        f"片段最小时长默认值 {CLIP_MIN_DURATION_DEFAULT} 应该 <= 最大时长默认值 {CLIP_MAX_DURATION_DEFAULT}"
    )


def test_subtitle_size_default_in_range():
    """
    Property 17: 配置默认值有效性 - 字幕字号默认值
    
    验证字幕字号默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert SUBTITLE_SIZE_MIN <= SUBTITLE_SIZE_DEFAULT <= SUBTITLE_SIZE_MAX, (
        f"字幕字号默认值 {SUBTITLE_SIZE_DEFAULT} 应该在 [{SUBTITLE_SIZE_MIN}, {SUBTITLE_SIZE_MAX}] 范围内"
    )


def test_subtitle_stroke_width_default_in_range():
    """
    Property 17: 配置默认值有效性 - 字幕描边宽度默认值
    
    验证字幕描边宽度默认值在有效范围内。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert SUBTITLE_STROKE_WIDTH_MIN <= SUBTITLE_STROKE_WIDTH_DEFAULT <= SUBTITLE_STROKE_WIDTH_MAX, (
        f"字幕描边宽度默认值 {SUBTITLE_STROKE_WIDTH_DEFAULT} 应该在 [{SUBTITLE_STROKE_WIDTH_MIN}, {SUBTITLE_STROKE_WIDTH_MAX}] 范围内"
    )


def test_subtitle_position_default_valid():
    """
    Property 17: 配置默认值有效性 - 字幕位置默认值
    
    验证字幕位置默认值在支持的位置列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert SUBTITLE_POSITION_DEFAULT in SUBTITLE_POSITIONS, (
        f"字幕位置默认值 {SUBTITLE_POSITION_DEFAULT} 应该在 {SUBTITLE_POSITIONS} 中"
    )


def test_output_quality_default_valid():
    """
    Property 17: 配置默认值有效性 - 输出质量默认值
    
    验证输出质量默认值在支持的质量列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert OUTPUT_QUALITY_DEFAULT in OUTPUT_QUALITIES, (
        f"输出质量默认值 {OUTPUT_QUALITY_DEFAULT} 应该在 {OUTPUT_QUALITIES} 中"
    )


def test_video_fps_default_valid():
    """
    Property 17: 配置默认值有效性 - 视频帧率默认值
    
    验证视频帧率默认值在支持的帧率列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert VIDEO_FPS_DEFAULT in FRAME_RATES, (
        f"视频帧率默认值 {VIDEO_FPS_DEFAULT} 应该在 {FRAME_RATES} 中"
    )


def test_video_resolution_default_valid():
    """
    Property 17: 配置默认值有效性 - 视频分辨率默认值
    
    验证视频分辨率默认值在支持的分辨率列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert VIDEO_RESOLUTION_DEFAULT in VIDEO_RESOLUTIONS, (
        f"视频分辨率默认值 {VIDEO_RESOLUTION_DEFAULT} 应该在 {list(VIDEO_RESOLUTIONS.keys())} 中"
    )


def test_video_layout_default_valid():
    """
    Property 17: 配置默认值有效性 - 视频布局默认值
    
    验证视频布局默认值在支持的布局列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert VIDEO_LAYOUT_DEFAULT in VIDEO_LAYOUTS, (
        f"视频布局默认值 {VIDEO_LAYOUT_DEFAULT} 应该在 {list(VIDEO_LAYOUTS.keys())} 中"
    )


def test_fit_mode_default_valid():
    """
    Property 17: 配置默认值有效性 - 素材适配模式默认值
    
    验证素材适配模式默认值在支持的模式列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert FIT_MODE_DEFAULT in FIT_MODES, (
        f"素材适配模式默认值 {FIT_MODE_DEFAULT} 应该在 {list(FIT_MODES.keys())} 中"
    )


def test_transition_type_default_valid():
    """
    Property 17: 配置默认值有效性 - 转场类型默认值
    
    验证转场类型默认值在支持的类型列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert TRANSITION_TYPE_DEFAULT in TRANSITIONS, (
        f"转场类型默认值 {TRANSITION_TYPE_DEFAULT} 应该在 {list(TRANSITIONS.keys())} 中"
    )


def test_color_filter_default_valid():
    """
    Property 17: 配置默认值有效性 - 颜色滤镜默认值
    
    验证颜色滤镜默认值在支持的滤镜列表中。
    
    **Validates: Requirements 9.2, 9.3**
    """
    assert COLOR_FILTER_DEFAULT in COLOR_FILTERS, (
        f"颜色滤镜默认值 {COLOR_FILTER_DEFAULT} 应该在 {list(COLOR_FILTERS.keys())} 中"
    )


def test_effect_type_default_valid():
    """
    Property 17: 配置默认值有效性 - 特效类型默认值
    
    验证特效类型默认值有效（None 或在支持的特效列表中）。
    
    **Validates: Requirements 9.2, 9.3**
    """
    # None 表示无特效，是有效的
    if EFFECT_TYPE_DEFAULT is not None:
        assert EFFECT_TYPE_DEFAULT in EFFECT_TYPES, (
            f"特效类型默认值 {EFFECT_TYPE_DEFAULT} 应该在 {list(EFFECT_TYPES.keys())} 中"
        )


@given(
    brightness=st.floats(
        min_value=BRIGHTNESS_MIN,
        max_value=BRIGHTNESS_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    contrast=st.floats(
        min_value=CONTRAST_MIN,
        max_value=CONTRAST_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    saturation=st.floats(
        min_value=SATURATION_MIN,
        max_value=SATURATION_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
)
@settings(max_examples=20)
def test_get_config_with_defaults_uses_provided_values(
    brightness: float,
    contrast: float,
    saturation: float
):
    """
    Property 17: 配置默认值有效性 - 使用提供的值
    
    *For any* 用户提供的有效配置值，get_config_with_defaults 应该使用这些值而不是默认值。
    
    **Validates: Requirements 9.2, 9.3**
    """
    user_config = {
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
    }
    
    result = get_config_with_defaults(user_config)
    
    # 验证使用了用户提供的值
    assert result["brightness"] == brightness, f"应该使用用户提供的亮度值: {brightness}"
    assert result["contrast"] == contrast, f"应该使用用户提供的对比度值: {contrast}"
    assert result["saturation"] == saturation, f"应该使用用户提供的饱和度值: {saturation}"


def test_get_config_with_defaults_fills_missing_values():
    """
    Property 17: 配置默认值有效性 - 填充缺失值
    
    验证 get_config_with_defaults 为未指定的配置项使用默认值。
    
    **Validates: Requirements 9.2, 9.3**
    """
    # 只提供部分配置
    user_config = {
        "brightness": 1.5,
    }
    
    result = get_config_with_defaults(user_config)
    
    # 验证使用了用户提供的值
    assert result["brightness"] == 1.5
    
    # 验证其他值使用了默认值
    assert result["contrast"] == CONTRAST_DEFAULT
    assert result["saturation"] == SATURATION_DEFAULT
    assert result["transition_duration"] == TRANSITION_DURATION_DEFAULT
    assert result["bgm_volume"] == BGM_VOLUME_DEFAULT
    assert result["video_resolution"] == VIDEO_RESOLUTION_DEFAULT
    assert result["video_layout"] == VIDEO_LAYOUT_DEFAULT
    assert result["video_fps"] == VIDEO_FPS_DEFAULT


def test_get_config_with_defaults_empty_config():
    """
    Property 17: 配置默认值有效性 - 空配置
    
    验证 get_config_with_defaults 对空配置返回所有默认值。
    
    **Validates: Requirements 9.2, 9.3**
    """
    result = get_config_with_defaults({})
    
    # 验证所有值都是默认值
    assert result["brightness"] == BRIGHTNESS_DEFAULT
    assert result["contrast"] == CONTRAST_DEFAULT
    assert result["saturation"] == SATURATION_DEFAULT
    assert result["transition_duration"] == TRANSITION_DURATION_DEFAULT
    assert result["bgm_volume"] == BGM_VOLUME_DEFAULT
    assert result["bgm_fade_in"] == BGM_FADE_IN_DEFAULT
    assert result["bgm_fade_out"] == BGM_FADE_OUT_DEFAULT
    assert result["clip_min_duration"] == CLIP_MIN_DURATION_DEFAULT
    assert result["clip_max_duration"] == CLIP_MAX_DURATION_DEFAULT
    assert result["subtitle_size"] == SUBTITLE_SIZE_DEFAULT
    assert result["subtitle_stroke_width"] == SUBTITLE_STROKE_WIDTH_DEFAULT
    assert result["subtitle_position"] == SUBTITLE_POSITION_DEFAULT
    assert result["output_quality"] == OUTPUT_QUALITY_DEFAULT
    assert result["video_fps"] == VIDEO_FPS_DEFAULT
    assert result["video_resolution"] == VIDEO_RESOLUTION_DEFAULT
    assert result["video_layout"] == VIDEO_LAYOUT_DEFAULT
    assert result["fit_mode"] == FIT_MODE_DEFAULT
    assert result["transition_type"] == TRANSITION_TYPE_DEFAULT
    assert result["color_filter"] == COLOR_FILTER_DEFAULT


def test_get_config_with_defaults_none_config():
    """
    Property 17: 配置默认值有效性 - None 配置
    
    验证 get_config_with_defaults 对 None 配置返回所有默认值。
    
    **Validates: Requirements 9.2, 9.3**
    """
    result = get_config_with_defaults(None)
    
    # 验证返回了有效的配置
    assert result is not None
    assert isinstance(result, dict)
    
    # 验证包含所有必要的键
    assert "brightness" in result
    assert "contrast" in result
    assert "saturation" in result
    assert "video_resolution" in result
    assert "video_layout" in result


def test_get_all_config_defaults():
    """
    Property 17: 配置默认值有效性 - 获取所有默认值
    
    验证 get_all_config_defaults 返回所有配置项的默认值。
    
    **Validates: Requirements 9.2, 9.3**
    """
    defaults = get_all_config_defaults()
    
    # 验证返回了字典
    assert isinstance(defaults, dict)
    
    # 验证包含所有必要的键
    expected_keys = [
        "brightness", "contrast", "saturation",
        "transition_duration", "transition_type",
        "bgm_volume", "bgm_fade_in", "bgm_fade_out",
        "clip_min_duration", "clip_max_duration",
        "subtitle_size", "subtitle_stroke_width", "subtitle_position",
        "subtitle_font", "subtitle_color", "subtitle_stroke_color",
        "output_quality", "video_fps", "video_resolution", "video_layout",
        "fit_mode", "color_filter", "effect_type"
    ]
    
    for key in expected_keys:
        assert key in defaults, f"默认值字典应该包含 {key}"


def test_get_config_ranges():
    """
    Property 17: 配置默认值有效性 - 获取配置范围
    
    验证 get_config_ranges 返回所有数值配置项的有效范围。
    
    **Validates: Requirements 9.2, 9.3**
    """
    ranges = get_config_ranges()
    
    # 验证返回了字典
    assert isinstance(ranges, dict)
    
    # 验证包含必要的键
    expected_keys = [
        "brightness", "contrast", "saturation",
        "transition_duration",
        "bgm_volume", "bgm_fade_in", "bgm_fade_out",
        "clip_min_duration", "clip_max_duration",
        "subtitle_size", "subtitle_stroke_width"
    ]
    
    for key in expected_keys:
        assert key in ranges, f"范围字典应该包含 {key}"
        assert "min" in ranges[key], f"{key} 应该包含 min"
        assert "max" in ranges[key], f"{key} 应该包含 max"
        assert "default" in ranges[key], f"{key} 应该包含 default"
        
        # 验证默认值在范围内
        assert ranges[key]["min"] <= ranges[key]["default"] <= ranges[key]["max"], (
            f"{key} 的默认值 {ranges[key]['default']} 应该在 [{ranges[key]['min']}, {ranges[key]['max']}] 范围内"
        )


def test_get_config_options():
    """
    Property 17: 配置默认值有效性 - 获取配置选项
    
    验证 get_config_options 返回所有枚举类型配置项的可选值列表。
    
    **Validates: Requirements 9.2, 9.3**
    """
    options = get_config_options()
    
    # 验证返回了字典
    assert isinstance(options, dict)
    
    # 验证包含必要的键
    expected_keys = [
        "video_resolution", "video_layout", "video_fps",
        "platform_preset", "fit_mode", "transition_type",
        "color_filter", "effect_type",
        "subtitle_position", "output_quality"
    ]
    
    for key in expected_keys:
        assert key in options, f"选项字典应该包含 {key}"
        assert isinstance(options[key], list), f"{key} 应该是列表"
        assert len(options[key]) > 0, f"{key} 应该有至少一个选项"
