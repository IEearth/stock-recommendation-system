"""
FastAPI 主应用
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, Recommendation, StockPrediction, SystemHealth
from models.recommender import StockRecommender

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="A股智能推荐系统",
    description="基于机器学习的A股股票智能推荐系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
recommender = StockRecommender()


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("初始化数据库...")
    init_db()
    logger.info("系统启动完成！")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A股智能推荐系统 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/recommendations/today")
async def get_today_recommendations(db: Session = Depends(get_db)):
    """获取今日推荐

    Returns:
        list: 今日推荐股票列表
    """
    try:
        recs = recommender.get_today_recommendations(db)

        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": len(recs),
            "recommendations": recs
        }
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/history")
async def get_recommendation_history(days: int = 7, db: Session = Depends(get_db)):
    """获取历史推荐

    Args:
        days: 获取最近多少天的推荐

    Returns:
        list: 历史推荐列表
    """
    try:
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = db.query(Recommendation).filter(
            Recommendation.recommend_date >= start_date.strftime('%Y-%m-%d'),
            Recommendation.recommend_date <= end_date.strftime('%Y-%m-%d')
        ).order_by(Recommendation.recommend_date.desc(), Recommendation.rank)

        result = []
        for rec in query.all():
            result.append({
                "date": rec.recommend_date,
                "rank": rec.rank,
                "ts_code": rec.ts_code,
                "name": rec.name,
                "name": rec.name,
                "predicted_return": rec.predicted_return,
                "current_price": rec.current_price,
                "reasons": rec.reasons.split('\n') if rec.reasons else []
            })

        return {
            "days": days,
            "count": len(result),
            "history": result
        }
    except Exception as e:
        logger.error(f"获取历史推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommendations/generate")
async def generate_recommendations():
    """生成新的推荐

    Returns:
        dict: 生成结果
    """
    try:
        recs = recommender.generate_recommendations(top_n=10)

        return {
            "status": "success",
            "count": len(recs),
            "message": f"成功生成 {len(recs)} 个推荐"
        }
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def list_stocks(db: Session = Depends(get_db)):
    """获取股票列表

    Returns:
        list: 股票列表
    """
    try:
        from database import Stock

        stocks = db.query(Stock).limit(100).all()

        result = []
        for stock in stocks:
            result.append({
                "ts_code": stock.ts_code,
                "name": stock.name,
                "industry": stock.industry,
                "market": stock.market
            })

        return {
            "count": len(result),
            "stocks": result
        }
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def system_status(db: Session = Depends(get_db)):
    """获取系统状态

    Returns:
        dict: 系统状态
    """
    try:
        # 获取最新的健康检查记录
        latest_health = db.query(SystemHealth).order_by(
            SystemHealth.check_time.desc()
        ).first()

        # 获取最新的推荐
        from sqlalchemy import func
        latest_rec = db.query(func.max(Recommendation.created_at)).scalar()

        return {
            "status": "running",
            "last_health_check": latest_health.check_time.isoformat() if latest_health else None,
            "last_recommendation": latest_rec.isoformat() if latest_rec else None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
