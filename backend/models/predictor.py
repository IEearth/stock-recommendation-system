"""
股票预测模型（优化版）
- 添加更多技术指标
- 改进预测算法
- 模型持久化存储
"""
import pandas as pd
import numpy as np
import logging
import sys
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import StockPrice, StockPrediction, SessionLocal, get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ma(series: pd.Series, window: int) -> pd.Series:
        """计算移动平均线"""
        return series.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(series: pd.Series, window: int) -> pd.Series:
        """计算指数移动平均线"""
        return series.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """计算相对强弱指标 RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算 MACD 指标"""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            'macd': macd_line.iloc[-1] if len(macd_line) > 0 else 0,
            'signal': signal_line.iloc[-1] if len(signal_line) > 0 else 0,
            'histogram': histogram.iloc[-1] if len(histogram) > 0 else 0
        }
    
    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2) -> Dict:
        """计算布林带"""
        ma = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return {
            'upper': upper.iloc[-1] if len(upper) > 0 else 0,
            'middle': ma.iloc[-1] if len(ma) > 0 else 0,
            'lower': lower.iloc[-1] if len(lower) > 0 else 0
        }
    
    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> Dict:
        """计算 KDJ 指标"""
        low_n = low.rolling(window=n).min()
        high_n = high.rolling(window=n).max()
        rsv = (close - low_n) / (high_n - low_n + 1e-10) * 100
        
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return {
            'k': k.iloc[-1] if len(k) > 0 else 50,
            'd': d.iloc[-1] if len(d) > 0 else 50,
            'j': j.iloc[-1] if len(j) > 0 else 50
        }


class StockPredictor:
    """股票预测器（优化版）"""

    def __init__(self):
        """初始化"""
        self.models = {}
        self.indicators = TechnicalIndicators()

    def _prepare_dataframe(self, data: list) -> pd.DataFrame:
        """准备数据框"""
        df = pd.DataFrame(data)
        if len(df) == 0:
            return df
        
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        df = df.reset_index(drop=True)
        
        for col in ['open', 'high', 'low', 'close', 'vol', 'pct_chg']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df

    def _calculate_features(self, df: pd.DataFrame) -> Dict:
        """计算特征"""
        if len(df) < 20:
            return None
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['vol']
        pct_chg = df['pct_chg']
        
        ma5 = self.indicators.calculate_ma(close, 5)
        ma10 = self.indicators.calculate_ma(close, 10)
        ma20 = self.indicators.calculate_ma(close, 20)
        
        rsi = self.indicators.calculate_rsi(close, 14)
        macd = self.indicators.calculate_macd(close)
        boll = self.indicators.calculate_bollinger_bands(close)
        kdj = self.indicators.calculate_kdj(high, low, close)
        
        momentum_5 = pct_chg.tail(5).mean()
        momentum_10 = pct_chg.tail(10).mean()
        volatility = pct_chg.std()
        
        current_price = close.iloc[-1]
        ma5_val = ma5.iloc[-1]
        ma10_val = ma10.iloc[-1]
        ma20_val = ma20.iloc[-1]
        
        trend_score = 0
        if current_price > ma5_val:
            trend_score += 1
        if ma5_val > ma10_val:
            trend_score += 1
        if ma10_val > ma20_val:
            trend_score += 1
        
        volume_trend = 0
        if len(volume) >= 5:
            vol_ma5 = volume.tail(5).mean()
            vol_ma10 = volume.tail(10).mean()
            if vol_ma5 > vol_ma10:
                volume_trend = 1
        
        return {
            'current_price': float(current_price),
            'ma5': float(ma5_val),
            'ma10': float(ma10_val),
            'ma20': float(ma20_val),
            'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
            'macd': macd,
            'bollinger': boll,
            'kdj': kdj,
            'momentum_5': float(momentum_5),
            'momentum_10': float(momentum_10),
            'volatility': float(volatility),
            'trend_score': trend_score,
            'volume_trend': volume_trend,
            'avg_return': float(pct_chg.mean())
        }

    def train(self, db_session=None):
        """训练模型"""
        try:
            if db_session is None:
                with get_db_session() as db:
                    self._train_internal(db)
            else:
                self._train_internal(db_session)
            
            logger.info("模型训练完成！")
            
        except Exception as e:
            logger.error(f"训练模型失败: {e}")
            raise

    def _train_internal(self, db):
        """内部训练逻辑"""
        stocks = db.query(StockPrice.ts_code).distinct().all()
        
        for stock in stocks:
            ts_code = stock.ts_code
            
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
            
            df = self._prepare_dataframe(data)
            features = self._calculate_features(df)
            
            if features:
                self.models[ts_code] = features
                logger.info(f"股票 {ts_code} 模型训练完成")

    def predict(self, ts_code: str, db_session=None) -> Optional[Dict[str, Any]]:
        """预测股票"""
        try:
            if ts_code not in self.models:
                if db_session is None:
                    with get_db_session() as db:
                        self._train_single_stock(ts_code, db)
                else:
                    self._train_single_stock(ts_code, db_session)
            
            if ts_code not in self.models:
                logger.warning(f"{ts_code} 没有足够的数据进行预测")
                return None
            
            model = self.models[ts_code]
            
            prediction_score = 0
            
            if model['trend_score'] >= 2:
                prediction_score += 1
            
            if model['momentum_5'] > 0:
                prediction_score += 1
            
            if model['rsi'] < 70 and model['rsi'] > 30:
                prediction_score += 0.5
            
            if model['macd']['histogram'] > 0:
                prediction_score += 1
            
            if model['kdj']['j'] < 100 and model['kdj']['j'] > 0:
                prediction_score += 0.5
            
            if model['volume_trend'] > 0:
                prediction_score += 0.5
            
            base_prediction = model['momentum_5'] * 0.4 + model['momentum_10'] * 0.3 + model['avg_return'] * 0.3
            
            if prediction_score >= 3:
                base_prediction *= 1.2
            elif prediction_score <= 1:
                base_prediction *= 0.8
            
            volatility = model['volatility']
            confidence = max(0.3, min(0.9, 0.5 + (prediction_score - 2) * 0.1 - volatility / 20))
            
            return {
                'ts_code': ts_code,
                'predicted_return': round(float(base_prediction), 2),
                'confidence': round(float(confidence), 3),
                'current_price': round(model['current_price'], 2),
                'signals': {
                    'trend': 'up' if model['trend_score'] >= 2 else 'down',
                    'rsi': 'oversold' if model['rsi'] < 30 else 'overbought' if model['rsi'] > 70 else 'neutral',
                    'macd': 'bullish' if model['macd']['histogram'] > 0 else 'bearish'
                }
            }
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return None

    def _train_single_stock(self, ts_code: str, db):
        """训练单个股票"""
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
            return
        
        df = self._prepare_dataframe(data)
        features = self._calculate_features(df)
        
        if features:
            self.models[ts_code] = features


if __name__ == "__main__":
    from database import init_db
    init_db()

    predictor = StockPredictor()
    predictor.train()
    result = predictor.predict('600519.SH')
    print(result)
