"""
定时任务调度器（优化版 - 支持交易日感知）
- 使用上下文管理器管理数据库会话
- 改进错误处理
- 添加交易日检查
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
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
    """任务调度器（优化版 - 支持交易日感知）"""

    def __init__(self):
        """初始化"""
        self.market_collector = None
        self.news_collector = None
        self.recommender = None
        self._initialized = False

        # 导入交易日检查器
        try:
            from utils.trading_day_checker import get_trading_day_checker
            self.trading_checker = get_trading_day_checker()
            logger.info("✅ 交易日检查器已启用")
        except ImportError:
            logger.warning("⚠️ 交易日检查器未找到")
            self.trading_checker = None

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

    def is_trading_day(self) -> bool:
        """判断今天是否为交易日"""
        if self.trading_checker is None:
            return True
        return self.trading_checker.is_trading_day()

    def get_next_trading_day(self) -> datetime:
        """获取下一个交易日"""
        if self.trading_checker is None:
            return datetime.now() + timedelta(days=1)
        return self.trading_checker.get_next_trading_day()

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
        """更新新闻数据任务（每天执行）"""
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
        """训练预测模型任务（仅交易日执行）"""
        task_start = datetime.now()

        # 检查是否为交易日
        if not self.is_trading_day():
            next_trading = self.get_next_trading_day()
            logger.info(f"⏭️  非交易日，跳过模型训练。下一个交易日: {next_trading.strftime('%Y-%m-%d')}")
            return

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

    async def generate_recommendations_task(self, top_n: int = 10, min_price: float = 0, max_price: float = 15, force: bool = False):
        """
        生成推荐任务（仅交易日执行）

        Args:
            top_n: 推荐数量
            min_price: 最低股价
            max_price: 最高股价
            force: 强制执行（忽略交易日检查）
        """
        task_start = datetime.now()

        # 检查是否为交易日
        if not force and not self.is_trading_day():
            next_trading = self.get_next_trading_day()
            logger.info(f"⏭️  非交易日，跳过推荐生成。下一个交易日: {next_trading.strftime('%Y-%m-%d')}")
            return

        try:
            logger.info("💡 开始生成推荐...")
            self._ensure_initialized()
            
            recs = self.recommender.generate_recommendations(
                top_n=top_n, 
                min_price=min_price, 
                max_price=max_price,
                force=force
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
        """完整数据更新任务（仅交易日执行）"""
        # 检查是否为交易日
        if not self.is_trading_day():
            next_trading = self.get_next_trading_day()
            logger.info(f"⏭️  非交易日，跳过完整数据更新。下一个交易日: {next_trading.strftime('%Y-%m-%d')}")
            return

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

                # 如果是交易日但无推荐，标记为警告
                if self.is_trading_day() and rec_count == 0:
                    status = "warning"
                    if not error_message:
                        error_message = "今日(交易日)未生成推荐"

                health = SystemHealth(
                    check_time=datetime.now(),
                    status=status,
                    data_update_time=latest_health.data_update_time if latest_health else None,
                    last_prediction_time=latest_health.last_prediction_time if latest_health else None,
                    error_message=error_message
                )
                db.add(health)
                db.commit()
            
            trading_day_status = "交易日" if self.is_trading_day() else "非交易日"
            logger.info(f"✅ 健康检查完成: 状态={status}, {trading_day_status}, 今日推荐={rec_count}条")
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")

    def schedule_next_trading_day_job(self):
        """调度下一个交易日的任务"""
        next_trading = self.get_next_trading_day()

        # 添加下一个交易日的推荐任务
        scheduler.add_job(
            self.generate_recommendations_task,
            trigger=DateTrigger(run_date=next_trading.replace(hour=9, minute=30)),
            id=f'next_trading_recommend_{next_trading.strftime("%Y%m%d")}',
            name=f'下一个交易日推荐 ({next_trading.strftime("%Y-%m-%d")})',
            replace_existing=True
        )

        logger.info(f"✅ 已调度下一个交易日 ({next_trading.strftime('%Y-%m-%d')}) 的推荐任务 (09:30)")

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

        # 每天早上9:30检查是否为交易日，如果是则执行完整更新
        scheduler.add_job(
            self.full_data_update,
            trigger=CronTrigger(hour=9, minute=30, timezone='Asia/Shanghai'),
            id='daily_trading_update',
            name='每日交易日数据更新 (09:30)',
            replace_existing=True
        )

        # 每天凌晨2点更新新闻（不需要交易日限制）
        scheduler.add_job(
            self.update_news_task,
            trigger=CronTrigger(hour=2, minute=0, timezone='Asia/Shanghai'),
            id='daily_news_update',
            name='每日新闻更新 (02:00)',
            replace_existing=True
        )

        # 启动调度器
        scheduler.start()

        logger.info("⏰ 定时任务已启动:")
        logger.info("   - 健康检查: 每20分钟")
        logger.info("   - 每日交易日数据更新: 每天 09:30 (仅交易日)")
        logger.info("   - 每日新闻更新: 每天 02:00")

        # 显示下一个交易日
        next_trading = self.get_next_trading_day()
        logger.info(f"   - 下一个交易日: {next_trading.strftime('%Y-%m-%d')}")


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
