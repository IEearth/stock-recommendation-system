#!/usr/bin/env python
"""
启动脚本：使用新的数据库驱动的任务调度器
"""
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler_db import JobScheduler


async def run():
    """运行调度器"""
    print("🚀 启动股票推荐系统（任务调度器 v2.0）...")

    scheduler_app = JobScheduler()
    scheduler_app.start()

    print("✅ 系统已启动，任务调度器运行中...")

    # 保持运行
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹ 接收到停止信号...")
        scheduler_app.stop()
        print("✅ 系统已停止")


if __name__ == "__main__":
    asyncio.run(run())
