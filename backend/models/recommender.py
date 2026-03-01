"""
股票推荐引擎（支持交易日判断）
"""
import logging
import random
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Stock, Recommendation, StockPrediction, SessionLocal
from models.predictor import StockPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockRecommender:
    """股票推荐引擎"""

    def __init__(self):
        """初始化"""
        self.predictor = StockPredictor()

        # 导入交易日检查器
        try:
            from utils.trading_day_checker import get_trading_day_checker
            self.trading_checker = get_trading_day_checker()
            logger.info("✅ 交易日检查器已启用")
        except ImportError:
            logger.warning("⚠️ 交易日检查器未找到，将不执行交易日检查")
            self.trading_checker = None

    def should_run_today(self, force: bool = False) -> tuple:
        """
        判断今天是否应该执行推荐

        Args:
            force: 是否强制执行

        Returns:
            (是否执行, 原因)
        """
        if force:
            return True, "强制执行"

        if self.trading_checker is None:
            return True, "交易日检查器未启用，默认执行"

        should_run, reason = self.trading_checker.should_run_today()

        if not should_run:
            logger.info(f"⏭️  跳过今日推荐: {reason}")

        return should_run, reason

    def generate_recommendations(self, top_n=10, min_price=0, max_price=15, db_session=None, force=False):
        """
        生成推荐

        Args:
            top_n: 推荐数量
            min_price: 最低股价
            max_price: 最高股价
            db_session: 数据库会话
            force: 强制执行（忽略交易日检查）

        Returns:
            list: 推荐列表
        """
        try:
            # 检查是否为交易日
            should_run, reason = self.should_run_today(force=force)

            if not should_run:
                logger.info(f"⏭️  跳过推荐生成: {reason}")
                return []

            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            logger.info(f"开始生成股票推荐... 价格范围: ¥{min_price}-{max_price}")

            # 获取所有股票
            stocks = db.query(Stock).limit(100).all()

            predictions = []

            for stock in stocks:
                # 预测
                pred = self.predictor.predict(stock.ts_code, db)

                # 只推荐预测收益为正且价格在指定范围内的股票
                if pred and pred['predicted_return'] > 0 and min_price <= pred['current_price'] <= max_price:
                    pred['name'] = stock.name
                    predictions.append(pred)

            # 按预测收益率排序
            predictions.sort(key=lambda x: x['predicted_return'], reverse=True)

            # 取前N个
            top_predictions = predictions[:top_n]

            # 生成推荐理由
            recommendations = []
            for i, pred in enumerate(top_predictions):
                # 计算目标价
                target_price = pred['current_price'] * (1 + pred['predicted_return'] / 100)

                # 生成理由
                reasons = []
                reasons.append(f"预测收益率: {pred['predicted_return']:.2f}%")
                reasons.append(f"当前价格: ¥{pred['current_price']:.2f}")
                reasons.append(f"目标价格: ¥{target_price:.2f}")
                reasons.append(f"模型置信度: {pred['confidence']:.2%}")

                if pred['predicted_return'] > 5:
                    reasons.append("技术面强势，突破关键位")
                elif pred['predicted_return'] > 2:
                    reasons.append("趋势向上，成交量配合")

                rec = Recommendation(
                    ts_code=pred['ts_code'],
                    name=pred['name'],
                    rank=i + 1,
                    recommend_date=datetime.now().strftime('%Y-%m-%d'),
                    predicted_return=pred['predicted_return'],
                    current_price=pred['current_price'],
                    reasons='\n'.join(reasons),
                    is_published=False
                )
                recommendations.append(rec)

            # 保存到数据库
            for rec in recommendations:
                db.add(rec)

            db.commit()
            logger.info(f"推荐生成完成: {len(recommendations)} 只")

            if db_session is None:
                db.close()

            return recommendations

        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            if db_session is None and 'db' in locals():
                db.rollback()
                db.close()
            raise

    def get_today_recommendations(self, db_session=None):
        """获取今日推荐

        Args:
            db_session: 数据库会话

        Returns:
            list: 推荐列表
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

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
                    'reasons': rec.reasons.split('\n')
                })

            if db_session is None:
                db.close()

            return result

        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            if db_session is None and 'db' in locals():
                db.close()
            return []


if __name__ == "__main__":
    # 测试
    from database import init_db
    init_db()

    recommender = StockRecommender()

    # 测试交易日检查
    print("测试交易日检查:")
    should_run, reason = recommender.should_run_today()
    print(f"应该运行: {should_run}, 原因: {reason}")

    # 测试推荐生成
    print("\n测试推荐生成:")
    recs = recommender.generate_recommendations(top_n=5)
    print(f"生成了 {len(recs)} 个推荐")

    # 测试获取今日推荐
    today_recs = recommender.get_today_recommendations()
    print(f"今日推荐: {len(today_recs)}")
