# Implementation Plan: 视频混剪系统

## Overview

基于现有的 FastAPI 后端和 Vue.js 前端架构，扩展视频混剪功能。主要工作包括：扩展配置选项、实现新的转场效果、添加视频特效和滤镜、优化字幕渲染、完善任务管理。

## Tasks

- [x] 1. 扩展视频配置管理
  - [x] 1.1 更新 video_service.py 中的配置常量
    - 添加完整的分辨率配置（480p, 720p, 1080p, 2k, 4k）
    - 添加完整的布局配置（9:16, 3:4, 1:1, 4:3, 16:9, 21:9）
    - 添加帧率选项（24, 25, 30, 50, 60）
    - 添加平台预设配置
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 1.2 编写属性测试：视频尺寸计算正确性
    - **Property 1: 视频尺寸计算正确性**
    - **Validates: Requirements 5.1, 5.2**
  - [x] 1.3 实现 calculate_video_size 函数
    - 根据分辨率和布局计算实际视频尺寸
    - 确保输出尺寸为偶数
    - _Requirements: 5.1, 5.2_
  - [x] 1.4 编写属性测试：平台预设配置完整性
    - **Property 2: 平台预设配置完整性**
    - **Validates: Requirements 5.4, 5.5**

- [x] 2. 扩展素材适配功能
  - [x] 2.1 实现三种素材适配模式
    - crop（裁剪填充）：保持比例，裁剪多余部分
    - fit（适应填充）：保持比例，添加黑边
    - stretch（拉伸填充）：直接拉伸
    - _Requirements: 6.1_
  - [x] 2.2 编写属性测试：素材尺寸适配正确性
    - **Property 7: 素材尺寸适配正确性**
    - **Validates: Requirements 6.1**

- [x] 3. Checkpoint - 确保配置和适配功能测试通过
  - 运行所有测试，确保通过
  - 如有问题请询问用户

- [x] 4. 实现转场效果
  - [x] 4.1 扩展转场效果配置
    - 添加转场类型：none, fade, slide_left/right/up/down, zoom_in/out, dissolve, wipe_left/right
    - 添加转场时长配置（0.3-2.0秒）
    - _Requirements: 6.4, 6.5_
  - [x] 4.2 实现 apply_transition 函数
    - 实现淡入淡出转场
    - 实现滑动转场
    - 实现缩放转场
    - _Requirements: 6.4_
  - [x] 4.3 编写属性测试：转场时长配置验证
    - **Property 10: 转场时长配置验证**
    - **Validates: Requirements 6.5**

- [x] 5. 实现视频特效和滤镜
  - [x] 5.1 实现 Ken Burns 效果
    - 缓慢缩放平移效果
    - 支持 zoom in/out 方向
    - _Requirements: 10.1_
  - [x] 5.2 实现颜色滤镜
    - grayscale（黑白）
    - vintage（复古）
    - warm/cool（暖色/冷色调）
    - high_contrast（高对比度）
    - soft（柔和）
    - _Requirements: 10.2_
  - [x] 5.3 实现亮度/对比度/饱和度调节
    - brightness: 0.5-2.0
    - contrast: 0.5-2.0
    - saturation: 0-2.0
    - _Requirements: 10.3_
  - [x] 5.4 编写属性测试：视频调节参数范围
    - **Property 19: 视频调节参数范围**
    - **Validates: Requirements 10.3**

- [x] 6. Checkpoint - 确保转场和特效功能测试通过
  - 运行所有测试，确保通过
  - 如有问题请询问用户

- [x] 7. 优化音频处理
  - [x] 7.1 实现 BGM 淡入淡出效果
    - 支持配置淡入时长（0-5秒）
    - 支持配置淡出时长（0-5秒）
    - _Requirements: 6.8_
  - [x] 7.2 优化音频混合逻辑
    - 配音作为主音轨
    - BGM 音量可调（0-100%）
    - 确保音频时长与视频一致
    - _Requirements: 6.6, 6.7_
  - [x] 7.3 编写属性测试：音频轨道合成
    - **Property 11: 音频轨道合成**
    - **Validates: Requirements 6.6, 6.7**

- [x] 8. 更新 API 接口
  - [x] 8.1 更新 VideoTaskCreate 模型
    - 添加新的配置字段（video_resolution, video_layout, platform_preset, fit_mode 等）
    - 添加特效配置字段（effect_type, color_filter, brightness, contrast, saturation）
    - 添加 BGM 淡入淡出配置
    - _Requirements: 9.1_
  - [x] 8.2 更新 /config API
    - 返回完整的配置选项（分辨率、布局、帧率、平台预设、转场、滤镜等）
    - _Requirements: 9.1_
  - [x] 8.3 添加参数验证
    - 验证所有配置参数在有效范围内
    - 无效参数返回 400 错误
    - _Requirements: 9.4, 9.5_
  - [x] 8.4 编写属性测试：配置参数验证
    - **Property 18: 配置参数验证**
    - **Validates: Requirements 9.4, 9.5**

- [x] 9. 更新数据库模型
  - [x] 9.1 更新 VideoTask 模型
    - 添加新字段：video_resolution, platform_preset, fit_mode
    - 添加特效字段：effect_type, color_filter, brightness, contrast, saturation
    - 添加 BGM 淡入淡出字段
    - _Requirements: 8.7_
  - [x] 9.2 创建数据库迁移脚本
    - 生成 ALTER TABLE 语句
    - _Requirements: 8.7_

- [x] 10. Checkpoint - 确保 API 和数据库更新测试通过
  - 运行所有测试，确保通过
  - 如有问题请询问用户

- [x] 11. 更新视频合成主流程
  - [x] 11.1 更新 create_video_from_config 函数
    - 集成新的尺寸计算逻辑
    - 集成素材适配模式
    - 集成转场效果
    - 集成视频特效和滤镜
    - 集成 BGM 淡入淡出
    - _Requirements: 5.5, 6.1, 6.4, 6.8, 10.1, 10.2, 10.3_
  - [x] 11.2 编写属性测试：输出视频格式验证
    - **Property 12: 输出视频格式验证**
    - **Validates: Requirements 6.9**

- [x] 12. 文件验证功能
  - [x] 12.1 实现文件格式验证函数
    - 验证视频格式：mp4, mov, avi, mkv, webm
    - 验证图片格式：jpg, jpeg, png, webp
    - _Requirements: 3.1, 3.2_
  - [x] 12.2 实现文件大小验证函数
    - 视频文件 ≤ 150MB
    - 图片文件 ≤ 10MB
    - _Requirements: 3.3, 3.4_
  - [x] 12.3 编写属性测试：媒体文件格式验证
    - **Property 3: 媒体文件格式验证**
    - **Validates: Requirements 3.1, 3.2**
  - [x] 12.4 编写属性测试：文件大小限制验证
    - **Property 4: 文件大小限制验证**
    - **Validates: Requirements 3.3, 3.4**

- [x] 13. 视频信息提取优化
  - [x] 13.1 优化 get_video_info 函数
    - 确保返回完整信息：duration, width, height, fps
    - 添加错误处理
    - _Requirements: 3.5_
  - [x] 13.2 编写属性测试：视频信息提取完整性
    - **Property 5: 视频信息提取完整性**
    - **Validates: Requirements 3.5**

- [x] 14. 视频裁剪功能优化
  - [x] 14.1 优化 trim_video 函数
    - 添加时间范围验证
    - 确保裁剪精度
    - _Requirements: 4.3, 4.4_
  - [x] 14.2 编写属性测试：视频裁剪时间验证
    - **Property 6: 视频裁剪时间验证**
    - **Validates: Requirements 4.3, 4.4, 4.5**

- [x] 15. Checkpoint - 确保文件处理功能测试通过
  - 运行所有测试，确保通过
  - 如有问题请询问用户

- [x] 16. 任务管理优化
  - [x] 16.1 优化任务 ID 生成
    - 确保使用 UUID 格式
    - _Requirements: 8.1_
  - [x] 16.2 优化任务状态查询
    - 返回完整状态信息
    - 完成状态返回 download_url
    - 失败状态返回 error_message
    - _Requirements: 8.3, 8.5, 8.6_
  - [x] 16.3 编写属性测试：任务 ID 唯一性
    - **Property 14: 任务 ID 唯一性**
    - **Validates: Requirements 8.1**
  - [x] 16.4 编写属性测试：任务状态查询完整性
    - **Property 15: 任务状态查询完整性**
    - **Validates: Requirements 8.3, 8.5, 8.6**

- [x] 17. 配置默认值验证
  - [x] 17.1 实现默认值验证逻辑
    - 确保所有默认值在有效范围内
    - 未指定配置时使用默认值
    - _Requirements: 9.2, 9.3_
  - [x] 17.2 编写属性测试：配置默认值有效性
    - **Property 17: 配置默认值有效性**
    - **Validates: Requirements 9.2, 9.3**

- [x] 18. Final Checkpoint - 确保所有测试通过
  - 运行完整测试套件
  - 确保所有属性测试通过
  - 如有问题请询问用户

## Notes

- 每个任务引用了具体的需求编号以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试使用 hypothesis 库，每个测试至少运行 100 次迭代
- 所有任务都是必须完成的，包括测试任务
