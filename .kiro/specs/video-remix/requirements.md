# Requirements Document

## Introduction

视频混剪系统是一个自动化视频创作平台，允许用户通过 AI 生成文案、语音合成、多视频高光片段混剪和自动字幕生成来快速创建专业级短视频内容。系统基于 MoviePy 实现视频处理，支持竖屏/横屏多种分辨率输出，适用于抖音、快手等短视频平台内容创作。

## Glossary

- **Video_Remix_System**: 视频混剪系统，负责协调所有视频处理流程的核心系统
- **AI_Script_Generator**: AI 文案生成器，使用大语言模型根据主题生成视频脚本
- **TTS_Engine**: 语音合成引擎，将文本转换为语音音频（使用 Edge TTS）
- **Highlight_Extractor**: 高光片段提取器，从源视频中识别和提取精彩片段
- **Video_Compositor**: 视频合成器，负责将多个视频片段、音频、字幕合成为最终视频
- **Subtitle_Generator**: 字幕生成器，根据语音时间戳生成同步字幕
- **Media_Asset**: 媒体素材，包括视频片段、图片、音频等原始素材
- **Clip_Segment**: 视频片段，从源视频中截取的一段内容
- **Transition_Effect**: 转场效果，视频片段之间的过渡动画
- **BGM**: 背景音乐，视频的背景配乐

## Requirements

### Requirement 1: AI 文案生成

**User Story:** As a 内容创作者, I want to 通过输入主题自动生成视频文案, so that 我可以快速获得专业的视频脚本而无需手动撰写。

#### Acceptance Criteria

1. WHEN 用户输入视频主题和风格参数 THEN THE AI_Script_Generator SHALL 调用配置的 LLM 服务生成符合指定风格的文案
2. WHEN 生成文案时 THEN THE AI_Script_Generator SHALL 支持多种风格选项（口播、故事、科普、幽默）
3. WHEN 生成文案时 THEN THE AI_Script_Generator SHALL 根据目标时长（30秒/1分钟/3分钟/5分钟）控制文案长度
4. WHEN AI 服务不可用 THEN THE AI_Script_Generator SHALL 返回明确的错误信息并允许用户手动输入文案
5. THE AI_Script_Generator SHALL 支持中英文双语文案生成

### Requirement 2: 语音合成

**User Story:** As a 内容创作者, I want to 将文案自动转换为配音, so that 我可以获得专业的旁白音频而无需录音。

#### Acceptance Criteria

1. WHEN 用户提交文案进行语音合成 THEN THE TTS_Engine SHALL 使用 Edge TTS 生成对应的音频文件
2. WHEN 生成语音时 THEN THE TTS_Engine SHALL 同时返回词级别的时间戳信息用于字幕同步
3. THE TTS_Engine SHALL 支持多种音色选择（按语言和性别分类）
4. THE TTS_Engine SHALL 支持语速调节（慢速/正常/快速）
5. WHEN 语音合成完成 THEN THE TTS_Engine SHALL 输出 MP3 格式的音频文件
6. IF 语音合成失败 THEN THE TTS_Engine SHALL 返回错误信息并允许用户上传自定义配音

### Requirement 3: 视频素材管理

**User Story:** As a 内容创作者, I want to 上传和管理视频素材, so that 我可以使用自己的素材进行混剪。

#### Acceptance Criteria

1. THE Video_Remix_System SHALL 支持上传 MP4、MOV、AVI、MKV、WebM 格式的视频文件
2. THE Video_Remix_System SHALL 支持上传 JPG、PNG、WebP 格式的图片文件
3. WHEN 上传视频文件 THEN THE Video_Remix_System SHALL 限制单个文件大小不超过 150MB
4. WHEN 上传图片文件 THEN THE Video_Remix_System SHALL 限制单个文件大小不超过 10MB
5. WHEN 视频上传完成 THEN THE Video_Remix_System SHALL 自动提取视频信息（时长、分辨率、帧率）
6. THE Video_Remix_System SHALL 支持批量上传多个素材文件

### Requirement 4: 高光片段提取

**User Story:** As a 内容创作者, I want to 从长视频中提取高光片段, so that 我可以快速获取精彩内容用于混剪。

#### Acceptance Criteria

1. WHEN 用户选择视频进行高光提取 THEN THE Highlight_Extractor SHALL 生成视频缩略图预览
2. THE Highlight_Extractor SHALL 支持用户手动指定片段的起止时间
3. WHEN 用户指定时间范围 THEN THE Highlight_Extractor SHALL 裁剪出对应的视频片段
4. THE Highlight_Extractor SHALL 验证起始时间小于结束时间
5. WHEN 裁剪完成 THEN THE Highlight_Extractor SHALL 返回裁剪后视频的预览 URL 和时长信息

### Requirement 5: 视频分辨率与布局

**User Story:** As a 内容创作者, I want to 选择多种视频分辨率和布局, so that 我可以针对不同平台（抖音、B站、YouTube等）输出适配的视频格式。

#### Acceptance Criteria

1. THE Video_Compositor SHALL 支持以下标准分辨率：
   - 480p（标清）
   - 720p（高清）
   - 1080p（全高清）
   - 2K（2560x1440）
   - 4K（3840x2160）

2. THE Video_Compositor SHALL 支持以下视频布局和宽高比：
   - 竖屏 9:16（抖音、快手、TikTok 短视频）
   - 竖屏 3:4（小红书图文视频）
   - 方形 1:1（Instagram、微信朋友圈）
   - 横屏 4:3（传统视频）
   - 横屏 16:9（YouTube、B站标准）
   - 横屏 21:9（电影宽银幕）

3. THE Video_Compositor SHALL 支持以下帧率选项：
   - 24fps（电影感）
   - 25fps（PAL 标准）
   - 30fps（网络视频标准）
   - 50fps（高帧率）
   - 60fps（游戏/运动视频）

4. THE Video_Compositor SHALL 提供平台预设配置：
   - 抖音/TikTok：1080x1920 (9:16), 30fps
   - 快手：1080x1920 (9:16), 30fps
   - 小红书：1080x1440 (3:4), 30fps
   - B站：1920x1080 (16:9), 30fps
   - YouTube：1920x1080 (16:9), 30fps
   - Instagram Reels：1080x1920 (9:16), 30fps
   - Instagram Feed：1080x1080 (1:1), 30fps
   - 微信视频号：1080x1920 (9:16), 30fps

5. WHEN 用户选择平台预设 THEN THE Video_Compositor SHALL 自动应用对应的分辨率、布局和帧率配置

### Requirement 6: 视频混剪合成

**User Story:** As a 内容创作者, I want to 将多个视频片段自动混剪成完整视频, so that 我可以快速生成成品视频。

#### Acceptance Criteria

1. WHEN 素材尺寸与目标尺寸不匹配 THEN THE Video_Compositor SHALL 支持以下适配模式：
   - 裁剪填充（Crop to Fill）：裁剪素材以完全填充画面
   - 适应填充（Fit）：保持素材比例，空白区域填充背景色
   - 拉伸填充（Stretch）：拉伸素材以填充画面

2. THE Video_Compositor SHALL 支持配置每个片段的最小和最大时长（1-60秒）

3. WHEN 素材数量不足以覆盖配音时长 THEN THE Video_Compositor SHALL 循环使用素材

4. THE Video_Compositor SHALL 支持以下转场效果：
   - 无转场（直接切换）
   - 淡入淡出（Fade/Crossfade）
   - 滑动（Slide：左/右/上/下）
   - 缩放（Zoom In/Out）
   - 溶解（Dissolve）
   - 擦除（Wipe：左/右/上/下）

5. THE Video_Compositor SHALL 支持配置转场时长（0.3-2.0秒）

6. WHEN 合成视频时 THEN THE Video_Compositor SHALL 将配音作为主音轨

7. THE Video_Compositor SHALL 支持添加背景音乐并可调节音量（0-100%）

8. THE Video_Compositor SHALL 支持配置背景音乐的淡入淡出效果

9. WHEN 视频合成完成 THEN THE Video_Compositor SHALL 输出 MP4 格式（H.264 编码）的视频文件

10. THE Video_Compositor SHALL 支持配置输出视频的码率质量（低/中/高/极高）

### Requirement 6: 字幕生成与渲染

**User Story:** As a 内容创作者, I want to 自动生成与配音同步的字幕, so that 视频内容更易于观看和理解。

#### Acceptance Criteria

1. WHEN 启用字幕功能 THEN THE Subtitle_Generator SHALL 根据 TTS 返回的时间戳生成句子级字幕
2. THE Subtitle_Generator SHALL 支持配置字幕字体、大小、颜色
3. THE Subtitle_Generator SHALL 支持配置字幕描边颜色和宽度
4. THE Subtitle_Generator SHALL 支持配置字幕位置（顶部、居中、底部）
5. WHEN 渲染字幕时 THEN THE Subtitle_Generator SHALL 确保字幕与配音时间精确同步
6. THE Subtitle_Generator SHALL 支持中英文字幕渲染

### Requirement 7: 任务管理与进度追踪

**User Story:** As a 内容创作者, I want to 追踪视频生成任务的进度, so that 我可以了解处理状态并在完成后下载视频。

#### Acceptance Criteria

1. WHEN 创建视频任务 THEN THE Video_Remix_System SHALL 返回唯一的任务 ID
2. THE Video_Remix_System SHALL 在后台异步处理视频生成任务
3. WHEN 查询任务状态 THEN THE Video_Remix_System SHALL 返回当前进度百分比和状态消息
4. THE Video_Remix_System SHALL 支持以下任务状态：等待中、处理中、已完成、失败
5. WHEN 任务完成 THEN THE Video_Remix_System SHALL 提供视频下载链接
6. IF 任务失败 THEN THE Video_Remix_System SHALL 返回错误原因
7. THE Video_Remix_System SHALL 保存用户的历史任务记录

### Requirement 8: 配置与参数管理

**User Story:** As a 内容创作者, I want to 灵活配置视频生成的各项参数, so that 我可以根据需求定制输出效果。

#### Acceptance Criteria

1. THE Video_Remix_System SHALL 提供 API 返回所有可配置选项（布局、分辨率、转场、字幕位置等）
2. THE Video_Remix_System SHALL 为所有配置项提供合理的默认值
3. WHEN 用户未指定某配置项 THEN THE Video_Remix_System SHALL 使用默认值
4. THE Video_Remix_System SHALL 验证用户输入的配置参数在有效范围内
5. IF 配置参数无效 THEN THE Video_Remix_System SHALL 返回明确的错误提示

### Requirement 9: 视频特效与滤镜

**User Story:** As a 内容创作者, I want to 为视频添加特效和滤镜, so that 我可以提升视频的视觉效果和专业感。

#### Acceptance Criteria

1. THE Video_Compositor SHALL 支持以下图片/视频动效：
   - Ken Burns 效果（缓慢缩放平移）
   - 轻微抖动效果
   - 缩放动画（Zoom In/Out）
   - 平移动画（Pan 左/右/上/下）

2. THE Video_Compositor SHALL 支持以下颜色滤镜：
   - 原始（无滤镜）
   - 黑白
   - 复古/怀旧
   - 暖色调
   - 冷色调
   - 高对比度
   - 柔和

3. THE Video_Compositor SHALL 支持调节视频亮度、对比度、饱和度

4. THE Video_Compositor SHALL 支持为图片素材添加动态效果以增加视觉吸引力
