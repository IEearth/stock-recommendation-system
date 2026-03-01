"""
手动运行所有任务生成数据（优化版）
"""
import asyncio
import logging
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import JobScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("🚀 开始执行所有任务...")

    scheduler = JobScheduler()

    logger.info("\n" + "="*60)
    logger.info("1. 更新股票列表...")
    await scheduler.update_stock_list_task(use_dynamic=False)

    logger.info("\n" + "="*60)
    logger.info("2. 更新行情数据（90天）...")
    await scheduler.update_market_data_task(days=90)

    logger.info("\n" + "="*60)
    logger.info("3. 更新新闻数据...")
    await scheduler.update_news_task()

    logger.info("\n" + "="*60)
    logger.info("4. 训练预测模型...")
    await scheduler.train_model_task()

    logger.info("\n" + "="*60)
    logger.info("5. 生成推荐...")
    await scheduler.generate_recommendations_task(top_n=10, min_price=0, max_price=15)

    logger.info("\n" + "="*60)
    logger.info("✅ 所有任务执行完成！")


if __name__ == "__main__":
    asyncio.run(main())
