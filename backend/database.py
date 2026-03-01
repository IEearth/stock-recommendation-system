"""
数据库模型和连接管理（支持 MySQL 和 SQLite）
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_recommendations.db")

# 创建引擎（MySQL 需要特定配置）
if DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Stock(Base):
    """股票基本信息"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    ts_code = Column(String(20), unique=True, index=True, nullable=False, comment="股票代码")
    name = Column(String(100), comment="股票名称")
    industry = Column(String(100), comment="所属行业")
    market = Column(String(20), comment="市场 (主板/创业板/科创板)")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class StockPrice(Base):
    """股票行情数据"""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    ts_code = Column(String(20), index=True, comment="股票代码")
    trade_date = Column(String(10), index=True, comment="交易日期")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    vol = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")
    pct_chg = Column(Float, comment="涨跌幅")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index('idx_stock_date', 'ts_code', 'trade_date'),
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


class StockNews(Base):
    """股票新闻"""
    __tablename__ = "stock_news"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(500), comment="新闻标题")
    content = Column(Text, comment="新闻内容")
    url = Column(String(500), comment="新闻链接")
    pub_date = Column(DateTime, index=True, comment="发布时间")
    sentiment = Column(Float, comment="情感分析得分 (-1 到 1)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class StockPrediction(Base):
    """股票预测结果"""
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    ts_code = Column(String(20), index=True, comment="股票代码")
    name = Column(String(100), comment="股票名称")
    predict_date = Column(String(10), index=True, comment="预测日期")
    predicted_return = Column(Float, comment="预测收益率")
    confidence = Column(Float, comment="置信度")
    current_price = Column(Float, comment="当前价格")
    reasons = Column(Text, comment="推荐理由")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index('idx_predict_date', 'predict_date'),
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


class Recommendation(Base):
    """每日推荐股票"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    ts_code = Column(String(20), comment="股票代码")
    name = Column(String(100), comment="股票名称")
    rank = Column(Integer, comment="排名 (1-10)")
    recommend_date = Column(String(10), index=True, comment="推荐日期")
    predicted_return = Column(Float, comment="预测收益率")
    current_price = Column(Float, comment="当前价格")
    reasons = Column(Text, comment="推荐理由")
    is_published = Column(Boolean, default=False, comment="是否已发布")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        Index('idx_recommend_date', 'recommend_date'),
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


class SystemHealth(Base):
    """系统健康状态"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    check_time = Column(DateTime, index=True, default=datetime.utcnow, comment="检查时间")
    status = Column(String(20), comment="运行状态 (running/stopped/error)")
    data_update_time = Column(DateTime, comment="数据最后更新时间")
    last_prediction_time = Column(DateTime, comment="最后预测时间")
    error_message = Column(Text, comment="错误信息")

    __table_args__ = (
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


class TaskConfig( Base):
    """任务配置表"""
    __tablename__ = "task_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    task_name = Column(String(100), unique=True, index=True, nullable=False, comment="任务名称")
    task_type = Column(String(50), comment="任务类型 (daily_update/data_fetch/recommendation/health_check)")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    interval_seconds = Column(Integer, comment="执行间隔（秒）")
    cron_expression = Column(String(100), comment="Cron表达式（可选）")
    last_run_time = Column(DateTime, comment="上次执行时间")
    next_run_time = Column(DateTime, comment="下次执行时间")
    config_json = Column(Text, comment="JSON格式的额外配置")
    description = Column(Text, comment="任务描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index('idx_task_config_name', 'task_name'),
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


class TaskLog(Base):
    """任务执行日志"""
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    task_name = Column(String(100), index=True, comment="任务名称")
    task_type = Column(String(50), comment="任务类型 (data_update/health_check)")
    status = Column(String(20), comment="执行状态 (success/failed/running)")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    duration_seconds = Column(Float, comment="执行时长（秒）")
    message = Column(Text, comment="执行消息")
    error = Column(Text, comment="错误信息")

    __table_args__ = (
        Index('idx_task_name', 'task_name'),
        Index('idx_task_status', 'status'),
        {'mysql_charset': 'utf8mb4'} if DATABASE_URL.startswith('mysql') else {}
    )


# 创建所有表
def init_db():
    """初始化数据库"""
    try:
        Base.metadata.create_all(bind=engine)
        print(f"✅ 数据库初始化成功 ({DATABASE_URL})")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseSessionManager:
    """数据库会话管理器 - 支持上下文管理"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type:
                self.db.rollback()
            self.db.close()
        return False


def get_db_session():
    """获取数据库会话上下文管理器"""
    return DatabaseSessionManager()


if __name__ == "__main__":
    init_db()
    print(f"数据库类型: {'MySQL' if DATABASE_URL.startswith('mysql') else 'SQLite'}")
