"""
定时任务调度器
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, SystemHealth, Recommendation
from models.market_collector import MarketCollector
from models.news_collector import NewsCollector
from models.recommender import StockRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler()


class JobScheduler:
    """任务调度器"""

    def __init__(self):
        """初始化"""
        self.market_collector = MarketCollector()
        self.news_collector = NewsCollector()
        self.recommender = StockRecommender()

    async def update_data(self):
        """更新数据任务"""
        logger.info("🔄 开始更新数据...")
        try:
            db = SessionLocal()

            # 更新股票列表
            logger.info("1️⃣ 更新股票列表...")
            self.market_collector.update_stock_list(db)

            # 更新行情数据
            logger.info("2️⃣ 更新行情数据...")
            self.market_collector.update_daily_quotes(days=30, db_session=db)

            # 更新新闻
            logger.info("3️⃣ 更新新闻数据...")
            self.news_collector.update_news(db_session=db)

            # 训练模型
            logger.info("4️⃣ 训练预测模型...")
            from models.predictor import StockPredictor
            predictor = StockPredictor()
            predictor.train(db_session=db)

            # 生成推荐
            logger.info("5️⃣ 生成今日推荐...")
            self.recommender.generate_recommendations(top_n=10, db_session=db)

            # 记录数据更新时间
            health = SystemHealth(
                check_time=datetime.now(),
                status="running",
                data_update_time=datetime.now(),
                last_prediction_time=datetime.now()
            )
            db.add(health)
            db.commit()
            db.close()

            logger.info("✅ 数据更新完成！")

        except Exception as e:
            logger.error(f"❌ 更新数据失败: {e}")
            import traceback
            traceback.print_exc()

    async def health_check(self):
        """健康检查任务"""
        logger.info("🏥 执行健康检查...")
        try:
            db = SessionLocal()

            # 检查是否有今日推荐
            from datetime import datetime as dt
            today = dt.now().strftime('%Y-%m-%d')
            today_recs = db.query(Recommendation).filter(
                Recommendation.recommend_date == today
            ).count()

            # 检查数据更新状态
            latest_health = db.query(SystemHealth).order_by(
                SystemHealth.check_time.desc()
            ).first()

            status = "running"
            error_message = None

            if latest_health:
                # 检查数据是否过期（超过24小时）
                if latest_health.data_update_time:
                    hours_since_update = (dt.now() - latest_health.data_update_time).total_seconds() / 3600
                    if hours_since_update > 24:
                        status = "warning"
                        error_message = f"数据已过期 {hours_since_update:.1f} 小时"
            else:
                status = "warning"
                error_message = "没有历史健康检查记录"

            if today_recs == 0:
                status = "warning"
                error_message = error_message or "今日未生成推荐"

            # 记录健康检查
            health = SystemHealth(
                check_time=dt.now(),
                status=status,
                data_update_time=latest_health.data_update_time if latest_health else None,
                last_prediction_time=latest_health.last_prediction_time if latest_health else None,
                error_message=error_message
            )
            db.add(health)
            db.commit()
            db.close()

            logger.info(f"✅ 健康检查完成: 状态={status}, 今日推荐={today_recs}条")

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """启动调度器"""
        logger.info("🚀 启动定时任务调度器...")

        # 每20分钟健康检查
        scheduler.add_job(
            self.health_check,
            trigger=IntervalTrigger(minutes=20),
            id='health_check',
            name='健康检查',
            replace_existing=True
        )

        # 每天凌晨2点更新数据
        scheduler.add_job(
            self.update_data,
            trigger='cron',
            hour=2,
            minute=0,
            id='data_update',
            name='数据更新',
            replace_existing=True
        )

        # 启动调度器
        scheduler.start()
        logger.info("⏰ 定时任务已启动:")
        logger.info("   - 健康检查: 每20分钟")
        logger.info("   - 数据更新: 每天 02:00")

    def stop(self):
        """停止调度器"""
        logger.info("⏹ 停止调度器...")
        scheduler.shutdown()
        logger.info("✅ 调度器已停止")


if __name__ == "__main__":
    # 测试
    import asyncio

    scheduler_app = JobScheduler()

    async def test():
        """测试任务"""
        # 先更新一次数据
        await scheduler_app.update_data()

        # 然后启动调度器
        scheduler_app.start()

        # 保持运行
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            scheduler_app.stop()

    asyncio.run(test())
