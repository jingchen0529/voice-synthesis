-- 视频混剪任务表扩展字段迁移脚本
-- 添加新的配置字段以支持更多视频处理功能

-- 添加 BGM 淡入淡出字段
ALTER TABLE ipl_video_tasks 
ADD COLUMN bgm_fade_in FLOAT DEFAULT 0 COMMENT 'BGM淡入时长(秒) 0-5' AFTER bgm_volume,
ADD COLUMN bgm_fade_out FLOAT DEFAULT 0 COMMENT 'BGM淡出时长(秒) 0-5' AFTER bgm_fade_in;

-- 添加视频分辨率字段 (替代 video_size)
ALTER TABLE ipl_video_tasks 
ADD COLUMN video_resolution VARCHAR(10) DEFAULT '1080p' COMMENT '分辨率: 480p/720p/1080p/2k/4k' AFTER bgm_fade_out;

-- 修改 video_layout 字段默认值和注释
ALTER TABLE ipl_video_tasks 
MODIFY COLUMN video_layout VARCHAR(10) DEFAULT '9:16' COMMENT '布局比例: 9:16/3:4/1:1/4:3/16:9/21:9';

-- 添加平台预设字段
ALTER TABLE ipl_video_tasks 
ADD COLUMN platform_preset VARCHAR(50) COMMENT '平台预设: douyin/kuaishou/xiaohongshu/bilibili/youtube/instagram_reels/instagram_feed/weixin' AFTER video_fps;

-- 添加素材适配模式字段
ALTER TABLE ipl_video_tasks 
ADD COLUMN fit_mode VARCHAR(20) DEFAULT 'crop' COMMENT '素材适配模式: crop/fit/stretch' AFTER platform_preset;

-- 添加输出质量字段
ALTER TABLE ipl_video_tasks 
ADD COLUMN output_quality VARCHAR(20) DEFAULT 'high' COMMENT '输出质量: low/medium/high/ultra' AFTER output_duration;

-- 添加特效配置字段
ALTER TABLE ipl_video_tasks 
ADD COLUMN effect_type VARCHAR(50) COMMENT '动效类型: ken_burns/shake/zoom_in/zoom_out/pan_left/pan_right等' AFTER output_quality,
ADD COLUMN color_filter VARCHAR(50) DEFAULT 'none' COMMENT '颜色滤镜: none/grayscale/vintage/warm/cool/high_contrast/soft' AFTER effect_type,
ADD COLUMN brightness FLOAT DEFAULT 1.0 COMMENT '亮度 0.5-2.0' AFTER color_filter,
ADD COLUMN contrast FLOAT DEFAULT 1.0 COMMENT '对比度 0.5-2.0' AFTER brightness,
ADD COLUMN saturation FLOAT DEFAULT 1.0 COMMENT '饱和度 0-2.0' AFTER contrast;

-- 迁移旧数据: 将 video_size 值复制到 video_resolution
UPDATE ipl_video_tasks SET video_resolution = video_size WHERE video_resolution IS NULL OR video_resolution = '';

-- 迁移旧数据: 将旧的 video_layout 值转换为新格式
UPDATE ipl_video_tasks SET video_layout = '9:16' WHERE video_layout = 'portrait';
UPDATE ipl_video_tasks SET video_layout = '16:9' WHERE video_layout = 'landscape';

-- 可选: 删除旧的 video_size 字段 (建议在确认迁移成功后执行)
-- ALTER TABLE ipl_video_tasks DROP COLUMN video_size;
