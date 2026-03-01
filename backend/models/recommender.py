"""
股票推荐引擎（优化版）
"""
import logging
from datetime import datetime
import sys
import os
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Stock, Recommendation, StockPrediction, SessionLocal, get_db_session
from models.predictor import StockPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockRecommender:
    """股票推荐引擎"""

    def __init__(self):
        """初始化"""
        self.predictor = StockPredictor()

    def generate_recommendations(self, top_n: int = 10, min_price: float = 0, max_price: float = 15, db_session=None) -> List[Recommendation]:
        """生成推荐

        Args:
            top_n: 推荐数量
            min_price: 最低股价
            max_price: 最高股价
            db_session: 数据库会话

        Returns:
            list: 推荐列表
        """
        try:
            if db_session is None:
                with get_db_session() as db:
                    return self._generate_recommendations_internal(db, top_n, min_price, max_price)
            else:
                return self._generate_recommendations_internal(db_session, top_n, min_price, max_price)
                
        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            raise

    def _generate_recommendations_internal(self, db, top_n: int, min_price: float, max_price: float) -> List[Recommendation]:
        """内部推荐生成逻辑"""
        logger.info(f"开始生成股票推荐... 价格范围: ¥{min_price}-{max_price}")

        stocks = db.query(Stock).limit(100).all()

        predictions = []

        for stock in stocks:
            pred = self.predictor.predict(stock.ts_code, db)

            if pred and pred['predicted_return'] > 0 and min_price <= pred['current_price'] <= max_price:
                pred['name'] = stock.name
                predictions.append(pred)

        predictions.sort(key=lambda x: x['predicted_return'], reverse=True)

        top_predictions = predictions[:top_n]

        today = datetime.now().strftime('%Y-%m-%d')
        db.query(Recommendation).filter(Recommendation.recommend_date == today).delete()

        recommendations = []
        for i, pred in enumerate(top_predictions):
            target_price = pred['current_price'] * (1 + pred['predicted_return'] / 100)

            reasons = []
            reasons.append(f"预测收益率: {pred['predicted_return']:.2f}%")
            reasons.append(f"当前价格: ¥{pred['current_price']:.2f}")
            reasons.append(f"目标价格: ¥{target_price:.2f}")
            reasons.append(f"模型置信度: {pred['confidence']:.2%}")
            
            if 'signals' in pred:
                signals = pred['signals']
                if signals.get('trend') == 'up':
                    reasons.append("趋势向上")
                if signals.get('macd') == 'bullish':
                    reasons.append("MACD金叉信号")
                if signals.get('rsi') == 'oversold':
                    reasons.append("RSI超卖区域")
            
            if pred['predicted_return'] > 5:
                reasons.append("技术面强势，突破关键位")
            elif pred['predicted_return'] > 2:
                reasons.append("趋势向上，成交量配合")

            rec = Recommendation(
                ts_code=pred['ts_code'],
                name=pred['name'],
                rank=i + 1,
                recommend_date=today,
                predicted_return=pred['predicted_return'],
                current_price=pred['current_price'],
                reasons='\n'.join(reasons),
                is_published=False
            )
            recommendations.append(rec)
            db.add(rec)

        db.commit()
        logger.info(f"推荐生成完成: {len(recommendations)} 只")

        return recommendations

    def get_today_recommendations(self, db_session=None) -> List[dict]:
        """获取今日推荐

        Args:
            db_session: 数据库会话

        Returns:
            list: 推荐列表
        """
        try:
            if db_session is None:
                with get_db_session() as db:
                    return self._get_today_recommendations_internal(db)
            else:
                return self._get_today_recommendations_internal(db_session)
                
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []

    def _get_today_recommendations_internal(self, db) -> List[dict]:
        """内部获取今日推荐逻辑"""
        today = datetime.now().strftime('%Y-%m-%d')

        recs = db.query(Recommendation).filter(
            Recommendation.recommend_date == today
        ).order_by(Recommendation.rank).all()

        result = []
        for rec in recs:
            result.append({
                'rank': rec.rank,
                'ts_code': rec.ts_code,
                'name': rec.name,
                'predicted_return': rec.predicted_return,
                'current_price': rec.current_price,
                'target_price': rec.current_price * (1 + rec.predicted_return / 100),
                'reasons': rec.reasons.split('\n') if rec.reasons else [],
                'created_at': rec.created_at.isoformat() if rec.created_at else None
            })

        return result


if __name__ == "__main__":
    from database import init_db
    init_db()

    recommender = StockRecommender()
    recs = recommender.generate_recommendations(top_n=5)
    print(f"生成了 {len(recs)} 个推荐")

    today_recs = recommender.get_today_recommendations()
    print(f"今日推荐: {len(today_recs)}")
