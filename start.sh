#!/bin/bash

echo "==================================="
echo "PPT 转 Sketch 服务启动脚本"
echo "==================================="

# 检查 Python3 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 请先安装 Python3"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖包..."
python3 -c "import django, pptx, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装依赖包..."
    python3 -m pip install -r requirements.txt
fi

# 检查数据库是否需要迁移
echo "检查数据库..."
if [ ! -f "db.sqlite3" ]; then
    echo "执行数据库迁移..."
    python3 manage.py makemigrations
    python3 manage.py migrate
    
    echo "创建管理员账户..."
    python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('管理员账户已创建: admin / admin123')
else:
    print('管理员账户已存在')
"
fi

# 检查端口占用情况
PORT=${1:-8000}  # 默认端口 8000，可通过参数指定其他端口
echo "检查端口 $PORT 是否被占用..."

if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "警告: 端口 $PORT 已被占用"
    PID=$(lsof -ti:$PORT)
    echo "占用进程 PID: $PID"
    
    read -p "是否要停止占用端口的进程? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在停止进程 $PID..."
        kill $PID
        sleep 2
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo "强制停止进程..."
            kill -9 $PID
        fi
        echo "进程已停止"
    else
        echo "请使用其他端口，例如: ./start.sh 8001"
        exit 1
    fi
fi

echo ""
echo "==================================="
echo "服务启动中..."
echo "==================================="
echo "访问地址："
echo "- 前端界面: http://127.0.0.1:$PORT/"
echo "- 管理后台: http://127.0.0.1:$PORT/admin/"
echo "- 管理员账户: admin / admin123"
echo "==================================="
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务器
if [ $PORT -eq 8000 ]; then
    python3 manage.py runserver
else
    python3 manage.py runserver 127.0.0.1:$PORT
fi 