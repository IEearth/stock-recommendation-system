"""
数据库迁移脚本：初始化任务配置表
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, TaskConfig, init_db
from datetime import datetime


def migrate_task_configs():
    """迁移任务配置到数据库"""
    print("🔄 开始迁移任务配置...")

    # 初始化数据库
    init_db()

    db = SessionLocal()

    # 默认任务配置
    default_configs = [
        {
            'task_name': 'health_check',
            'task_type': 'health_check',
            'is_enabled': True,
            'interval_seconds': 1200,  # 20分钟
            'description': '系统健康检查'
        },
        {
            'task_name': 'update_news',
            'task_type': 'data_fetch',
            'is_enabled': True,
            'interval_seconds': 3600,  # 1小时
            'description': '更新新闻数据'
        },
        {
            'task_name': 'full_data_update',
            'task_type': 'daily_update',
            'is_enabled': True,
            'cron_expression': '0 2 * * *',  # 每天凌晨2点
            'description': '完整数据更新（每日）'
        },
        {
            'task_name': 'update_stock_list',
            'task_type': 'data_fetch',
            'is_enabled': False,
            'interval_seconds': 86400,  # 每天
            'description': '更新股票列表'
        },
        {
            'task_name': 'update_market_data',
            'task_type': 'data_fetch',
            'is_enabled': False,
            'interval_seconds': 3600,  # 每小时
            'description': '更新行情数据'
        },
        {
            'task_name': 'train_model',
            'task_type': 'daily_update',
            'is_enabled': False,
            'interval_seconds': 86400,  # 每天
            'description': '训练预测模型'
        },
        {
            'task_name': 'generate_recommendations',
            'task_type': 'recommendation',
            'is_enabled': False,
            'interval_seconds': 86400,  # 每天
            'description': '生成推荐'
        }
    ]

    created_count = 0
    skipped_count = 0

    for config in default_configs:
        task_name = config['task_name']
        existing = db.query(TaskConfig).filter(TaskConfig.task_name == task_name).first()

        if existing:
            print(f"  ⏭️  任务配置已存在: {task_name}")
            skipped_count += 1
        else:
            task_config = TaskConfig(**config)
            db.add(task_config)
            print(f"  ✅ 创建任务配置: {task_name}")
            created_count += 1

    try:
        db.commit()
        db.close()
        print(f"\n✅ 迁移完成！")
        print(f"   新建: {created_count}")
        print(f"   跳过: {skipped_count}")
    except Exception as e:
        db.rollback()
        db.close()
        print(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    migrate_task_configs()
