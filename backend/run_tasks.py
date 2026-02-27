"""
手动运行所有任务生成数据
"""
import asyncio
import logging
from datetime import datetime
from scheduler import JobScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("🚀 开始执行所有任务...")

    scheduler = JobScheduler()

    # 1. 更新股票列表
    logger.info("\n" + "="*60)
    await scheduler.update_stock_list_task()

    # 2. 更新行情数据
    logger.info("\n" + "="*60)
    await scheduler.update_market_data_task()

    # 3. 更新新闻数据
    logger.info("\n" + "="*60)
    await scheduler.update_news_task()

    # 4. 训练预测模型
    logger.info("\n" + "="*60)
    await scheduler.train_model_task()

    # 5. 生成推荐
    logger.info("\n" + "="*60)
    await scheduler.generate_recommendations_task()

    logger.info("\n" + "="*60)
    logger.info("✅ 所有任务执行完成！")


if __name__ == "__main__":
    asyncio.run(main())
