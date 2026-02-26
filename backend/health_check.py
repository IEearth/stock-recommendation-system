"""
健康检查模块
- 检查系统各组件状态
- 检查数据完整性
- 生成健康报告
"""
import logging
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Stock, StockPrice, StockNews, Recommendation, SystemHealth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        """初始化"""
        self.db = None

    def connect_db(self):
        """连接数据库"""
        try:
            self.db = SessionLocal()
            self.db.execute("SELECT 1")  # 测试连接
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def check_database(self):
        """检查数据库状态"""
        try:
            results = {
                "status": "ok",
                "tables": {},
                "issues": []
            }

            # 检查各表的记录数
            results["tables"]["stocks"] = self.db.query(Stock).count()
            results["tables"]["stock_prices"] = self.db.query(StockPrice).count()
            results["tables"]["stock_news"] = self.db.query(StockNews).count()
            results["tables"]["recommendations"] = self.db.query(Recommendation).count()
            results["tables"]["system_health"] = self.db.query(SystemHealth).count()

            # 检查数据完整性
            if results["tables"]["stocks"] == 0:
                results["status"] = "warning"
                results["issues"].append("股票列表为空，需要初始化数据")

            if results["tables"]["stock_prices"] == 0:
                results["status"] = "warning"
                results["issues"].append("行情数据为空，需要采集数据")

            # 检查今日推荐
            today = datetime.now().strftime('%Y-%m-%d')
            today_recs = self.db.query(Recommendation).filter(
                Recommendation.recommend_date == today
            ).count()

            if today_recs == 0:
                results["status"] = "warning"
                results["issues"].append(f"今日({today})未生成推荐")
            else:
                results["today_recommendations"] = today_recs

            # 检查数据新鲜度
            latest_price = self.db.query(StockPrice).order_by(
                StockPrice.trade_date.desc()
            ).first()

            if latest_price:
                latest_date = datetime.strptime(latest_price.trade_date, '%Y%m%d')
                days_old = (datetime.now() - latest_date).days

                if days_old > 2:
                    results["status"] = "warning"
                    results["issues"].append(f"行情数据已过期 {days_old} 天")

                results["latest_price_date"] = latest_price.trade_date
            else:
                results["status"] = "warning"
                results["issues"].append("没有行情数据")

            return results

        except Exception as e:
            logger.error(f"数据库检查失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_system(self):
        """检查系统整体状态"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "overall": "healthy",
                "components": {}
            }

            # 数据库连接
            if not self.connect_db():
                status["overall"] = "critical"
                status["components"]["database"] = {
                    "status": "error",
                    "message": "无法连接数据库"
                }
                return status

            # 数据库
            status["components"]["database"] = self.check_database()
            if status["components"]["database"]["status"] != "ok":
                status["overall"] = "degraded"

            # 数据更新状态
            latest_health = self.db.query(SystemHealth).order_by(
                SystemHealth.check_time.desc()
            ).first()

            if latest_health:
                status["components"]["data_update"] = {
                    "status": latest_health.status,
                    "last_update": latest_health.data_update_time.isoformat() if latest_health.data_update_time else None,
                    "last_prediction": latest_health.last_prediction_time.isoformat() if latest_health.last_prediction_time else None
                }

                # 检查查新度
                if latest_health.data_update_time:
                    hours_old = (datetime.now() - latest_health.data_update_time).total_seconds() / 3600
                    if hours_old > 24:
                        status["overall"] = "degraded"
                        status["components"]["data_update"]["status"] = "warning"
                        status["components"]["data_update"]["message"] = f"数据已过期 {hours_old:.1f} 小时"
            else:
                status["overall"] = "degraded"
                status["components"]["data_update"] = {
                    "status": "warning",
                    "message": "没有数据更新记录"
                }

            return status

        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall": "critical",
                "error": str(e)
            }
        finally:
            if self.db:
                self.db.close()

    def record_health(self, status_data):
        """记录健康状态到数据库"""
        try:
            db = SessionLocal()

            health = SystemHealth(
                check_time=datetime.now(),
                status=status_data.get("overall", "unknown"),
                data_update_time=status_data.get("components", {}).get("data_update", {}).get("last_update"),
                last_prediction_time=status_data.get("components", {}).get("data_update", {}).get("last_prediction"),
                error_message=status_data.get("error")
            )
            db.add(health)
            db.commit()
            db.close()

            return True

        except Exception as e:
            logger.error(f"记录健康状态失败: {e}")
            return False

    def quick_check(self):
        """快速健康检查"""
        try:
            checker = HealthChecker()
            status = checker.check_system()
            checker.record_health(status)
            return status
        except Exception as e:
            logger.error(f"快速检查失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall": "critical",
                "error": str(e)
            }


if __name__ == "__main__":
    # 测试
    import json

    checker = HealthChecker()
    status = checker.check_system()

    print("=" * 50)
    print("系统健康检查报告")
    print("=" * 50)
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 记录到数据库
    checker.record_health(status)
