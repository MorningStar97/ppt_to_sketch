# Docker 部署指南

🐳 本文档介绍如何使用Docker将PPT to Sketch服务部署到阿里云ECS服务器。

## 🚀 快速部署流程

### 1. 连接ECS服务器

```bash
# 连接到您的ECS服务器
ssh root@47.100.31.84

# 确认Docker已安装
docker --version
docker-compose --version
```

### 2. 服务器环境准备

```bash
# 更新系统
yum update -y

# 安装必要工具
yum install -y git curl wget

# 安装docker-compose（如果没有）
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
systemctl start docker
systemctl enable docker
```

### 3. 克隆项目代码

```bash
# 在服务器上克隆项目
cd /opt
git clone https://github.com/MorningStar97/ppt_to_sketch.git
cd ppt_to_sketch
```

### 4. 创建Docker配置文件

#### 4.1 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=ppt_to_sketch_service.settings_docker

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements_prod.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements_prod.txt

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/media/uploads/ppt /app/media/outputs/sketch /app/staticfiles /app/logs

# 设置权限
RUN chmod +x start.sh

# 收集静态文件
RUN python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_docker

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "ppt_to_sketch_service.wsgi:application"]
```

#### 4.2 创建 docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:13
    restart: always
    environment:
      POSTGRES_DB: ppt_to_sketch
      POSTGRES_USER: ppt_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    restart: always
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  web:
    build: .
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
      - DATABASE_URL=postgresql://ppt_user:${DB_PASSWORD}@db:5432/ppt_to_sketch
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    command: >
      sh -c "python manage.py migrate --settings=ppt_to_sketch_service.settings_docker &&
             python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_docker &&
             gunicorn --config gunicorn.conf.py ppt_to_sketch_service.wsgi:application"

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    depends_on:
      - web

volumes:
  postgres_data:
```

#### 4.3 创建Docker专用配置文件

```python
# ppt_to_sketch_service/settings_docker.py
import os
from .settings import *

# 安全设置
DEBUG = False
ALLOWED_HOSTS = ['*']  # 生产环境请设置具体域名
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key')

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ppt_to_sketch',
        'USER': 'ppt_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'db',  # Docker服务名
        'PORT': '5432',
    }
}

# Redis配置
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# 静态文件和媒体文件
STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'converter': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 文件上传限制
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
```

#### 4.4 创建Nginx配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name _;

        client_max_body_size 100M;

        # 静态文件
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # 媒体文件
        location /media/ {
            alias /app/media/;
            expires 7d;
        }

        # 主应用
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
            proxy_read_timeout 300;
            send_timeout 300;
        }
    }
}
```

#### 4.5 创建环境变量文件

```bash
# .env
SECRET_KEY=your-very-long-random-secret-key-change-this-in-production
DB_PASSWORD=your-strong-database-password
```

### 5. 部署和启动

```bash
# 1. 创建Docker配置文件（在服务器上执行）
cd /opt/ppt_to_sketch

# 2. 创建上述配置文件
# 注意：需要手动创建 Dockerfile, docker-compose.yml, settings_docker.py, nginx.conf, .env

# 3. 生成安全密钥
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 4. 编辑 .env 文件，设置密钥和密码
vi .env

# 5. 构建和启动服务
docker-compose up --build -d

# 6. 查看服务状态
docker-compose ps

# 7. 查看日志
docker-compose logs -f web
```

### 6. 创建超级用户

```bash
# 进入web容器创建超级用户
docker-compose exec web python manage.py createsuperuser --settings=ppt_to_sketch_service.settings_docker
```

### 7. 验证部署

```bash
# 检查服务状态
curl http://47.100.31.84/

# 检查API接口
curl http://47.100.31.84/api/tasks/

# 在浏览器中访问
# http://47.100.31.84/
```

## 🔧 管理命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart web
```

### 更新代码
```bash
# 拉取最新代码
git pull origin main

# 重新构建和启动
docker-compose up --build -d
```

### 备份数据
```bash
# 备份数据库
docker-compose exec db pg_dump -U ppt_user ppt_to_sketch > backup_$(date +%Y%m%d).sql

# 备份媒体文件
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

## 🛡️ 安全配置

### 防火墙设置
```bash
# 只开放必要端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-port=22/tcp
firewall-cmd --reload
```

### SSL证书配置（可选）
```bash
# 安装certbot
yum install -y certbot

# 申请SSL证书（需要域名）
certbot certonly --standalone -d yourdomain.com
```

## 📊 监控和维护

### 系统监控
```bash
# 查看资源使用
docker stats

# 查看磁盘使用
df -h

# 清理Docker
docker system prune -f
```

### 日志轮转
Docker会自动处理日志轮转，但可以配置限制：

```yaml
# 在docker-compose.yml中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🆘 故障排除

### 常见问题

1. **端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep :80
```

2. **容器无法启动**
```bash
# 查看详细错误
docker-compose logs web
```

3. **数据库连接失败**
```bash
# 检查数据库容器状态
docker-compose exec db psql -U ppt_user -d ppt_to_sketch
```

4. **静态文件不显示**
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_docker
```

这种Docker部署方式简单可靠，适合快速部署和测试！ 