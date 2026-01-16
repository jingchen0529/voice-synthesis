-- Edge TTS 音色表
CREATE TABLE IF NOT EXISTS edge_tts_voices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    short_name VARCHAR(100) NOT NULL UNIQUE COMMENT '音色短名称，如 zh-CN-XiaoxiaoNeural',
    name VARCHAR(200) NOT NULL COMMENT '完整名称',
    locale VARCHAR(20) NOT NULL COMMENT '语言区域，如 zh-CN',
    language VARCHAR(50) NOT NULL COMMENT '语言名称，如 Chinese',
    gender VARCHAR(20) NOT NULL COMMENT '性别：Male/Female',
    display_name VARCHAR(100) COMMENT '显示名称，如 晓晓',
    voice_type VARCHAR(50) COMMENT '音色类型',
    status TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_locale (locale),
    INDEX idx_gender (gender),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Edge TTS 音色配置表';
