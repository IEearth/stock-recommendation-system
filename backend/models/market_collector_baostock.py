"""
市场行情数据采集 - 使用 baostock
"""
import baostock as bs
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
    """行情数据采集器 - baostock 版本"""

    def __init__(self):
        """初始化"""
        self.lg = bs.login()
        if self.lg.error_code != '0':
            raise ValueError(f"baostock 登录失败: {self.lg.error_msg}")

    def __del__(self):
        """析构时登出"""
        try:
            bs.logout()
        except:
            pass

    def _convert_ts_code(self, ts_code):
        """转换股票代码格式

        Args:
            ts_code: Tushare 格式 (如 600000.SH, 000001.SZ)

        Returns:
            baostock 格式 (如 sh.600000, sz.000001)
        """
        if ts_code.endswith('.SH'):
            return f"sh.{ts_code.split('.')[0]}"
        elif ts_code.endswith('.SZ'):
            return f"sz.{ts_code.split('.')[0]}"
        else:
            # 默认认为是沪市
            return f"sh.{ts_code}"

    def fetch_stock_list(self):
        """获取股票列表 - 使用预定义列表（15元以下有潜力的股票）"""
        # baostock 没有直接获取股票列表的接口，使用预定义列表
        stocks = [
            ('sh.600000', '600000.SH', '浦发银行', '金融'),
            ('sh.600015', '600015.SH', '华夏银行', '金融'),
            ('sh.600019', '600019.SH', '宝钢股份', '钢铁'),
            ('sh.600028', '600028.SH', '中国石化', '石油石化'),
            ('sh.600029', '600029.SH', '南方航空', '航空运输'),
            ('sh.600100', '600100.SH', '同方股份', '电子信息'),
            ('sh.600104', '600104.SH', '上汽集团', '汽车整车'),
            ('sh.600115', '600115.SH', '东方航空', '航空运输'),
            ('sh.600123', '600123.SH', '兰花科创', '煤炭'),
            ('sh.600131', '600131.SH', '国网新能', '电力设备'),
            ('sh.600256', '600256.SH', '广汇能源', '石油石化'),
            ('sh.600339', '600339.SH', '四川长虹', '家用电器'),
            ('sh.600362', '600362.SH', '江西铜业', '有色金属'),
            ('sz.000063', '000063.SZ', '中兴通讯', '通信设备'),
            ('sz.000406', '000406.SZ', '石油大明', '石油石化'),
            ('sz.000528', '000528.SZ', '柳工', '工程机械'),
            ('sz.000581', '000581.SZ', '威孚高科', '汽车零部件'),
            ('sz.000630', '000630.SZ', '铜陵有色', '有色金属'),
        ]

        df = pd.DataFrame(stocks, columns=['bs_code', 'ts_code', 'name', 'industry'])
        logger.info(f"获取到 {len(df)} 只股票 (预定义列表)")
        return df

    def fetch_daily_quotes(self, ts_code, start_date=None, end_date=None):
        """获取日线行情

        Args:
            ts_code: 股票代码 (Tushare 格式)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        """
        try:
            # 转换为 baostock 格式
            bs_code = self._convert_ts_code(ts_code)

            # 格式化日期为 YYYY-MM-DD 格式
            if start_date:
                if '-' not in start_date and len(start_date) == 8:
                    start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
            else:
                start_date = '2024-01-01'

            if end_date:
                if '-' not in end_date and len(end_date) == 8:
                    end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"获取行情数据: {bs_code} from {start_date} to {end_date}")

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"  # 不复权
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换列名以匹配原有格式
            if len(df) > 0:
                df['ts_code'] = ts_code
                df['trade_date'] = df['date']
                df['close'] = pd.to_numeric(df['close'])
                df['open'] = pd.to_numeric(df['open'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                df['vol'] = pd.to_numeric(df['volume'])
                df['pct_chg'] = pd.to_numeric(df['pctChg'])

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
                    industry=row['industry'],
                    market='主板'
                )
                db.add(stock)

            db.commit()
            logger.info(f"股票列表更新完成: {len(df)} 只")

            if db_session is None:
                db.close()

        except Exception as e:
            logger.error(f"更新股票列表失败: {e}")
            raise

    def update_market_data(self, db_session=None, days=30):
        """更新所有股票的行情数据

        Args:
            db_session: 数据库会话
            days: 获取最近多少天的数据
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            stocks = db.query(Stock).all()
            logger.info(f"开始更新 {len(stocks)} 只股票的行情数据...")

            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            success_count = 0
            for stock in stocks:
                try:
                    df = self.fetch_daily_quotes(
                        stock.ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    if len(df) > 0:
                        # 删除旧数据
                        db.query(StockPrice).filter(
                            StockPrice.ts_code == stock.ts_code
                        ).delete()

                        # 插入新数据
                        for _, row in df.iterrows():
                            price = StockPrice(
                                ts_code=stock.ts_code,
                                trade_date=row['trade_date'],
                                open=row['open'],
                                high=row['high'],
                                low=row['low'],
                                close=row['close'],
                                vol=row['vol'],
                                pct_chg=row['pct_chg']
                            )
                            db.add(price)

                        db.commit()
                        success_count += 1
                        logger.info(f"✅ {stock.name} 更新完成: {len(df)} 条数据")
                    else:
                        logger.warning(f"⚠️  {stock.name} 无数据")

                except Exception as e:
                    logger.warning(f"获取 {stock.ts_code} 数据失败: {e}")
                    db.rollback()

            logger.info(f"行情数据更新完成！成功: {success_count}/{len(stocks)}")

            if db_session is None:
                db.close()

        except Exception as e:
            logger.error(f"更新行情数据失败: {e}")
            raise
