"""
市场行情数据采集 - 使用 baostock（优化版）
- 动态获取股票列表
- 改进错误处理
- 支持上下文管理
"""
import baostock as bs
import pandas as pd
import logging
from datetime import datetime, timedelta
import sys
import os
from typing import Optional, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Stock, StockPrice, SessionLocal, get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketCollector:
    """行情数据采集器 - baostock 版本（优化版）"""

    def __init__(self):
        """初始化"""
        self._logged_in = False
        self._login()

    def _login(self):
        """登录 baostock"""
        try:
            self.lg = bs.login()
            if self.lg.error_code != '0':
                raise ValueError(f"baostock 登录失败: {self.lg.error_msg}")
            self._logged_in = True
            logger.info("baostock 登录成功")
        except Exception as e:
            logger.error(f"baostock 登录失败: {e}")
            raise

    def _ensure_login(self):
        """确保已登录"""
        if not self._logged_in:
            self._login()

    def __del__(self):
        """析构时登出"""
        try:
            if self._logged_in:
                bs.logout()
                logger.info("baostock 登出成功")
        except Exception:
            pass

    def _convert_ts_code(self, ts_code: str) -> str:
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
            return f"sh.{ts_code}"

    def _convert_bs_code_to_ts(self, bs_code: str) -> str:
        """将 baostock 代码转换为 tushare 格式"""
        if bs_code.startswith('sh'):
            return f"{bs_code[3:]}.SH"
        elif bs_code.startswith('sz'):
            return f"{bs_code[3:]}.SZ"
        return bs_code

    def fetch_stock_list_dynamic(self) -> pd.DataFrame:
        """动态获取全部 A 股股票列表"""
        try:
            self._ensure_login()
            
            rs = bs.query_all_stock(day=datetime.now().strftime('%Y-%m-%d'))
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                code = row[0]
                if code.startswith('sh.6') or code.startswith('sz.0') or code.startswith('sz.3'):
                    data_list.append({
                        'bs_code': code,
                        'ts_code': self._convert_bs_code_to_ts(code),
                        'name': row[1] if len(row) > 1 else '',
                        'industry': ''
                    })
            
            df = pd.DataFrame(data_list)
            logger.info(f"动态获取到 {len(df)} 只 A 股股票")
            return df
            
        except Exception as e:
            logger.error(f"动态获取股票列表失败: {e}")
            return self._get_default_stock_list()

    def _get_default_stock_list(self) -> pd.DataFrame:
        """获取默认股票列表（备用）"""
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
            ('sh.601318', '601318.SH', '中国平安', '保险'),
            ('sh.601398', '601398.SH', '工商银行', '银行'),
            ('sh.601939', '601939.SH', '建设银行', '银行'),
            ('sh.601288', '601288.SH', '农业银行', '银行'),
            ('sz.000001', '000001.SZ', '平安银行', '银行'),
            ('sz.000002', '000002.SZ', '万科A', '房地产'),
            ('sz.000333', '000333.SZ', '美的集团', '家用电器'),
            ('sz.000651', '000651.SZ', '格力电器', '家用电器'),
            ('sz.000858', '000858.SZ', '五粮液', '白酒'),
            ('sz.002415', '002415.SZ', '海康威视', '电子设备'),
            ('sz.002594', '002594.SZ', '比亚迪', '汽车'),
            ('sz.300750', '300750.SZ', '宁德时代', '电池'),
        ]

        df = pd.DataFrame(stocks, columns=['bs_code', 'ts_code', 'name', 'industry'])
        logger.info(f"使用默认股票列表: {len(df)} 只")
        return df

    def fetch_stock_list(self, use_dynamic: bool = True) -> pd.DataFrame:
        """获取股票列表

        Args:
            use_dynamic: 是否使用动态获取

        Returns:
            股票列表 DataFrame
        """
        if use_dynamic:
            return self.fetch_stock_list_dynamic()
        return self._get_default_stock_list()

    def fetch_daily_quotes(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取日线行情

        Args:
            ts_code: 股票代码 (Tushare 格式)
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)
        """
        try:
            self._ensure_login()
            
            bs_code = self._convert_ts_code(ts_code)

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

            logger.debug(f"获取行情数据: {bs_code} from {start_date} to {end_date}")

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            if len(df) > 0:
                df['ts_code'] = ts_code
                df['trade_date'] = df['date']
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['open'] = pd.to_numeric(df['open'], errors='coerce')
                df['high'] = pd.to_numeric(df['high'], errors='coerce')
                df['low'] = pd.to_numeric(df['low'], errors='coerce')
                df['vol'] = pd.to_numeric(df['volume'], errors='coerce')
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                df['pct_chg'] = pd.to_numeric(df['pctChg'], errors='coerce')

            return df
        except Exception as e:
            logger.error(f"获取行情数据失败 {ts_code}: {e}")
            return pd.DataFrame()

    def update_stock_list(self, db_session=None, use_dynamic: bool = False, max_stocks: int = 50):
        """更新股票列表到数据库
        
        Args:
            db_session: 数据库会话
            use_dynamic: 是否动态获取股票列表
            max_stocks: 最大股票数量（动态模式下有效）
        """
        try:
            if db_session is None:
                with get_db_session() as db:
                    self._update_stock_list_internal(db, use_dynamic, max_stocks)
            else:
                self._update_stock_list_internal(db_session, use_dynamic, max_stocks)
                
        except Exception as e:
            logger.error(f"更新股票列表失败: {e}")
            raise

    def _update_stock_list_internal(self, db, use_dynamic: bool, max_stocks: int):
        """内部更新股票列表逻辑"""
        df = self.fetch_stock_list(use_dynamic=use_dynamic)
        
        if use_dynamic and max_stocks > 0 and len(df) > max_stocks:
            df = df.head(max_stocks)

        db.query(Stock).delete()

        for _, row in df.iterrows():
            stock = Stock(
                ts_code=row['ts_code'],
                name=row.get('name', ''),
                industry=row.get('industry', ''),
                market='主板'
            )
            db.add(stock)

        db.commit()
        logger.info(f"股票列表更新完成: {len(df)} 只")

    def update_market_data(self, db_session=None, days: int = 30):
        """更新所有股票的行情数据

        Args:
            db_session: 数据库会话
            days: 获取最近多少天的数据
        """
        try:
            if db_session is None:
                with get_db_session() as db:
                    self._update_market_data_internal(db, days)
            else:
                self._update_market_data_internal(db_session, days)
                
        except Exception as e:
            logger.error(f"更新行情数据失败: {e}")
            raise

    def _update_market_data_internal(self, db, days: int):
        """内部更新行情数据逻辑"""
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
                    db.query(StockPrice).filter(
                        StockPrice.ts_code == stock.ts_code
                    ).delete()

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


if __name__ == "__main__":
    collector = MarketCollector()
    
    df = collector.fetch_stock_list(use_dynamic=True)
    print(f"获取到 {len(df)} 只股票")
    print(df.head())
