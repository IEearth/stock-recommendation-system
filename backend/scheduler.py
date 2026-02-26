"""
定时任务调度器（增强版）
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, SystemHealth, Recommendation, TaskLog, Stock, StockNews
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

    def log_task(self, task_name, task_type, status, message=None, error=None, duration=0):
        """记录任务执行日志"""
        try:
            db = SessionLocal()
            
            task_log = TaskLog(
                task_name=task_name,
                task_type=task_type,
                status=status,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=duration,
                message=message,
                error=error
            )
            db.add(task_log)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"记录任务日志失败: {e}")

    async def update_stock_list_task(self):
        """更新股票列表任务"""
        task_start = datetime.now()
        try:
            logger.info("🔄 开始更新股票列表...")
            
            db = SessionLocal()
            self.market_collector.update_stock_list(db_session=db)
            db.close()
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新股票列表",
                "data_update",
                "success",
                message=f"成功更新股票列表",
                duration=duration
            )
            logger.info("✅ 股票列表更新完成！")
            
        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新股票列表",
                "data_update",
                "failed",
                message=f"更新失败",
                error=str(e),
                duration=duration
            )
            logger.error(f"❌ 更新股票列表失败: {e}")

    async def update_market_data_task(self):
        """更新行情数据任务"""
        task_start = datetime.now()
        try:
            logger.info("🔄 开始更新行情数据...")
            
            db = SessionLocal()
            self.market_collector.update_daily_quotes(days=30, db_session=db)
            db.close()
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新行情数据",
                "data_update",
                "success",
                message=f"成功更新30天行情数据",
                duration=duration
            )
            logger.info("✅ 行情数据更新完成！")
            
        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新行情数据",
                "data_update",
                "failed",
                message=f"更新失败",
                error=str(e),
                duration=duration
            )
            logger.error(f"❌ 更新行情数据失败: {e}")

    async def update_news_task(self):
        """更新新闻数据任务"""
        task_start = datetime.now()
        try:
            logger.info("🔄 开始更新新闻数据...")
            
            db = SessionLocal()
            self.news_collector.update_news(db_session=db)
            db.close()
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新新闻数据",
                "data_update",
                "success",
                message=f"成功更新新闻数据",
                duration=duration
            )
            logger.info("✅ 新闻数据更新完成！")
            
        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新新闻数据",
                "data_update",
                "failed",
                message=f"更新失败",
                error=str(e),
                duration=duration
            )
            logger.error(f"❌ 更新新闻数据失败: {e}")

    async def train_model_task(self):
        """训练预测模型任务"""
        task_start = datetime.now()
        try:
            logger.info("🧠 开始训练预测模型...")
            
            from models.predictor import StockPredictor
            db = SessionLocal()
            predictor = StockPredictor()
            predictor.train(db_session=db)
            db.close()
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "训练预测模型",
                "data_update",
                "success",
                message=f"成功训练预测模型",
                duration=duration
            )
            logger.info("✅ 预测模型训练完成！")
            
        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "训练预测模型",
                "data_update",
                "failed",
                message=f"训练失败",
                error=str(e),
                duration=duration
            )
            logger.error(f"❌ 训练预测模型失败: {e}")

    async def generate_recommendations_task(self):
        """生成推荐任务"""
        task_start = datetime.now()
        try:
            logger.info("💡 开始生成推荐...")
            
            db = SessionLocal()
            recs = self.recommender.generate_recommendations(top_n=10, db_session=db)
            db.close()
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "生成推荐",
                "data_update",
                "success",
                message=f"成功生成 {len(recs)} 个推荐",
                duration=duration
            )
            logger.info(f"✅ 推荐生成完成: {len(recs)} 个！")
            
        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "生成推荐",
                "data_update",
                "failed",
                message=f"生成失败",
                error=str(e),
                duration=duration
            )
            logger.error(f"❌ 生成推荐失败: {e}")

    async def full_data_update(self):
        """完整数据更新任务"""
        logger.info("🔄 开始完整数据更新...")
        
        # 按顺序执行
        await self.update_stock_list_task()
        await self.update_market_data_task()
        await self.update_news_task()
        await self.train_model_task()
        await self.generate_recommendations_task()
        
        # 更新系统健康状态
        try:
            db = SessionLocal()
            
            latest_rec = db.query(func.max(Recommendation.created_at)).scalar()
            
            health = SystemHealth(
                check_time=datetime.now(),
                status="running",
                data_update_time=datetime.now(),
                last_prediction_time=latest_rec,
                error_message=None
            )
            db.add(health)
            db.commit()
            db.close()
            
            logger.info("✅ 系统健康状态已更新！")
            
        except Exception as e:
            logger.error(f"更新系统健康状态失败: {e}")

    async def health_check_task(self):
        """健康检查任务"""
        logger.info("🏥 执行健康检查...")
        try:
            from sqlalchemy import func
            from datetime import timedelta
            
            db = SessionLocal()
            
            # 检查今日推荐
            today = datetime.now().strftime('%Y-%m-%d')
            today_recs = db.query(Recommendation).filter(
                Recommendation.recommend_date == today
            ).count()
            
            # 检查数据更新状态
            latest_health = db.query(SystemHealth).order_by(
                SystemHealth.check_time.desc()
            ).first()
            
            status = "running"
            error_message = None
            
            if latest_health and latest_health.data_update_time:
                hours_since_update = (datetime.now() - latest_health.data_update_time).total_seconds() / 3600
                if hours_since_update > 24:
                    status = "warning"
                    error_message = f"数据已过期 {hours_since_update:.1f} 小时"
            else:
                status = "warning"
                error_message = "没有历史健康检查记录"
            
            if today_recs == 0:
                status = "warning"
                if not error_message:
                    error_message = "今日未生成推荐"
            
            # 记录健康检查
            health = SystemHealth(
                check_time=datetime.now(),
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

    def start(self):
        """启动调度器"""
        logger.info("🚀 启动定时任务调度器...")
        
        # 每20分钟健康检查
        scheduler.add_job(
            self.health_check_task,
            trigger=IntervalTrigger(minutes=20, timezone='UTC'),
            id='health_check',
            name='健康检查',
            replace_existing=True
        )
        
        # 每天凌晨2点完整数据更新
        scheduler.add_job(
            self.full_data_update,
            trigger=CronTrigger(hour=2, minute=0, timezone='Asia/Shanghai'),
            id='full_data_update',
            name='完整数据更新',
            replace_existing=True
        )
        
        # 每小时更新新闻
        scheduler.add_job(
            self.update_news_task,
            trigger=IntervalTrigger(hours=1, timezone='Asia/Shanghai'),
            id='update_news',
            name='更新新闻',
            replace_existing=True
        )
        
        # 启动调度器
        scheduler.start()
        logger.info("⏰ 定时任务已启动:")
        logger.info("   - 健康检查: 每20分钟")
        logger.info("   - 更新新闻: 每1小时")
        logger.info("   - 完整数据更新: 每天 02:00")

    def stop(self):
        """停止调度器"""
        logger.info("⏹ 停止调度器...")
        scheduler.shutdown()
        logger.info("✅ 调度器已停止")


if __name__ == "__main__":
    import asyncio
    
    scheduler_app = JobScheduler()
    
    async def run():
        """运行调度器"""
        scheduler_app.start()
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            scheduler_app.stop()
    
    asyncio.run(run())
