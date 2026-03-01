"""
定时任务调度器（支持数据库配置）
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, SystemHealth, Recommendation, TaskLog, TaskConfig
from models.market_collector_baostock import MarketCollector
from models.news_collector import NewsCollector
from models.recommender import StockRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler()


class JobScheduler:
    """任务调度器（支持数据库配置）"""

    def __init__(self):
        """初始化"""
        self.market_collector = MarketCollector()
        self.news_collector = NewsCollector()
        self.recommender = StockRecommender()
        self.task_functions = {
            'update_stock_list': self.update_stock_list_task,
            'update_market_data': self.update_market_data_task,
            'update_news': self.update_news_task,
            'train_model': self.train_model_task,
            'generate_recommendations': self.generate_recommendations_task,
            'full_data_update': self.full_data_update,
            'health_check': self.health_check_task
        }

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

            # 更新任务配置的最后执行时间
            task_config = db.query(TaskConfig).filter(TaskConfig.task_name == task_name).first()
            if task_config:
                task_config.last_run_time = datetime.now()
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
            self.market_collector.update_market_data(days=90, db_session=db)
            db.close()

            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "更新行情数据",
                "data_update",
                "success",
                message=f"成功更新90天行情数据",
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
                "recommendation",
                "success",
                message=f"成功生成 {len(recs)} 个推荐",
                duration=duration
            )
            logger.info(f"✅ 推荐生成完成: {len(recs)} 个！")

        except Exception as e:
            duration = (datetime.now() - task_start).total_seconds()
            self.log_task(
                "生成推荐",
                "recommendation",
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
            from sqlalchemy import func
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

    def ensure_default_task_configs(self):
        """确保存在默认的任务配置"""
        db = SessionLocal()

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
            }
        ]

        for config in default_configs:
            existing = db.query(TaskConfig).filter(TaskConfig.task_name == config['task_name']).first()
            if not existing:
                task_config = TaskConfig(**config)
                db.add(task_config)
                logger.info(f"✅ 创建默认任务配置: {config['task_name']}")

        db.commit()
        db.close()

    def load_and_schedule_tasks(self):
        """从数据库加载任务配置并调度"""
        db = SessionLocal()

        # 清除所有现有任务
        scheduler.remove_all_jobs()

        # 加载启用的任务配置
        task_configs = db.query(TaskConfig).filter(TaskConfig.is_enabled == True).all()

        for config in task_configs:
            try:
                # 根据任务名称查找对应的执行函数
                task_func = self.task_functions.get(config.task_name)

                if not task_func:
                    logger.warning(f"⚠️  未找到任务函数: {config.task_name}")
                    continue

                # 根据配置创建触发器
                trigger = None
                if config.cron_expression:
                    # 使用 Cron 表达式
                    parts = config.cron_expression.split()
                    if len(parts) >= 5:
                        minute, hour, day, month, day_of_week = parts[:5]
                        trigger = CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=day_of_week,
                            timezone='Asia/Shanghai'
                        )
                        logger.info(f"  - {config.task_name}: Cron({config.cron_expression})")
                elif config.interval_seconds:
                    # 使用间隔
                    trigger = IntervalTrigger(
                        seconds=config.interval_seconds,
                        timezone='Asia/Shanghai'
                    )
                    logger.info(f"  - {config.task_name}: 每{config.interval_seconds}秒")
                else:
                    logger.warning(f"⚠️  任务 {config.task_name} 没有配置触发器")
                    continue

                # 添加任务
                scheduler.add_job(
                    task_func,
                    trigger=trigger,
                    id=config.task_name,
                    name=config.description or config.task_name,
                    replace_existing=True
                )

            except Exception as e:
                logger.error(f"❌ 加载任务 {config.task_name} 失败: {e}")

        db.close()

    def start(self):
        """启动调度器"""
        logger.info("🚀 启动定时任务调度器...")

        # 确保存在默认任务配置
        self.ensure_default_task_configs()

        # 从数据库加载任务配置
        self.load_and_schedule_tasks()

        # 启动调度器
        scheduler.start()
        logger.info("✅ 定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        logger.info("⏹ 停止调度器...")
        scheduler.shutdown()
        logger.info("✅ 调度器已停止")

    def reload_tasks(self):
        """重新加载任务配置（热更新）"""
        logger.info("🔄 重新加载任务配置...")
        self.load_and_schedule_tasks()
        logger.info("✅ 任务配置已重新加载")


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
