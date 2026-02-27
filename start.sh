#!/bin/bash
# 股票推荐系统启动脚本

cd /root/stock-recommendation-system

# 停止旧进程
pkill -f "uvicorn backend.main:app"

sleep 2

# 启动新进程
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

sleep 3

# 检查启动状态
if ps aux | grep -v grep | grep "uvicorn backend.main:app" > /dev/null; then
    echo "✅ 服务启动成功！"
    echo "访问地址: http://118.89.54.140:8000"
    echo "或内网地址: http://10.1.12.4:8000"
else
    echo "❌ 服务启动失败！"
    tail -20 logs/api.log
fi
