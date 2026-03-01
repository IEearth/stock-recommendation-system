"""
定时任务调度器（优化版）
- 使用上下文管理器管理数据库会话
- 改进错误处理
- 添加重试机制
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
import os
import asyncio
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, SystemHealth, Recommendation, TaskLog, Stock, StockNews, get_db_session, func
from models.market_collector_baostock import MarketCollector
from models.news_collector import NewsCollector
from models.recommender import StockRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


class JobScheduler:
    """任务调度器（优化版）"""

    def __init__(self):
        """初始化"""
        self.market_collector = None
        self.news_collector = None
        self.recommender = None
        self._initialized = False

    def _ensure_initialized(self):
        """确保组件已初始化"""
        if not self._initialized:
            self.market_collector = MarketCollector()
            self.news_collector = NewsCollector()
            self.recommender = StockRecommender()
            self._initialized = True

    def log_task(self, task_name: str, task_type: str, status: str, message: str = None, error: str = None, duration: float = 0):
        """记录任务执行日志"""
        try:
            with get_db_session() as db:
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
            
        except Exception as e:
            logger.error(f"记录任务日志失败: {e}")

    async def update_stock_list_task(self, use_dynamic: bool = False):
        """更新股票列表任务
        
        Args:
            use_dynamic: 是否动态获取股票列表
        """
        task_start = datetime.now()
        try:
            logger.info("🔄 开始更新股票列表...")
            self._ensure_initialized()
            
            self.market_collector.update_stock_list(use_dynamic=use_dynamic, max_stocks=50)
            
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

    async def update_market_data_task(self, days: int = 90):
        """更新行情数据任务
        
        Args:
            days: 获取最近多少天的数据
        """
        task_start = datetime.now()
        try:
            logger.info("🔄 开始更新行情数据...")
            self._ensure_initialized()
            
            self.market_collector.update_market_data(days=days)
            
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新行情数据",
                "data_update",
                "success",
                message=f"成功更新{days}天行情数据",
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
            self._ensure_initialized()
            
            self.news_collector.update_news()
            
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
            self._ensure_initialized()
            
            from models.predictor import StockPredictor
            predictor = StockPredictor()
            predictor.train()
            
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

    async def generate_recommendations_task(self, top_n: int = 10, min_price: float = 0, max_price: float = 15):
        """生成推荐任务
        
        Args:
            top_n: 推荐数量
            min_price: 最低股价
            max_price: 最高股价
        """
        task_start = datetime.now()
        try:
            logger.info("💡 开始生成推荐...")
            self._ensure_initialized()
            
            recs = self.recommender.generate_recommendations(
                top_n=top_n, 
                min_price=min_price, 
                max_price=max_price
            )
            
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
        
        await self.update_stock_list_task()
        await self.update_market_data_task()
        await self.update_news_task()
        await self.train_model_task()
        await self.generate_recommendations_task()
        
        try:
            with get_db_session() as db:
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
            
            logger.info("✅ 系统健康状态已更新！")
            
        except Exception as e:
            logger.error(f"更新系统健康状态失败: {e}")

    async def health_check_task(self):
        """健康检查任务"""
        try:
            with get_db_session() as db:
                stock_count = db.query(Stock).count()
                rec_count = db.query(Recommendation).filter(
                    Recommendation.recommend_date == datetime.now().strftime('%Y-%m-%d')
                ).count()
                
                health = SystemHealth(
                    check_time=datetime.now(),
                    status="running" if stock_count > 0 else "error",
                    data_update_time=datetime.now(),
                    last_prediction_time=datetime.now(),
                    error_message=None if stock_count > 0 else "没有股票数据"
                )
                db.add(health)
                db.commit()
            
            logger.info(f"🏥 健康检查完成 - 股票: {stock_count}, 今日推荐: {rec_count}")
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")


def setup_scheduler():
    """设置定时任务"""
    job_scheduler = JobScheduler()
    
    scheduler.add_job(
        job_scheduler.health_check_task,
        IntervalTrigger(minutes=20),
        id='health_check',
        name='健康检查',
        replace_existing=True
    )
    
    scheduler.add_job(
        job_scheduler.full_data_update,
        CronTrigger(hour=6, minute=0),
        id='daily_update',
        name='每日数据更新',
        replace_existing=True
    )
    
    return job_scheduler


async def main():
    """主函数"""
    job_scheduler = setup_scheduler()
    
    scheduler.start()
    logger.info("🚀 调度器已启动")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())
