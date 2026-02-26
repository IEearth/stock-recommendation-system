"""
FastAPI 主应用 - 优化版（支持后台管理）
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, Recommendation, StockPrediction, SystemHealth, TaskLog, Stock, StockPrice, StockNews

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="A股智能推荐系统 - 管理后台",
    description="基于机器学习的A股股票智能推荐系统管理平台",
    version="2.0.0"
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
recommender = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("初始化数据库...")
    init_db()
    
    # 延迟导入避免循环依赖
    from models.recommender import StockRecommender
    global recommender
    recommender = StockRecommender()
    
    logger.info("系统启动完成！")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """管理后台首页"""
    host = request.headers.get('host', 'localhost:8000')
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股智能推荐系统 - 管理后台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5f; }}
        .container {{ display: flex; height: 100vh; }}
        .sidebar {{ width: 250px; background: #1a1a1a; color: #fff; padding: 20px 0; }}
        .sidebar h2 {{ padding: 20px; border-bottom: 1px solid #333; }}
        .menu-item {{ padding: 15px 20px; cursor: pointer; transition: background 0.3s; }}
        .menu-item:hover {{ background: #333; }}
        .menu-item.active {{ background: #2563eb; }}
        .content {{ flex: 1; padding: 30px; overflow-y: auto; }}
        .card {{ background: #2a2a2a; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .card h3 {{ color: #2563eb; margin-bottom: 15px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-box {{ background: #333; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 32px; font-weight: bold; color: #2563eb; }}
        .stat-box .label {{ color: #888; margin-top: 5px; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .data-table th, .data-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        .data-table th {{ color: #2563eb; }}
        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; }}
        .status-success {{ background: #28a745; color: #fff; }}
        .status-warning {{ background: #ffc107; color: #000; }}
        .status-error {{ background: #dc3545; color: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>📊 股票推荐系统</h2>
            <div class="menu-item active" onclick="showPage('dashboard')">🏠 仪表盘</div>
            <div class="menu-item" onclick="showPage('recommendations')">💡 每日推荐</div>
            <div class="menu-item" onclick="showPage('stocks')">📈 股票列表</div>
            <div class="menu-item" onclick="showPage('news')">📰 新闻数据</div>
            <div class="menu-item" onclick="showPage('tasks')">⏰ 任务日志</div>
            <div class="menu-item" onclick="showPage('settings')">⚙️ 系统设置</div>
        </div>
        <div class="content" id="main-content">
            <div class="card">
                <h3>系统加载中...</h3>
                <p>请稍候，正在加载数据...</p>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = 'http://{host}/api';
        
        async function showPage(page) {{
            document.querySelectorAll('.menu-item').forEach(item => {{
                item.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            switch(page) {{
                case 'dashboard': await loadDashboard(); break;
                case 'recommendations': await loadRecommendations(); break;
                case 'stocks': await loadStocks(); break;
                case 'news': await loadNews(); break;
                case 'tasks': await loadTasks(); break;
                case 'settings': await loadSettings(); break;
            }}
        }}
        
        async function loadDashboard() {{
            const response = await fetch(`${{API_BASE}}/system/status`);
            const data = await response.json();
            
            const response2 = await fetch(`${{API_BASE}}/recommendations/today`);
            const data2 = await response2.json();
            
            const response3 = await fetch(`${{API_BASE}}/tasks/recent?limit=10`);
            const data3 = await response3.json();
            
            const taskLogs = data3.logs || [];
            const lastTasks = taskLogs.slice(0, 3).map(log => `
                <div style="margin-bottom: 10px;">
                    <strong>${{log.task_name}}</strong> - 
                    <span class="status-badge ${{log.status === 'success' ? 'status-success' : 'status-error'}}">${{log.status}}</span>
                    <div style="font-size: 12px; color: #888;">${{new Date(log.start_time).toLocaleString('zh-CN')}}</div>
                </div>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
                <div class="card">
                    <h3>📊 系统概览</h3>
                    <div class="stats">
                        <div class="stat-box">
                            <div class="number">${{data2.count}}</div>
                            <div class="label">今日推荐</div>
                        </div>
                        <div class="stat-box">
                            <div class="number">${{data3.total || 0}}</div>
                            <div class="label">总任务数</div>
                        </div>
                        <div class="stat-box">
                            <div class="number" style="color: #28a745;">${{data3.success || 0}}</div>
                            <div class="label">成功任务</div>
                        </div>
                        <div class="stat-box">
                            <div class="number" style="color: #dc3545;">${{data3.failed || 0}}</div>
                            <div class="label">失败任务</div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h3>⏰ 最近任务</h3>
                    ${{lastTasks || '<p>暂无任务记录</p>'}}
                </div>
            `;
        }}
        
        // 初始加载
        loadDashboard();
        
        // 自动刷新
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
"""


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# API endpoints
@app.get("/api/recommendations/today")
async def get_today_recommendations(db: Session = Depends(get_db)):
    """获取今日推荐"""
    try:
        today = recermender.get_today_recommendations(db)
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": len(today),
            "recommendations": today
        }
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/history")
async def get_recommendation_history(days: int = 7, db: Session = Depends(get_db)):
    """获取历史推荐"""
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
                "predicted_return": rec.predicted_return,
                "current_price": rec.current_price,
                "reasons": rec.reasons.split('\\n') if rec.reasons else []
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
    """生成新的推荐"""
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
async def list_stocks(limit: int = 100, db: Session = Depends(get_db)):
    """获取股票列表"""
    try:
        stocks = db.query(Stock).limit(limit).all()
        
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


@app.get("/api/news")
async def list_news(limit: int = 50, db: Session = Depends(get_db)):
    """获取新闻列表"""
    try:
        news = db.query(StockNews).order_by(StockNews.pub_date.desc()).limit(limit).all()
        
        result = []
        for n in news:
            result.append({
                "title": n.title,
                "url": n.url,
                "pub_date": n.pub_date.isoformat() if n.pub_date else None,
                "sentiment": n.sentiment
            })
        
        return {
            "count": len(result),
            "news": result
        }
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/recent")
async def get_recent_tasks(limit: int = 10, db: Session = Depends(get_db)):
    """获取最近任务日志"""
    try:
        tasks = db.query(TaskLog).order_by(
            TaskLog.start_time.desc()
        ).limit(limit).all()
        
        # 统计
        total = db.query(func.count(TaskLog.id)).scalar()
        success = db.query(func.count(TaskLog.id)).filter(TaskLog.status == 'success').scalar()
        failed = db.query(func.count(TaskLog.id)).filter(TaskLog.status == 'failed').scalar()
        
        result = []
        for task in tasks:
            result.append({
                "task_name": task.task_name,
                "task_type": task.task_type,
                "status": task.status,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "duration_seconds": task.duration_seconds,
                "message": task.message,
                "error": task.error
            })
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "logs": result
        }
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def system_status(db: Session = Depends(get_db)):
    """获取系统状态"""
    try:
        latest_health = db.query(SystemHealth).order_by(
            SystemHealth.check_time.desc()
        ).first()
        
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
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
