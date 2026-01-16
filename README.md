# 部署文档

## 系统要求

- Ubuntu 20.04+ / CentOS 7+
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 6+
- Nginx

## 一、服务器环境准备

### 1.1 安装基础依赖

```bash
# Ubuntu
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip nodejs npm mysql-server redis-server nginx ffmpeg

# CentOS
sudo yum install -y python310 nodejs npm mysql-server redis nginx ffmpeg
```

### 1.2 创建项目目录

```bash
sudo mkdir -p /var/www/voice-synthesis
sudo chown $USER:$USER /var/www/voice-synthesis
cd /var/www/voice-synthesis
```

### 1.3 克隆代码

```bash
git clone <your-repo-url> .
```

## 二、后端部署

### 2.1 创建 Python 虚拟环境

```bash
cd /var/www/voice-synthesis/backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 配置环境变量

```bash
cp .env.example .env
vim .env
```

编辑 `.env` 文件：

```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=voice_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=voice_synthesis

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your_super_secret_key_change_this

# API
API_BASE_URL=https://your-domain.com

# AI API Keys (按需配置)
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### 2.3 初始化数据库

```bash
# 登录 MySQL 创建数据库和用户
mysql -u root -p

CREATE DATABASE voice_synthesis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'voice_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON voice_synthesis.* TO 'voice_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 执行初始化 SQL
mysql -u voice_user -p voice_synthesis < sql/init.sql
mysql -u voice_user -p voice_synthesis < sql/003_video_tasks.sql
mysql -u voice_user -p voice_synthesis < sql/004_edge_tts_voices.sql
mysql -u voice_user -p voice_synthesis < sql/005_video_tasks_update.sql
```

### 2.4 初始化 Edge TTS 音色

```bash
source .venv/bin/activate
python scripts/init_edge_tts_voices.py
```

### 2.5 创建必要目录

```bash
mkdir -p uploads outputs uploads/bgm uploads/videos uploads/images
touch uploads/.gitkeep outputs/.gitkeep
```

### 2.6 配置 Systemd 服务

创建后端 API 服务：

```bash
sudo vim /etc/systemd/system/voice-api.service
```

```ini
[Unit]
Description=Voice Synthesis API
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/voice-synthesis/backend
Environment="PATH=/var/www/voice-synthesis/backend/.venv/bin"
ExecStart=/var/www/voice-synthesis/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

创建 Celery Worker 服务（用于语音克隆任务）：

```bash
sudo vim /etc/systemd/system/voice-celery.service
```

```ini
[Unit]
Description=Voice Synthesis Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/voice-synthesis/backend
Environment="PATH=/var/www/voice-synthesis/backend/.venv/bin"
ExecStart=/var/www/voice-synthesis/backend/.venv/bin/celery -A app.core.celery_app worker --loglevel=info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-api voice-celery
sudo systemctl start voice-api voice-celery
```

## 三、前端部署

### 3.1 安装依赖并构建

```bash
cd /var/www/voice-synthesis/frontend
npm install
```

### 3.2 配置环境变量

```bash
cp .env.example .env
vim .env
```

```env
VITE_API_BASE_URL=https://your-domain.com/api
```

### 3.3 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

## 四、Nginx 配置

```bash
sudo vim /etc/nginx/sites-available/voice-synthesis
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 前端静态文件
    root /var/www/voice-synthesis/frontend/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 文件上传大小限制
        client_max_body_size 200M;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件（上传和输出）
    location /static/uploads/ {
        alias /var/www/voice-synthesis/backend/uploads/;
    }

    location /static/outputs/ {
        alias /var/www/voice-synthesis/backend/outputs/;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/voice-synthesis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 五、SSL 证书（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 六、文件权限

```bash
sudo chown -R www-data:www-data /var/www/voice-synthesis
sudo chmod -R 755 /var/www/voice-synthesis
sudo chmod -R 775 /var/www/voice-synthesis/backend/uploads
sudo chmod -R 775 /var/www/voice-synthesis/backend/outputs
```

## 七、常用命令

```bash
# 查看服务状态
sudo systemctl status voice-api
sudo systemctl status voice-celery

# 查看日志
sudo journalctl -u voice-api -f
sudo journalctl -u voice-celery -f

# 重启服务
sudo systemctl restart voice-api voice-celery

# 更新代码后
cd /var/www/voice-synthesis
git pull
cd backend && source .venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart voice-api voice-celery
```

## 八、AI 模型部署（语音克隆功能）

如果需要语音克隆功能，需要下载 XTTS v2 模型：

```bash
cd /var/www/voice-synthesis/backend/ai_models
# 从 Hugging Face 下载模型
git lfs install
git clone https://huggingface.co/coqui/XTTS-v2 tts_models--multilingual--multi-dataset--xtts_v2
```

注意：模型文件约 2GB，需要 GPU 支持才能高效运行。

## 九、防火墙配置

```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 十、备份策略

```bash
# 数据库备份
mysqldump -u voice_user -p voice_synthesis > backup_$(date +%Y%m%d).sql

# 上传文件备份
tar -czf uploads_$(date +%Y%m%d).tar.gz /var/www/voice-synthesis/backend/uploads
```
