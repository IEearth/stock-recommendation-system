"""
股票预测模型（简化版）
"""
import pandas as pd
import numpy as np
import logging
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import StockPrice, StockPrediction, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockPredictor:
    """股票预测器"""

    def __init__(self):
        """初始化"""
        self.models = {}

    def train(self, db_session=None):
        """训练模型（简化版 - 基于历史数据）

        Args:
            db_session: 数据库会话
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            # 获取所有股票数据
            stocks = db.query(StockPrice.ts_code).distinct().all()

            for stock in stocks:
                ts_code = stock.ts_code

                # 获取该股票的数据
                query = db.query(StockPrice).filter(
                    StockPrice.ts_code == ts_code
                ).order_by(StockPrice.trade_date.desc()).limit(100)

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
                    continue

                df = pd.DataFrame(data)

                # 计算平均涨跌幅和波动率
                avg_return = df['pct_chg'].mean()
                volatility = df['pct_chg'].std()
                momentum = df['pct_chg'].tail(5).mean()

                # 保存模型参数
                self.models[ts_code] = {
                    'avg_return': avg_return,
                    'volatility': volatility,
                    'momentum': momentum,
                    'latest_close': df['close'].iloc[0]
                }

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
            if ts_code not in self.models:
                logger.warning(f"{ts_code} 没有训练好的模型")
                return None

            model = self.models[ts_code]

            # 基于动量和平均涨跌幅进行预测
            # 加上一些随机性模拟预测
            base_prediction = model['momentum'] * 0.6 + model['avg_return'] * 0.4

            # 如果动量是正的，增加一点预测值
            if model['momentum'] > 0:
                base_prediction += abs(base_prediction) * 0.2

            # 置信度基于稳定性
            volatility = model['volatility']
            confidence = max(0.3, min(0.9, 1 - volatility / 10))

            return {
                'ts_code': ts_code,
                'predicted_return': float(base_prediction),
                'confidence': float(confidence),
                'current_price': float(model['latest_close'])
            }

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return None


if __name__ == "__main__":
    # 测试
    from database import init_db
    init_db()

    predictor = StockPredictor()
    predictor.train()
    result = predictor.predict('600519.SH')
    print(result)
