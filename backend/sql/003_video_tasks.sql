-- 视频混剪任务表
CREATE TABLE IF NOT EXISTS ipl_video_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL UNIQUE,
    celery_task_id VARCHAR(64),
    user_id BIGINT NOT NULL,
    
    -- 文案配置
    topic VARCHAR(500),
    script TEXT,
    script_language VARCHAR(10) DEFAULT 'zh',
    
    -- 配音配置
    voice_language VARCHAR(10) DEFAULT 'zh',
    voice_name VARCHAR(100),
    voice_speed VARCHAR(20) DEFAULT 'normal',
    voice_audio_url VARCHAR(500),
    
    -- 背景音乐配置
    bgm_enabled TINYINT DEFAULT 0,
    bgm_path VARCHAR(500),
    bgm_volume FLOAT DEFAULT 0.3,
    
    -- 视频配置
    video_layout VARCHAR(50) DEFAULT 'portrait',
    video_fps INT DEFAULT 30,
    video_size VARCHAR(20) DEFAULT '1080p',
    clip_min_duration FLOAT DEFAULT 3.0,
    clip_max_duration FLOAT DEFAULT 10.0,
    
    -- 素材配置
    use_local_videos TINYINT DEFAULT 0,
    local_video_dir VARCHAR(500),
    
    -- 转场配置
    transition_enabled TINYINT DEFAULT 1,
    transition_type VARCHAR(50) DEFAULT 'fade',
    transition_effect VARCHAR(50) DEFAULT 'fade',
    transition_duration FLOAT DEFAULT 1.0,
    
    -- 字幕配置
    subtitle_enabled TINYINT DEFAULT 1,
    subtitle_font VARCHAR(100) DEFAULT 'SimHei',
    subtitle_size INT DEFAULT 48,
    subtitle_color VARCHAR(20) DEFAULT '#FFFFFF',
    subtitle_stroke_color VARCHAR(20) DEFAULT '#000000',
    subtitle_stroke_width FLOAT DEFAULT 2.0,
    subtitle_position VARCHAR(50) DEFAULT 'bottom',
    subtitle_line_spacing INT DEFAULT 2,
    
    -- 输出配置
    output_video_url VARCHAR(500),
    output_duration FLOAT,
    
    -- 任务状态
    status TINYINT DEFAULT 0 COMMENT '0-待处理 1-处理中 2-完成 3-失败',
    progress INT DEFAULT 0,
    progress_message VARCHAR(200),
    error_message TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_task_id (task_id),
    INDEX idx_celery_task_id (celery_task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    
    FOREIGN KEY (user_id) REFERENCES ipl_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
