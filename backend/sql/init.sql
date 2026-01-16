-- 创建数据库
CREATE DATABASE IF NOT EXISTS voice_synthesis DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE voice_synthesis;

-- 用户表
CREATE TABLE IF NOT EXISTS ipl_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    avatar VARCHAR(500),
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用 1-正常',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- API密钥表 (AK/SK)
CREATE TABLE IF NOT EXISTS ipl_api_keys (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    access_key VARCHAR(64) NOT NULL UNIQUE COMMENT 'AK',
    secret_key VARCHAR(128) NOT NULL COMMENT 'SK (加密存储)',
    name VARCHAR(100) COMMENT '密钥名称',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用 1-正常',
    expires_at DATETIME COMMENT '过期时间，NULL表示永不过期',
    last_used_at DATETIME COMMENT '最后使用时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_access_key (access_key),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES ipl_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';

-- 应用/服务表
CREATE TABLE IF NOT EXISTS ipl_services (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '服务代码: tts, video_mix, tiktok_crawler',
    name VARCHAR(100) NOT NULL COMMENT '服务名称',
    description TEXT COMMENT '服务描述',
    icon VARCHAR(500) COMMENT '图标URL',
    quota_per_call INT DEFAULT 1 COMMENT '每次调用消耗配额',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-下线 1-正常 2-维护中',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应用服务表';

-- 初始化服务数据
INSERT INTO ipl_services (code, name, description, quota_per_call, sort_order) VALUES
('tts', '语音克隆', '基于XTTS v2的语音克隆服务，支持多语言', 1, 1),
('video_mix', '视频混剪', 'AI智能视频混剪服务', 2, 2),
('tiktok_crawler', 'TikTok爬虫', 'TikTok视频数据采集服务', 1, 3);

-- 用户服务配额表
CREATE TABLE IF NOT EXISTS ipl_user_service_quotas (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    service_id BIGINT NOT NULL,
    free_quota INT DEFAULT 0 COMMENT '免费配额',
    paid_quota INT DEFAULT 0 COMMENT '付费配额',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_service (user_id, service_id),
    INDEX idx_user_id (user_id),
    INDEX idx_service_id (service_id),
    FOREIGN KEY (user_id) REFERENCES ipl_users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES ipl_services(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户服务配额表';

-- TTS任务表
CREATE TABLE IF NOT EXISTS ipl_tts_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64) NOT NULL UNIQUE COMMENT '任务UUID',
    user_id BIGINT NOT NULL,
    text TEXT NOT NULL COMMENT '合成文本',
    language VARCHAR(10) DEFAULT 'zh' COMMENT '语言代码',
    speaker_audio_url VARCHAR(500) COMMENT '参考音频URL',
    output_audio_url VARCHAR(500) COMMENT '输出音频URL',
    status TINYINT DEFAULT 0 COMMENT '状态: 0-待处理 1-处理中 2-完成 3-失败',
    error_message TEXT COMMENT '错误信息',
    duration_seconds FLOAT COMMENT '处理耗时(秒)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES ipl_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS任务表';

-- 配额使用记录表
CREATE TABLE IF NOT EXISTS ipl_quota_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    service_id BIGINT NOT NULL COMMENT '服务ID',
    task_id VARCHAR(64) COMMENT '关联任务ID',
    quota_type ENUM('free', 'paid') NOT NULL COMMENT '消耗配额类型',
    amount INT DEFAULT 1 COMMENT '消耗数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_service_id (service_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES ipl_users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES ipl_services(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配额使用记录表';

-- API调用日志表
CREATE TABLE IF NOT EXISTS ipl_api_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    api_key_id BIGINT,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    status_code INT,
    request_body TEXT,
    response_time_ms INT COMMENT '响应时间(毫秒)',
    ip VARCHAR(50),
    user_agent VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_api_key_id (api_key_id),
    INDEX idx_created_at (created_at),
    INDEX idx_path (path(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API调用日志表';
