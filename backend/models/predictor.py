"""
股票预测模型（简化版）
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import StockPrice, StockPrediction, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockPredictor:
    """股票预测器"""

    def __init__(self):
        """初始化"""
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()

    def prepare_features(self, df):
        """准备特征

        Args:
            df: 股票行情数据

        Returns:
            np.array: 特征矩阵
        """
        # 基础特征
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()

        df['vol_ma5'] = df['vol'].rolling(5).mean()

        df['pct_chg_ma5'] = df['pct_chg'].rolling(5).mean()

        # 价格相对位置
        df['price_range'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-6)

        # 动量指标
        df['momentum'] = df['close'].pct_change(5)

        # 目标：下一日涨跌幅
        df['target'] = df['pct_chg'].shift(-1)

        # 删除NaN
        df = df.dropna()

        # 特征列
        feature_cols = [
            'ma5', 'ma10', 'ma20',
            'vol_ma5',
            'pct_chg_ma5',
            'price_range',
            'momentum'
        ]

        X = df[feature_cols].values
        y = df['target'].values

        return X, y, df[['ts_code', 'trade_date', 'close']].iloc[-len(y):]

    def train(self, db_session=None):
        """训练模型

        Args:
            db_session: 数据库会话
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            # 获取行情数据
            query = db.query(StockPrice).order_by(StockPrice.trade_date.desc()).limit(1000)

            # 转为DataFrame
            data = []
            for row in query.all():
                data.append({
                    'ts_code': row.ts_code,
                    'trade_date': row.trade_date,
                    'open': row.open,
                    'high': row.high,
                    'low': row.low,
                    'close': row.close,
                    'vol': row.vol,
                    'pct_chg': row.pct_chg
                })

            if len(data) < 50:
                logger.warning("数据不足，无法训练模型")
                return

            df = pd.DataFrame(data)
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 按股票分组训练
            for ts_code, stock_df in df.groupby('ts_code'):
                if len(stock_df) < 30:
                    continue

                X, y, info = self.prepare_features(stock_df)

                if len(X) < 20:
                    continue

                # 训练
                X_scaled = self.scaler.fit_transform(X)
                self.model.fit(X_scaled, y)

                logger.info(f"股票 {ts_code} 模型训练完成")

            if db_session is None:
                db.close()

            logger.info("模型训练完成！")

        except Exception as e:
            logger.error(f"训练模型失败: {e}")
            if db_session is None and 'db' in locals():
                db.close()
            raise

    def predict(self, ts_code, db_session=None):
        """预测股票

        Args:
            ts_code: 股票代码
            db_session: 数据库会话

        Returns:
            dict: 预测结果
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            # 获取最近的行情数据
            query = db.query(StockPrice).filter(
                StockPrice.ts_code == ts_code
            ).order_by(StockPrice.trade_date.desc()).limit(50)

            data = []
            for row in query.all():
                data.append({
                    'ts_code': row.ts_code,
                    'trade_date': row.trade_date,
                    'open': row.open,
                    'high': row.high,
                    'low': row.low,
                    'close': row.close,
                    'vol': row.vol,
                    'pct_chg': row.pct_chg
                })

            if len(data) < 20:
                logger.warning(f"{ts_code} 数据不足，无法预测")
                return None

            df = pd.DataFrame(data)
            df = df.sort_values('trade_date')

            X, y, info = self.prepare_features(df)

            # 预测
            if len(X) > 0:
                X_scaled = self.scaler.transform(X[-1:])
                prediction = self.model.predict(X_scaled)[0]
                confidence = min(abs(prediction) * 10, 0.95)  # 置信度估算

                current_price = info['close'].iloc[-1]

                return {
                    'ts_code': ts_code,
                    'predicted_return': float(prediction),
                    'confidence': float(confidence),
                    'current_price': float(current_price)
                }

            if db_session is None:
                db.close()

            return None

        except Exception as e:
            logger.error(f"预测失败: {e}")
            if db_session is None and 'db' in locals():
                db.close()
            return None


if __name__ == "__main__":
    # 测试
    from database import init_db
    init_db()

    predictor = StockPredictor()
    predictor.train()
    result = predictor.predict('000001.SZ')
    print(result)
