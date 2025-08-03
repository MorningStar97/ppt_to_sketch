# 云服务器部署指南

📋 本文档详细介绍如何将PPT to Sketch转换服务部署到阿里云等云服务器上。

## 🚀 部署方案概览

### 推荐架构
```
用户 → 域名/CDN → Nginx → Gunicorn → Django应用
                     ↓
                  PostgreSQL数据库
                     ↓
                  文件存储(OSS)
```

### 服务器配置推荐
- **CPU**: 2核及以上
- **内存**: 4GB及以上（转换大文件需要更多内存）
- **硬盘**: 40GB SSD（系统盘）+ 数据盘（可选）
- **带宽**: 5Mbps及以上

## 🛠️ 阿里云ECS部署步骤

### 1. 购买和配置ECS实例

#### 1.1 创建ECS实例
```bash
# 推荐配置
- 实例规格：ecs.c6.large (2vCPU 4GB内存)
- 操作系统：Ubuntu 20.04 LTS 或 CentOS 8
- 公网IP：分配
- 安全组：允许22(SSH), 80(HTTP), 443(HTTPS)端口
```

#### 1.2 连接服务器
```bash
# 使用SSH连接
ssh root@your_server_ip

# 或使用阿里云提供的密钥对
ssh -i your_private_key.pem root@your_server_ip
```

### 2. 系统环境准备

#### 2.1 更新系统
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
# 或新版本
sudo dnf update -y
```

#### 2.2 安装基础软件
```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl wget

# CentOS/RHEL  
sudo yum install -y python3 python3-pip nginx postgresql postgresql-server postgresql-contrib redis git curl wget
# 或
sudo dnf install -y python3 python3-pip nginx postgresql postgresql-server postgresql-contrib redis git curl wget
```

#### 2.3 配置防火墙
```bash
# Ubuntu (ufw)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# CentOS (firewalld)
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. 数据库配置

#### 3.1 PostgreSQL安装和配置
```bash
# 初始化数据库 (CentOS需要)
sudo postgresql-setup --initdb  # 仅CentOS需要

# 启动PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE ppt_to_sketch;
CREATE USER ppt_user WITH PASSWORD 'your_strong_password';
ALTER ROLE ppt_user SET client_encoding TO 'utf8';
ALTER ROLE ppt_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ppt_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ppt_to_sketch TO ppt_user;
\q
EOF
```

#### 3.2 Redis配置
```bash
# 启动Redis
sudo systemctl start redis
sudo systemctl enable redis

# 测试Redis连接
redis-cli ping  # 应返回 PONG
```

### 4. 应用部署

#### 4.1 创建应用用户
```bash
# 创建专用用户
sudo adduser pptuser
sudo usermod -aG sudo pptuser

# 切换到应用用户
sudo su - pptuser
```

#### 4.2 部署应用代码
```bash
# 克隆项目
cd /home/pptuser
git clone https://github.com/MorningStar97/ppt_to_sketch.git
cd ppt_to_sketch

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # 生产环境额外依赖
```

#### 4.3 生产环境配置
```bash
# 创建生产配置文件
cp ppt_to_sketch_service/settings.py ppt_to_sketch_service/settings_prod.py
```

编辑生产配置：
```python
# ppt_to_sketch_service/settings_prod.py
import os
from .settings import *

# 安全设置
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'your_server_ip']
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key')

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ppt_to_sketch',
        'USER': 'ppt_user',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_strong_password'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Redis配置 (如果使用Celery)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 静态文件
STATIC_ROOT = '/home/pptuser/ppt_to_sketch/staticfiles'
MEDIA_ROOT = '/home/pptuser/ppt_to_sketch/media'

# 安全设置
SECURE_SSL_REDIRECT = True  # 启用HTTPS后
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 文件上传限制
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/pptuser/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

#### 4.4 环境变量配置
```bash
# 创建环境变量文件
cat > /home/pptuser/ppt_to_sketch/.env << EOF
SECRET_KEY=your-very-long-random-secret-key
DB_PASSWORD=your_strong_password
DJANGO_SETTINGS_MODULE=ppt_to_sketch_service.settings_prod
EOF

# 设置权限
chmod 600 /home/pptuser/ppt_to_sketch/.env
```

#### 4.5 数据库初始化
```bash
# 创建日志目录
mkdir -p /home/pptuser/logs

# 运行数据库迁移
cd /home/pptuser/ppt_to_sketch
source venv/bin/activate
python manage.py migrate --settings=ppt_to_sketch_service.settings_prod

# 收集静态文件
python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_prod

# 创建超级用户
python manage.py createsuperuser --settings=ppt_to_sketch_service.settings_prod
```

### 5. Web服务器配置

#### 5.1 Gunicorn配置
```bash
# 创建Gunicorn配置文件
cat > /home/pptuser/ppt_to_sketch/gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
preload_app = True
user = "pptuser"
group = "pptuser"
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https'
}
EOF
```

#### 5.2 系统服务配置
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/ppt-to-sketch.service << EOF
[Unit]
Description=PPT to Sketch Django Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=pptuser
Group=pptuser
RuntimeDirectory=ppt-to-sketch
WorkingDirectory=/home/pptuser/ppt_to_sketch
Environment=DJANGO_SETTINGS_MODULE=ppt_to_sketch_service.settings_prod
EnvironmentFile=/home/pptuser/ppt_to_sketch/.env
ExecStart=/home/pptuser/ppt_to_sketch/venv/bin/gunicorn -c gunicorn.conf.py ppt_to_sketch_service.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start ppt-to-sketch
sudo systemctl enable ppt-to-sketch

# 检查状态
sudo systemctl status ppt-to-sketch
```

#### 5.3 Nginx配置
```bash
# 创建Nginx配置
sudo tee /etc/nginx/sites-available/ppt-to-sketch << EOF
upstream ppt_to_sketch {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL证书配置 (需要申请SSL证书)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # 安全头
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 上传文件大小限制
    client_max_body_size 100M;
    
    # 静态文件
    location /static/ {
        alias /home/pptuser/ppt_to_sketch/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件
    location /media/ {
        alias /home/pptuser/ppt_to_sketch/media/;
        expires 7d;
    }
    
    # 主应用
    location / {
        proxy_pass http://ppt_to_sketch;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/ppt-to-sketch /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

## 🔒 SSL证书配置

### 使用Let's Encrypt免费证书
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu
# 或
sudo yum install certbot python3-certbot-nginx  # CentOS

# 申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控和日志

### 1. 日志配置
```bash
# 创建日志轮转配置
sudo tee /etc/logrotate.d/ppt-to-sketch << EOF
/home/pptuser/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 pptuser pptuser
    postrotate
        systemctl reload ppt-to-sketch
    endscript
}
EOF
```

### 2. 监控脚本
```bash
# 创建健康检查脚本
cat > /home/pptuser/health_check.sh << EOF
#!/bin/bash
# 检查服务状态
if ! systemctl is-active --quiet ppt-to-sketch; then
    echo "PPT to Sketch service is down"
    # 发送告警 (可集成钉钉、邮件等)
fi

# 检查磁盘空间
DISK_USAGE=\$(df / | awk 'NR==2 {print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 80 ]; then
    echo "Disk usage is high: \${DISK_USAGE}%"
fi
EOF

chmod +x /home/pptuser/health_check.sh

# 设置定时检查
crontab -e
# 添加：*/5 * * * * /home/pptuser/health_check.sh
```

## 🚀 性能优化

### 1. 数据库优化
```sql
-- PostgreSQL配置优化
-- 编辑 /etc/postgresql/*/main/postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### 2. Redis优化
```bash
# 编辑 /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 3. 应用优化
```python
# 在settings_prod.py中添加
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 使用Celery处理长时间任务
CELERY_TASK_ROUTES = {
    'converter.tasks.convert_ppt_to_sketch': {'queue': 'conversion'},
}
```

## 🔧 部署检查清单

### 部署前检查
- [ ] 服务器规格满足要求
- [ ] 域名解析配置正确
- [ ] SSL证书申请完成
- [ ] 数据库和Redis正常运行
- [ ] 防火墙配置正确

### 部署后检查
- [ ] 应用服务正常启动
- [ ] Nginx反向代理工作正常
- [ ] 静态文件访问正常
- [ ] 文件上传功能正常
- [ ] API接口响应正常
- [ ] 管理后台可以访问
- [ ] 日志正常记录
- [ ] 监控脚本运行正常

## 🆘 常见问题解决

### 1. 内存不足
```bash
# 创建交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. 文件权限问题
```bash
# 确保权限正确
sudo chown -R pptuser:pptuser /home/pptuser/ppt_to_sketch
chmod -R 755 /home/pptuser/ppt_to_sketch
chmod -R 755 /home/pptuser/ppt_to_sketch/media
```

### 3. 502 Bad Gateway
```bash
# 检查Gunicorn状态
sudo systemctl status ppt-to-sketch
# 检查日志
sudo journalctl -u ppt-to-sketch -f
```

## 💰 成本估算

### 阿里云ECS成本 (月费用)
- **基础型**: 2核4GB + 3Mbps带宽 ≈ ¥150-200/月
- **标准型**: 4核8GB + 5Mbps带宽 ≈ ¥300-400/月
- **高配型**: 8核16GB + 10Mbps带宽 ≈ ¥600-800/月

### 额外服务 (可选)
- **对象存储OSS**: ¥10-50/月 (文件存储)
- **CDN加速**: ¥20-100/月 (静态资源)
- **SSL证书**: 免费 (Let's Encrypt) 或 ¥200-500/年 (付费证书)
- **域名**: ¥50-100/年

## 🔄 维护和更新

### 代码更新流程
```bash
# 1. 备份数据库
sudo -u postgres pg_dump ppt_to_sketch > backup_$(date +%Y%m%d).sql

# 2. 拉取最新代码
cd /home/pptuser/ppt_to_sketch
git pull origin main

# 3. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 数据库迁移
python manage.py migrate --settings=ppt_to_sketch_service.settings_prod

# 5. 收集静态文件
python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_prod

# 6. 重启服务
sudo systemctl restart ppt-to-sketch
```

### 备份策略
```bash
# 创建自动备份脚本
cat > /home/pptuser/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/pptuser/backups"
DATE=\$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p \$BACKUP_DIR

# 备份数据库
sudo -u postgres pg_dump ppt_to_sketch > \$BACKUP_DIR/db_\$DATE.sql

# 备份媒体文件
tar -czf \$BACKUP_DIR/media_\$DATE.tar.gz -C /home/pptuser/ppt_to_sketch media

# 清理7天前的备份
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/pptuser/backup.sh

# 设置定时备份
crontab -e
# 添加：0 2 * * * /home/pptuser/backup.sh
```

这个部署指南提供了完整的生产环境部署方案，包括安全配置、性能优化和维护策略。根据实际需求，您可以选择合适的配置级别。 