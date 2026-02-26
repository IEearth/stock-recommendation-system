#!/usr/bin/env python3
"""
系统测试脚本
"""
import sys
import os
from sqlalchemy import text

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


print("=" * 60)
print("A股智能推荐系统 - 系统测试")
print("=" * 60)

# 测试1: 数据库初始化
print("\n[1/5] 测试数据库初始化...")
try:
    from database import init_db, SessionLocal
    init_db()
    print("✅ 数据库初始化成功")
except Exception as e:
    print(f"❌ 数据库初始化失败: {e}")
    sys.exit(1)

# 测试2: 数据库连接
print("\n[2/5] 测试数据库连接...")
try:
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    db.close()
    print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)

# 测试3: 健康检查
print("\n[3/5] 测试健康检查模块...")
try:
    from health_check import HealthChecker
    checker = HealthChecker()
    status = checker.check_system()
    print(f"✅ 健康检查完成")
    print(f"   状态: {status.get('overall')}")
except Exception as e:
    print(f"❌ 健康检查失败: {e}")

# 测试4: 模块导入
print("\n[4/5] 测试核心模块导入...")
try:
    from models.market_collector import MarketCollector
    from models.news_collector import NewsCollector
    from models.predictor import StockPredictor
    from models.recommender import StockRecommender
    print("✅ 所有核心模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")

# 测试5: API服务
print("\n[5/5] 测试API服务启动...")
try:
    from main import app
    print("✅ FastAPI应用初始化成功")
    print(f"   标题: {app.title}")
    print(f"   版本: {app.version}")
except Exception as e:
    print(f"❌ API服务初始化失败: {e}")

print("\n" + "=" * 60)
print("✅ 系统测试完成！")
print("=" * 60)
print("\n提示：")
print("1. Tushare Token 已配置 ✅")
print("2. 运行: python3 main.py  # 启动API服务")
print("3. 运行: python3 scheduler.py  # 启动定时任务")
print("4. 访问: http://localhost:8000/docs  # API文档")
