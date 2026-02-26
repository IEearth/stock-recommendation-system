"""
数据库模型和连接管理
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_recommendations.db")

# 创建引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Stock(Base):
    """股票基本信息"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), unique=True, index=True)  # 股票代码
    name = Column(String(100))  # 股票名称
    industry = Column(String(100))  # 所属行业
    market = Column(String(20))  # 市场 (主板/创业板/科创板)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockPrice(Base):
    """股票行情数据"""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), index=True)  # 股票代码
    trade_date = Column(String(10), index=True)  # 交易日期
    open = Column(Float)  # 开盘价
    high = Column(Float)  # 最高价
    low = Column(Float)  # 最低价
    close = Column(Float)  # 收盘价
    vol = Column(Float)  # 成交量
    amount = Column(Float)  # 成交额
    pct_chg = Column(Float)  # 涨跌幅
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('idx_stock_date', 'ts_code', 'trade_date'),)


class StockNews(Base):
    """股票新闻"""
    __tablename__ = "stock_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))  # 新闻标题
    content = Column(Text)  # 新闻内容
    url = Column(String(500))  # 新闻链接
    pub_date = Column(DateTime, index=True)  # 发布时间
    sentiment = Column(Float)  # 情感分析得分 (-1 到 1)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockPrediction(Base):
    """股票预测结果"""
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), index=True)  # 股票代码
    name = Column(String(100))  # 股票名称
    predict_date = Column(String(10), index=True)  # 预测日期
    predicted_return = Column(Float)  # 预测收益率
    confidence = Column(Float)  # 置信度
    current_price = Column(Float)  # 当前价格
    reasons = Column(Text)  # 推荐理由
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('idx_predict_date', 'predict_date'),)


class Recommendation(Base):
    """每日推荐股票"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20))  # 股票代码
    name = Column(String(100))  # 股票名称
    rank = Column(Integer)  # 排名 (1-10)
    recommend_date = Column(String(10), index=True)  # 推荐日期
    predicted_return = Column(Float)  # 预测收益率
    current_price = Column(Float)  # 当前价格
    reasons = Column(Text)  # 推荐理由
    is_published = Column(Boolean, default=False)  # 是否已发布
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('idx_recommend_date', 'recommend_date'),)


class SystemHealth(Base):
    """系统健康状态"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    check_time = Column(DateTime, index=True, default=datetime.utcnow)
    status = Column(String(20))  # running/stopped/error
    data_update_time = Column(DateTime)  # 数据最后更新时间
    last_prediction_time = Column(DateTime)  # 最后预测时间
    error_message = Column(Text)  # 错误信息


# 创建所有表
def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成！")
