#!/bin/bash

# PPT to Sketch 服务 - 快速Docker部署脚本
# 使用方法：在ECS服务器上运行此脚本

set -e

echo "🚀 PPT to Sketch 服务 - Docker 快速部署"
echo "==============================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请以root用户运行此脚本"
    exit 1
fi

# 1. 环境检查和准备
echo "📋 1. 检查系统环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装 docker-compose..."
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 启动Docker服务
echo "🔧 启动 Docker 服务..."
systemctl start docker
systemctl enable docker

# 2. 下载项目代码
echo "📥 2. 下载项目代码..."
cd /opt

if [ -d "ppt_to_sketch" ]; then
    echo "📁 项目目录已存在，更新代码..."
    cd ppt_to_sketch
    git checkout production
    git pull origin production
else
    echo "📁 克隆项目代码..."
    git clone -b production https://github.com/MorningStar97/ppt_to_sketch.git
    cd ppt_to_sketch
fi

# 3. 创建 Dockerfile
echo "🐳 3. 创建 Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=ppt_to_sketch_service.settings_docker

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements_prod.txt .

RUN pip install --no-cache-dir -r requirements_prod.txt

COPY . .

RUN mkdir -p /app/media/uploads/ppt /app/media/outputs/sketch /app/staticfiles /app/logs

RUN chmod +x start.sh

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn_docker.conf.py", "ppt_to_sketch_service.wsgi:application"]
EOF

# 4. 创建 Gunicorn 配置
echo "⚙️ 4. 创建 Gunicorn 配置..."
cat > gunicorn_docker.conf.py << 'EOF'
bind = "0.0.0.0:8000"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
preload_app = True
EOF

# 5. 创建 Docker 专用设置
echo "🔧 5. 创建 Docker 专用配置..."
cat > ppt_to_sketch_service/settings_docker.py << 'EOF'
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['*']
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ppt_to_sketch',
        'USER': 'ppt_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'db',
        'PORT': '5432',
    }
}

REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'converter': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600
EOF

# 6. 创建 docker-compose.yml
echo "🐳 6. 创建 docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
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

  redis:
    image: redis:6-alpine
    restart: always
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  web:
    build: .
    restart: always
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
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
             gunicorn --config gunicorn_docker.conf.py ppt_to_sketch_service.wsgi:application"

volumes:
  postgres_data:
EOF

# 7. 生成密钥和密码
echo "🔐 7. 生成安全密钥..."
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# 8. 创建环境变量文件
echo "📝 8. 创建环境变量文件..."
cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DB_PASSWORD=${DB_PASSWORD}
EOF

echo "✅ 配置文件创建完成！"
echo "🔑 数据库密码: ${DB_PASSWORD}"
echo "🔑 Secret Key: ${SECRET_KEY}"

# 9. 构建和启动服务
echo "🚀 9. 构建和启动服务..."
docker-compose down 2>/dev/null || true
docker-compose up --build -d

# 10. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 11. 检查服务状态
echo "📊 11. 检查服务状态..."
docker-compose ps

# 12. 创建超级用户（交互式）
echo "👤 12. 创建管理员用户..."
echo "请输入管理员信息："
docker-compose exec -T web python manage.py shell --settings=ppt_to_sketch_service.settings_docker << 'EOF'
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ 创建管理员用户成功: admin/admin123')
else:
    print('ℹ️ 管理员用户已存在')
EOF

# 13. 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me || hostname -I | cut -d' ' -f1)

# 14. 显示部署结果
echo ""
echo "🎉 部署完成！"
echo "==============================================="
echo "🌐 访问地址："
echo "  - Web界面: http://${SERVER_IP}:8000"
echo "  - 管理后台: http://${SERVER_IP}:8000/admin"
echo "  - API接口: http://${SERVER_IP}:8000/api/tasks/"
echo ""
echo "👤 管理员账户："
echo "  - 用户名: admin"
echo "  - 密码: admin123"
echo ""
echo "🔧 管理命令："
echo "  - 查看状态: docker-compose ps"
echo "  - 查看日志: docker-compose logs -f web"
echo "  - 重启服务: docker-compose restart"
echo "  - 停止服务: docker-compose down"
echo ""
echo "📝 配置文件位置: /opt/ppt_to_sketch"
echo "🔑 环境变量文件: /opt/ppt_to_sketch/.env"
echo ""

# 15. 测试服务
echo "🧪 测试服务连接..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ 服务正常运行！"
else
    echo "⚠️ 服务可能还在启动中，请稍后测试"
    echo "💡 运行以下命令查看详细日志："
    echo "   cd /opt/ppt_to_sketch && docker-compose logs web"
fi

echo ""
echo "🎯 部署脚本执行完成！" 