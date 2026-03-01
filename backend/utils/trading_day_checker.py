"""
交易日判断模块
支持中国A股交易日判断，排除周末和节假日
"""
import logging
from datetime import datetime, timedelta
import json
from typing import Set, Optional, Tuple
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDayChecker:
    """交易日判断器"""

    def __init__(self, cache_days: int = 365):
        """
        初始化交易日判断器

        Args:
            cache_days: 缓存的天数
        """
        self.cache_days = cache_days
        self.holidays_cache: Set[str] = set()
        self.cache_loaded = False
        self.use_tushare = False

        # 尝试导入 tushare
        try:
            import tushare as ts
            self.ts = ts
            # 检查是否有 token
            token = os.getenv('TUSHARE_TOKEN')
            if token:
                self.ts.set_token(token)
                self.use_tushare = True
                logger.info("✅ Tushare API 已启用")
            else:
                logger.warning("⚠️  未设置 TUSHARE_TOKEN，将使用本地交易日历缓存")
        except ImportError:
            logger.warning("⚠️  Tushare 未安装，使用本地交易日历缓存")
            self.ts = None

    def load_holidays(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Set[str]:
        """
        加载节假日数据

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            节假日集合
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=self.cache_days)).strftime('%Y%m%d')
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y%m%d')

        # 如果使用 tushare，从 API 获取
        if self.use_tushare:
            try:
                pro = self.ts.pro_api()
                df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)

                # 获取非交易日（节假日和周末）
                holidays = df[df['is_open'] == 0]['cal_date'].tolist()
                self.holidays_cache = set(holidays)
                self.cache_loaded = True
                logger.info(f"✅ 从 Tushare 加载节假日数据: {len(self.holidays_cache)} 天")
                return self.holidays_cache

            except Exception as e:
                logger.error(f"❌ 从 Tushare 获取交易日历失败: {e}")
                self.use_tushare = False

        # 使用本地节假日数据（中国主要节假日）
        self.holidays_cache = self._get_chinese_holidays()
        self.cache_loaded = True
        logger.info(f"✅ 使用本地节假日缓存: {len(self.holidays_cache)} 天")
        return self.holidays_cache

    def _get_chinese_holidays(self) -> Set[str]:
        """
        获取中国主要节假日（2024-2027）

        Returns:
            节假日集合 (YYYYMMDD 格式)
        """
        # 手动维护的中国主要节假日（2024-2027）
        holidays = [
            # 2024年
            '20240101', '20240210', '20240211', '20240212', '20240213', '20240214', '20240215', '20240216', '20240217',
            '20240404', '20240405', '20240406', '20240430', '20240501', '20240502', '20240503', '20240504', '20240505',
            '20240610', '20240915', '20240916', '20240917', '20241001', '20241002', '20241003', '20241004', '20241005', '20241006', '20241007',
            # 2025年
            '20250101', '20250128', '20250129', '20250130', '20250131', '20250201', '20250202', '20250203', '20250204',
            '20250404', '20250405', '20250406', '20250501', '20250502', '20250503', '20250504', '20250505',
            '20250531', '20250602', '20250906', '20250907', '20250908', '20251001', '20251002', '20251003', '20251004', '20251005', '20251006', '20251007', '20251008',
            # 2026年
            '20260101', '20260216', '20260217', '20260218', '20260219', '20260220', '20260221', '20260222', '20260223', '20260224',
            '20260404', '20260405', '20260406', '20260501', '20260502', '20260503', '20260504', '20260505',
            '20260601', '20260925', '20260926', '20260927', '20261001', '20261002', '20261003', '20261004', '20261005', '20261006', '20261007', '20261008',
            # 2027年
            '20270101', '20270206', '20270207', '20270208', '20270209', '20270210', '20270211', '20270212', '20270213', '20270214',
            '20270403', '20270404', '20270405', '20270501', '20270502', '20270503', '20270504', '20270505',
            '20270621', '20270918', '20270919', '20270920', '20271001', '20271002', '20271003', '20271004', '20271005', '20271006', '20271007', '20271008',
        ]

        # 添加所有周末（非交易日）
        # 实际判断时会动态检查周末，这里只存真正的节假日
        return set(holidays)

    def is_trading_day(self, date: Optional[datetime] = None) -> bool:
        """
        判断是否为交易日

        Args:
            date: 要检查的日期，默认为今天

        Returns:
            bool: True 是交易日，False 非交易日
        """
        if date is None:
            date = datetime.now()

        # 加载节假日缓存
        if not self.cache_loaded:
            self.load_holidays()

        # 检查是否为周末
        if date.weekday() >= 5:  # 5=周六, 6=周日
            return False

        # 检查是否为节假日
        date_str = date.strftime('%Y%m%d')
        if date_str in self.holidays_cache:
            return False

        return True

    def get_next_trading_day(self, start_date: Optional[datetime] = None, max_days: int = 10) -> datetime:
        """
        获取下一个交易日

        Args:
            start_date: 起始日期，默认为明天
            max_days: 最大查找天数

        Returns:
            下一个交易日
        """
        if start_date is None:
            start_date = datetime.now() + timedelta(days=1)

        current = start_date
        days_checked = 0

        while days_checked < max_days:
            if self.is_trading_day(current):
                return current
            current += timedelta(days=1)
            days_checked += 1

        logger.warning(f"⚠️  在 {max_days} 天内未找到交易日，返回原始日期")
        return start_date

    def get_previous_trading_day(self, start_date: Optional[datetime] = None, max_days: int = 10) -> datetime:
        """
        获取上一个交易日

        Args:
            start_date: 起始日期，默认为昨天
            max_days: 最大查找天数

        Returns:
            上一个交易日
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=1)

        current = start_date
        days_checked = 0

        while days_checked < max_days:
            if self.is_trading_day(current):
                return current
            current -= timedelta(days=1)
            days_checked += 1

        logger.warning(f"⚠️  在 {max_days} 天内未找到交易日，返回原始日期")
        return start_date

    def get_trading_days_range(self, start_date: str, end_date: str) -> list:
        """
        获取日期范围内的所有交易日

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            交易日列表
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        trading_days = []
        current = start

        while current <= end:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)

        return trading_days

    def get_next_trading_day_cron(self) -> str:
        """
        获取下一个交易日的 Cron 表达式

        Returns:
            Cron 时间表达式 (仅返回时间部分，不包含日期)
        """
        # 通常在交易日 9:00-9:30 执行任务
        return "30 9"

    def should_run_today(self, check_time: Optional[datetime] = None, force: bool = False) -> Tuple[bool, str]:
        """
        判断今天是否应该执行任务

        Args:
            check_time: 检查时间
            force: 是否强制执行

        Returns:
            (是否执行, 原因)
        """
        if force:
            return True, "强制执行"

        if check_time is None:
            check_time = datetime.now()

        if not self.is_trading_day(check_time):
            # 获取下一个交易日
            next_trading = self.get_next_trading_day(check_time)
            reason = f"非交易日（{check_time.strftime('%Y-%m-%d %A')}），下一个交易日: {next_trading.strftime('%Y-%m-%d')}"
            return False, reason

        return True, "是交易日，可以执行"


# 全局实例
_trading_day_checker = None


def get_trading_day_checker() -> TradingDayChecker:
    """获取交易日检查器实例（单例）"""
    global _trading_day_checker
    if _trading_day_checker is None:
        _trading_day_checker = TradingDayChecker()
    return _trading_day_checker


if __name__ == "__main__":
    # 测试
    checker = TradingDayChecker()

    today = datetime.now()
    print(f"今天 ({today.strftime('%Y-%m-%d %A')}): 是交易日? {checker.is_trading_day(today)}")

    next_trading = checker.get_next_trading_day()
    print(f"下一个交易日: {next_trading.strftime('%Y-%m-%d %A')}")

    prev_trading = checker.get_previous_trading_day()
    print(f"上一个交易日: {prev_trading.strftime('%Y-%m-%d %A')}")

    # 测试应该运行
    should_run, reason = checker.should_run_today()
    print(f"今天应该运行: {should_run}, 原因: {reason}")
