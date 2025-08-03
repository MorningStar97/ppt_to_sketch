#!/bin/bash

# 快速清理端口脚本
PORT=${1:-8000}

echo "检查端口 $PORT 的占用情况..."

if lsof -ti:$PORT > /dev/null 2>&1; then
    PID=$(lsof -ti:$PORT)
    echo "发现进程 $PID 正在占用端口 $PORT"
    
    # 查看进程详情
    echo "进程详情:"
    ps -p $PID
    
    echo ""
    read -p "确定要停止这个进程吗? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在停止进程 $PID..."
        kill $PID
        sleep 2
        
        # 检查是否成功停止
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo "进程仍在运行，强制停止..."
            kill -9 $PID
            sleep 1
        fi
        
        # 最终检查
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo "❌ 无法停止进程"
        else
            echo "✅ 端口 $PORT 已释放"
        fi
    else
        echo "操作已取消"
    fi
else
    echo "✅ 端口 $PORT 未被占用"
fi 