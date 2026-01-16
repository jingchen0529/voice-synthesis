-- 获客线索表
-- 用于存储从各渠道获取的潜在客户信息

CREATE TABLE IF NOT EXISTS `ipl_leads` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    
    -- 渠道来源: google/yahoo/tiktok/facebook/youtube
    `channel` VARCHAR(50) NOT NULL COMMENT '渠道来源',
    
    -- 获客方式: whatsapp/email/competitor_fans/comments/website/phone
    `acquisition_type` VARCHAR(50) NOT NULL COMMENT '获客方式',
    
    -- 线索基本信息
    `name` VARCHAR(200) DEFAULT NULL COMMENT '名称/昵称',
    `contact` VARCHAR(500) DEFAULT NULL COMMENT '联系方式',
    `website` VARCHAR(500) DEFAULT NULL COMMENT '网址/主页链接',
    `description` TEXT DEFAULT NULL COMMENT '描述/备注',
    
    -- 来源详情
    `source_url` VARCHAR(1000) DEFAULT NULL COMMENT '来源页面URL',
    `source_keyword` VARCHAR(200) DEFAULT NULL COMMENT '搜索关键词',
    
    -- 扩展数据
    `extra_data` TEXT DEFAULT NULL COMMENT '扩展数据JSON',
    
    -- 状态: 0-未处理, 1-已联系, 2-有意向, 3-已成交, 4-无效
    `status` INT DEFAULT 0 COMMENT '状态',
    
    -- 时间戳
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
    
    -- 索引
    INDEX `idx_channel` (`channel`),
    INDEX `idx_acquisition_type` (`acquisition_type`),
    INDEX `idx_source_keyword` (`source_keyword`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='获客线索表';
