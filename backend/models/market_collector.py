"""
市场行情数据采集
"""
import tushare as ts
import pandas as pd
import logging
from datetime import datetime, timedelta
import sys
import os

# 添加父目录到路径，以便导入 database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Stock, StockPrice, SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketCollector:
    """行情数据采集器"""

    def __init__(self, tushare_token=None):
        """初始化

        Args:
            tushare_token: Tushare Pro API Token
        """
        self.token = tushare_token or os.getenv("TUSHARE_TOKEN", "")
        if not self.token:
            raise ValueError("TUSHARE_TOKEN 未设置！")

        ts.set_token(self.token)
        self.pro = ts.pro_api()

    def fetch_stock_list(self):
        """获取股票列表"""
        try:
            logger.info("开始获取股票列表...")
            # 获取A股列表
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,name,industry,market'
            )
            logger.info(f"获取到 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    def fetch_daily_quotes(self, ts_code=None, start_date=None, end_date=None):
        """获取日线行情

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            logger.info(f"获取行情数据: {ts_code} from {start_date} to {end_date}")

            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            logger.error(f"获取行情数据失败: {e}")
            raise

    def update_stock_list(self, db_session=None):
        """更新股票列表到数据库"""
        try:
            df = self.fetch_stock_list()

            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            # 清空并重新插入
            db.query(Stock).delete()

            for _, row in df.iterrows():
                stock = Stock(
                    ts_code=row['ts_code'],
                    name=row['name'],
                    industry=row.get('industry', ''),
                    market=row.get('market', '')
                )
                db.add(stock)

            db.commit()
            logger.info(f"股票列表更新完成: {len(df)} 只")

            if db_session is None:
                db.close()

        except Exception as e:
            logger.error(f"更新股票列表失败: {e}")
            if db_session is None and 'db' in locals():
                db.rollback()
                db.close()
            raise

    def update_daily_quotes(self, days=30, db_session=None):
        """更新最近N天的行情数据

        Args:
            days: 获取最近多少天的数据
            db_session: 数据库会话
        """
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # 获取所有股票
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            stocks = db.query(Stock).limit(100).all()  # 限制数量以避免API限制

            logger.info(f"开始更新 {len(stocks)} 只股票的行情数据...")

            for i, stock in enumerate(stocks):
                try:
                    df = self.fetch_daily_quotes(
                        ts_code=stock.ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    # 保存到数据库
                    for _, row in df.iterrows():
                        price = StockPrice(
                            ts_code=row['ts_code'],
                            trade_date=row['trade_date'],
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            vol=row['vol'],
                            amount=row['amount'],
                            pct_chg=row['pct_chg']
                        )
                        db.add(price)

                    logger.info(f"[{i+1}/{len(stocks)}] {stock.ts_code}: {len(df)} 条数据")

                    # 避免API限制
                    import time
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"获取 {stock.ts_code} 数据失败: {e}")
                    continue

            db.commit()
            logger.info("行情数据更新完成！")

            if db_session is None:
                db.close()

        except Exception as e:
            logger.error(f"更新行情数据失败: {e}")
            if db_session is None and 'db' in locals():
                db.rollback()
                db.close()
            raise


if __name__ == "__main__":
    # 测试
    from database import init_db
    init_db()

    collector = MarketCollector()
    collector.update_stock_list()
    collector.update_daily_quotes(days=5)
