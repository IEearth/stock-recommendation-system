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
from sqlalchemy import func

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
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }}
        
        .container {{
            display: flex;
            min-height: 100vh;
        }}
        
        .sidebar {{
            width: 260px;
            background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
            color: #f3f4f6;
            padding: 24px 0;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }}
        
        .sidebar h2 {{
            padding: 0 24px 24px;
            font-size: 18px;
            font-weight: 700;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 16px;
        }}
        
        .menu-item {{
            padding: 14px 24px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-left: 3px solid transparent;
            font-size: 14px;
            color: #9ca3af;
        }}
        
        .menu-item:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: #e5e7eb;
            border-left-color: #667eea;
        }}
        
        .menu-item.active {{
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.2), transparent);
            color: #fff;
            border-left-color: #667eea;
            font-weight: 600;
        }}
        
        .content {{
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            position: relative;
        }}
        
        .card {{
            background: rgba(31, 41, 55, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 10px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .card h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 20px;
            font-weight: 600;
            padding-bottom: 12px;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, #667eea, #764ba2) 1;
        }}
        
        .card h4 {{
            color: #f3f4f6;
            margin-bottom: 12px;
            font-size: 16px;
            font-weight: 500;
        }}
        
        .card p {{
            color: #9ca3af;
            line-height: 1.6;
            margin-bottom: 12px;
        }}
        
        .card strong {{
            color: #f3f4f6;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .stat-box {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(102, 126, 234, 0.3);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-box:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }}
        
        .stat-box .number {{
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .stat-box .label {{
            color: #9ca3af;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            background: rgba(17, 24, 39, 0.5);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .data-table th {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 2px solid rgba(102, 126, 234, 0.5);
            color: #667eea;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(102, 126, 234, 0.1);
        }}
        
        .data-table td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #d1d5db;
            font-size: 14px;
        }}
        
        .data-table tr:hover {{
            background: rgba(102, 126, 234, 0.08);
        }}
        
        .data-table tr:last-child td {{
            border-bottom: none;
        }}
        
        /* 模态框样式 */
        #modal-overlay label {{
            display: block;
            margin-bottom: 8px;
            font-size: 13px;
            color: #9ca3af;
            font-weight: 500;
        }}
        
        #modal-overlay label + div {{
            color: #e5e7eb;
            font-size: 14px;
        }}
        
        #modal-overlay pre {{
            margin: 0;
            font-size: 13px;
            font-family: 'Courier New', monospace;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .status-badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-success {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: #fff;
        }}
        
        .status-warning {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #fff;
        }}
        
        .status-error {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: #fff;
        }}
        
        /* 移动端适配 */
        @media (max-width: 768px) {{
            body {{
                background: #1a1a2e;
            }}
            
            .container {{
                flex-direction: column;
                height: 100vh;
            }}
            
            .sidebar {{
                width: 100%;
                height: 60px;
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 0;
                box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
                z-index: 1000;
                display: flex;
                justify-content: space-around;
                align-items: center;
                background: #1f2937;
            }}
            
            .sidebar h2 {{
                display: none;
            }}
            
            .menu-item {{
                padding: 8px;
                flex: 1;
                text-align: center;
                border-bottom: 3px solid transparent;
                font-size: 10px;
                color: #9ca3af;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 2px;
            }}
            
            .menu-item:hover {{
                border-bottom-color: #667eea;
                color: #e5e7eb;
            }}
            
            .menu-item.active {{
                border-bottom-color: #667eea;
                background: rgba(102, 126, 234, 0.2);
                color: #fff;
            }}
            
            .content {{
                flex: 1;
                padding: 16px;
                padding-bottom: 70px;
                min-height: calc(100vh - 60px);
                position: relative;
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                width: 100%;
                box-sizing: border-box;
            }}
            
            .stats {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin-bottom: 16px;
            }}
            
            .stat-box {{
                padding: 14px;
            }}
            
            .stat-box .number {{
                font-size: 24px;
            }}
            
            .stat-box .label {{
                font-size: 11px;
            }}
            
            .card {{
                padding: 16px;
                margin-bottom: 16px;
            }}
            
            .card h3 {{
                font-size: 16px;
                margin-bottom: 12px;
                padding-bottom: 8px;
            }}
            
            .data-table {{
                font-size: 11px;
            }}
            
            .data-table th,
            .data-table td {{
                padding: 8px 6px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            
            .card {{
                padding: 14px;
            }}
            
            .card h3 {{
                font-size: 16px;
            }}
            
            .stat-box .number {{
                font-size: 32px;
            }}
        }}
        
        /* 滚动条美化 */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(17, 24, 39, 0.5);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, #764ba2, #667eea);
        }}
        
        /* 链接样式 */
        a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        /* 分页样式 */
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin-top: 20px;
            padding: 16px;
        }}
        
        .pagination button {{
            padding: 8px 16px;
            background: rgba(102, 126, 234, 0.2);
            border: 1px solid rgba(102, 126, 234, 0.5);
            color: #667eea;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 13px;
        }}
        
        .pagination button:hover:not(:disabled) {{
            background: rgba(102, 126, 234, 0.4);
            transform: translateY(-1px);
        }}
        
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .pagination button.active {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-color: transparent;
        }}
        
        .pagination .page-info {{
            color: #9ca3af;
            font-size: 13px;
            margin: 0 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>📊 股票推荐系统</h2>
            <div class="menu-item active" onclick="showPage('dashboard', this)">🏠 仪表盘</div>
            <div class="menu-item" onclick="showPage('recommendations', this)">💡 每日推荐</div>
            <div class="menu-item" onclick="showPage('stocks', this)">📈 股票列表</div>
            <div class="menu-item" onclick="showPage('news', this)">📰 新闻数据</div>
            <div class="menu-item" onclick="showPage('tasks', this)">⏰ 任务日志</div>
            <div class="menu-item" onclick="showPage('settings', this)">⚙️ 系统设置</div>
        </div>
        <div class="content" id="main-content">
            <div class="card">
                <h3>系统加载中...</h3>
                <p>请稍候，正在加载数据...</p>
            </div>
        </div>
        
        <!-- 模态框 -->
        <div id="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); justify-content: center; align-items: center; z-index: 1000;">
            <div id="modal-content" style="background: #1f2937; padding: 24px; border-radius: 12px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);">
            </div>
        </div>
    </div>
    <script>
        const API_BASE = 'http://{host}/api';

        // 分页状态
        let stocksPage = 1;
        let stocksPageSize = 10;
        let recommendationsPage = 1;
        let recommendationsPageSize = 10;
        let tasksPage = 1;
        let tasksPageSize = 10;

        // 推荐日期（默认今天）
        let recommendationDate = new Date().toISOString().split('T')[0];

        async function showPage(page, target) {{
            document.querySelectorAll('.menu-item').forEach(item => {{
                item.classList.remove('active');
            }});
            if (target) {{
                target.classList.add('active');
            }}
            
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
            
            const response3 = await fetch(`${{API_BASE}}/tasks/recent?page=1&page_size=10`);
            const data3 = await response3.json();
            
            const taskLogs = data3.logs || [];
            const lastTasks = taskLogs.slice(0, 3).map(log => `
                <div style="margin-bottom: 10px; padding: 8px; background: rgba(17, 24, 39, 0.3); border-radius: 6px;">
                    <div style="font-size: 13px; font-weight: 500; margin-bottom: 4px;">${{log.task_name}}</div>
                    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <span class="status-badge ${{log.status === 'success' ? 'status-success' : 'status-error'}}">${{log.status}}</span>
                        <span style="font-size: 11px; color: #9ca3af;">${{new Date(log.start_time).toLocaleString('zh-CN')}}</span>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
                <div class="card">
                    <h3>📊 系统概览</h3>
                    <div class="stats">
                        <div class="stat-box">
                            <div class="number">${{data2.total || 0}}</div>
                            <div class="label">今日推荐</div>
                        </div>
                        <div class="stat-box">
                            <div class="number">${{data3.total || 0}}</div>
                            <div class="label">总任务数</div>
                        </div>
                        <div class="stat-box">
                            <div class="number" style="color: #10b981;">${{data3.success || 0}}</div>
                            <div class="label">成功任务</div>
                        </div>
                        <div class="stat-box">
                            <div class="number" style="color: #ef4444;">${{data3.failed || 0}}</div>
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
        
        async function loadRecommendations() {{
            const response = await fetch(`${{API_BASE}}/recommendations/today?date=${{recommendationDate}}&page=${{recommendationsPage}}&page_size=${{recommendationsPageSize}}`);
            const data = await response.json();
            
            const html = data.recommendations.map((rec, i) => `
                <tr>
                    <td>${{(data.page - 1) * data.page_size + i + 1}}</td>
                    <td><strong>${{rec.name}}</strong> (${{rec.ts_code}})</td>
                    <td style="color: ${{rec.predicted_return > 0 ? '#28a745' : '#dc3545'}}">${{rec.predicted_return.toFixed(2)}}%</td>
                    <td>¥${{rec.current_price?.toFixed(2) || 'N/A'}}</td>
                    <td>${{new Date(rec.created_at || recommendationDate).toLocaleString('zh-CN').split(' ')[0]}}</td>
                    <td>${{rec.reasons?.join('<br>') || '无'}}</td>
                </tr>
            `).join('');
            
            // 生成分页HTML
            let paginationHtml = '';
            if (data.total_pages > 1) {{
                const pageButtons = [];
                pageButtons.push(`<button ${{data.page <= 1 ? 'disabled' : ''}} onclick="changeRecommendationsPage(${{data.page - 1}})">上一页</button>`);
                
                let startPage = Math.max(1, data.page - 2);
                let endPage = Math.min(data.total_pages, startPage + 4);
                if (endPage - startPage < 4) {{
                    startPage = Math.max(1, endPage - 4);
                }}
                
                for (let i = startPage; i <= endPage; i++) {{
                    pageButtons.push(`<button class="${{i === data.page ? 'active' : ''}}" onclick="changeRecommendationsPage(${{i}})">${{i}}</button>`);
                }}
                
                pageButtons.push(`<button ${{data.page >= data.total_pages ? 'disabled' : ''}} onclick="changeRecommendationsPage(${{data.page + 1}})">下一页</button>`);
                
                paginationHtml = `
                    <div class="pagination">
                        ${{pageButtons.join('')}}
                        <span class="page-info">${{data.page}} / ${{data.total_pages}} 页，共 ${{data.total}} 条</span>
                    </div>
                `;
            }}
            
            document.getElementById('main-content').innerHTML = `
                <div class="card">
                    <h3>💡 推荐列表</h3>
                    <div style="margin-bottom: 15px; display: flex; gap: 15px; align-items: center;">
                        <label style="font-size: 13px; color: #e5e7eb;">选择日期：</label>
                        <input type="date" id="recommendation-date-input" value="${{recommendationDate}}" 
                            onchange="updateRecommendationDate(this.value)"
                            style="padding: 8px 12px; background: rgba(17, 24, 39, 0.5); border: 1px solid rgba(102, 126, 234, 0.5); color: #e5e7eb; border-radius: 6px; font-size: 14px;">
                        <button onclick="reloadRecommendations()" 
                            style="padding: 8px 16px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">查询</button>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr><th>排名</th><th>股票名称</th><th>预期收益</th><th>当前价格</th><th>推荐日期</th><th>推荐理由</th></tr>
                        </thead>
                        <tbody>${{html || '<tr><td colspan="6">暂无推荐数据</td></tr>'}}</tbody>
                    </table>
                    ${{paginationHtml}}
                </div>`;
        }}
        
        function updateRecommendationDate(date) {{
            recommendationDate = date;
        }}
        
        function reloadRecommendations() {{
            recommendationsPage = 1;
            loadRecommendations();
        }}
        
        function changeRecommendationsPage(page) {{
            recommendationsPage = page;
            loadRecommendations();
        }}
        
        async function loadStocks() {{
            const response = await fetch(`${{API_BASE}}/stocks?page=${{stocksPage}}&page_size=${{stocksPageSize}}`);
            const data = await response.json();
            
            const html = data.stocks.map(stock => `
                <tr>
                    <td><strong>${{stock.name}}</strong> (${{stock.ts_code}})</td>
                    <td>${{stock.industry || 'N/A'}}</td>
                    <td>${{stock.market || 'N/A'}}</td>
                    <td><a href="#" onclick="loadStockDetail('${{stock.ts_code}}'); return false;">查看详情</a></td>
                </tr>
            `).join('');
            
            // 生成分页HTML
            let paginationHtml = '';
            if (data.total_pages > 1) {{
                const pageButtons = [];
                // 上一页按钮
                pageButtons.push(`<button ${{data.page <= 1 ? 'disabled' : ''}} onclick="changeStocksPage(${{data.page - 1}})">上一页</button>`);
                
                // 页码按钮（最多显示5个）
                let startPage = Math.max(1, data.page - 2);
                let endPage = Math.min(data.total_pages, startPage + 4);
                if (endPage - startPage < 4) {{
                    startPage = Math.max(1, endPage - 4);
                }}
                
                for (let i = startPage; i <= endPage; i++) {{
                    pageButtons.push(`<button class="${{i === data.page ? 'active' : ''}}" onclick="changeStocksPage(${{i}})">${{i}}</button>`);
                }}
                
                // 下一页按钮
                pageButtons.push(`<button ${{data.page >= data.total_pages ? 'disabled' : ''}} onclick="changeStocksPage(${{data.page + 1}})">下一页</button>`);
                
                paginationHtml = `
                    <div class="pagination">
                        ${{pageButtons.join('')}}
                        <span class="page-info">${{data.page}} / ${{data.total_pages}} 页，共 ${{data.total}} 条</span>
                    </div>
                `;
            }}
            
            document.getElementById('main-content').innerHTML = `
                <div class="card">
                    <h3>📈 股票列表</h3>
                    <p style="margin-bottom: 12px; color: #9ca3af;">共有 ${{data.total}} 只股票</p>
                    <table class="data-table">
                        <thead>
                            <tr><th>股票名称</th><th>行业</th><th>市场</th><th>操作</th></tr>
                        </thead>
                        <tbody>${{html || '<tr><td colspan="5">暂无股票数据</td></tr>'}}</tbody>
                    </table>
                    ${{paginationHtml}}
                </div>`;
        }}
        
        function changeStocksPage(page) {{
            stocksPage = page;
            loadStocks();
        }}
        
        async function loadStockDetail(ts_code) {{
            const response = await fetch(`${{API_BASE}}/stocks/${{ts_code}}`);
            const data = await response.json();
            
            const pricesHtml = data.prices.slice(0, 20).map(p => `
                <tr>
                    <td>${{p.trade_date}}</td>
                    <td>¥${{p.open?.toFixed(2) || 'N/A'}}</td>
                    <td>¥${{p.high?.toFixed(2) || 'N/A'}}</td>
                    <td>¥${{p.low?.toFixed(2) || 'N/A'}}</td>
                    <td>¥${{p.close?.toFixed(2) || 'N/A'}}</td>
                    <td style="color: ${{p.pct_chg > 0 ? '#28a745' : p.pct_chg < 0 ? '#dc3545' : '#6c757d'}};">${{p.pct_chg?.toFixed(2) || 0}}%</td>
                </tr>
            `).join('');
            
            const newsHtml = data.news.map(n => `
                <div style="margin-bottom: 12px; padding: 10px; background: rgba(17, 24, 39, 0.3); border-radius: 8px;">
                    <h4 style="margin-bottom: 6px;">${{n.title}}</h4>
                    <p style="font-size: 12px; color: #9ca3af; margin-bottom: 6px;">${{new Date(n.pub_date).toLocaleString('zh-CN')}} | 情感: ${{n.sentiment?.toFixed(2) || 'N/A'}}</p>
                    <p style="font-size: 13px; color: #d1d5db;">${{n.content || '无内容'}}</p>
                    ${{n.url ? `<a href="${{n.url}}" target="_blank" style="font-size: 12px;">阅读原文 →</a>` : ''}}
                </div>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>📊 ${{data.stock.name}} (${{data.stock.ts_code}})</h3>
                <div style="margin-bottom: 20px;">
                    <strong>行业:</strong> ${{data.stock.industry || 'N/A'}} | 
                    <strong>市场:</strong> ${{data.stock.market || 'N/A'}}
                </div>
                
                <h4>💰 近20日价格走势</h4>
                <table style="margin-bottom: 24px;">
                    <thead>
                        <tr><th>日期</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>涨跌幅</th></tr>
                    </thead>
                    <tbody>${{pricesHtml || '<tr><td colspan="6">暂无价格数据</td></tr>'}}</tbody>
                </table>
                
                <h4>📰 相关新闻</h4>
                ${{newsHtml || '<p>暂无新闻数据</p>'}}
                
                <div style="margin-top: 20px;">
                    <a href="#" onclick="loadStocks(); return false;" style="color: #667eea;">← 返回列表</a>
                </div>
            </div>`;
        }}
        
        async function loadNews() {{
            const response = await fetch(`${{API_BASE}}/news`);
            const data = await response.json();
            
            const html = data.news.map(news => `
                <div class="card" style="margin-bottom: 15px;">
                    <h4>${{news.title}}</h4>
                    <p style="color: #666; font-size: 12px;">${{new Date(news.pub_time).toLocaleString('zh-CN')}} | ${{news.source || '未知来源'}}</p>
                    <p>${{news.content || news.url || '无内容'}}</p>
                </div>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>📰 新闻数据</h3>
                ${{html || '<p>暂无新闻数据</p>'}}
            </div>`;
        }}
        
        async function loadTasks() {{
            const response = await fetch(`${{API_BASE}}/tasks/recent?page=${{tasksPage}}&page_size=${{tasksPageSize}}`);
            const data = await response.json();

            // 存储当前页的日志数据
            window.currentTaskLogs = data.logs;

            const html = data.logs.map((log, index) => `
                <tr>
                    <td>${{new Date(log.start_time).toLocaleString('zh-CN')}}</td>
                    <td><strong>${{log.task_name}}</strong></td>
                    <td><span class="status-badge ${{log.status === 'success' ? 'status-success' : 'status-error'}}">${{log.status}}</span></td>
                    <td style="max-width: 200px; word-wrap: break-word; overflow: hidden; text-overflow: ellipsis;">${{log.error ? (log.error.length > 50 ? log.error.substring(0, 50) + '...' : log.error) : '-'}}</td>
                    <td><button onclick="showTaskDetail(${{index}})" style="padding: 6px 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">查看</button></td>
                </tr>
            `).join('');

            // 生成分页HTML
            let paginationHtml = '';
            if (data.total_pages > 1) {{
                const pageButtons = [];
                pageButtons.push(`<button ${{data.page <= 1 ? 'disabled' : ''}} onclick="changeTasksPage(${{data.page - 1}})">上一页</button>`);

                let startPage = Math.max(1, data.page - 2);
                let endPage = Math.min(data.total_pages, startPage + 4);
                if (endPage - startPage < 4) {{
                    startPage = Math.max(1, endPage - 4);
                }}

                for (let i = startPage; i <= endPage; i++) {{
                    pageButtons.push(`<button class="${{i === data.page ? 'active' : ''}}" onclick="changeTasksPage(${{i}})">${{i}}</button>`);
                }}

                pageButtons.push(`<button ${{data.page >= data.total_pages ? 'disabled' : ''}} onclick="changeTasksPage(${{data.page + 1}})">下一页</button>`);

                paginationHtml = `
                    <div class="pagination">
                        ${{pageButtons.join('')}}
                        <span class="page-info">${{data.page}} / ${{data.total_pages}} 页，共 ${{data.total}} 条</span>
                    </div>
                `;
            }}

            document.getElementById('main-content').innerHTML = `
                <div class="card">
                    <h3>⏰ 任务日志</h3>
                    <div style="margin-bottom: 15px;">
                        <span>总任务数: ${{data.total || 0}}</span> |
                        <span style="color: #28a745;">成功: ${{data.success || 0}}</span> |
                        <span style="color: #dc3545;">失败: ${{data.failed || 0}}</span>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr><th>时间</th><th>任务名称</th><th>状态</th><th>错误信息</th></tr>
                        </thead>
                        <tbody>${{html || '<tr><td colspan="5">暂无任务日志</td></tr>'}}</tbody>
                    </table>
                    ${{paginationHtml}}
                </div>`;
        }}

        function changeTasksPage(page) {{
            tasksPage = page;
            loadTasks();
        }}
        
        function showTaskDetail(index) {{
            const log = window.currentTaskLogs[index];
            
            document.getElementById('modal-overlay').style.display = 'flex';
            document.getElementById('modal-content').innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                    <h3 style="margin: 0; font-size: 18px;">任务详情</h3>
                    <button onclick="closeModal()" style="background: none; border: none; color: #e5e7eb; font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                
                <div style="display: grid; gap: 15px;">
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">任务名称</label>
                        <div style="font-size: 14px; font-weight: 500;">${{log.task_name}}</div>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">任务类型</label>
                        <div style="font-size: 14px;">${{log.task_type}}</div>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">执行时间</label>
                        <div style="font-size: 14px;">${{new Date(log.start_time).toLocaleString('zh-CN')}}</div>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">状态</label>
                        <span class="status-badge ${{log.status === 'success' ? 'status-success' : 'status-error'}}">${{log.status}}</span>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">执行时长</label>
                        <div style="font-size: 14px;">${{log.duration_seconds ? log.duration_seconds.toFixed(2) + ' 秒' : '-'}}</div>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">执行消息</label>
                        <div style="font-size: 14px; word-wrap: break-word;">${{log.message || '-'}}</div>
                    </div>
                    
                    <div>
                        <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #9ca3af;">错误信息</label>
                        <div style="font-size: 14px; word-wrap: break-word; white-space: pre-wrap; background: rgba(220, 38, 38, 0.1); padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">${{log.error || '-'}}</div>
                    </div>
                </div>
            `;
        }}
        
        function closeModal() {{
            document.getElementById('modal-overlay').style.display = 'none';
        }}
        
        async function loadSettings() {{
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>⚙️ 系统设置</h3>
                
                <div style="margin-bottom: 30px;">
                    <h4>💡 自定义价格范围生成推荐</h4>
                    <p style="color: #9ca3af; margin-bottom: 15px;">根据你设定的股价范围生成新的推荐</p>
                    <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 15px;">
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #e5e7eb;">最低价格 (元)</label>
                            <input type="number" id="min-price" value="0" min="0" step="0.01"
                                style="padding: 10px; width: 150px; background: rgba(17, 24, 39, 0.5); border: 1px solid rgba(102, 126, 234, 0.5); color: #e5e7eb; border-radius: 6px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-size: 13px; color: #e5e7eb;">最高价格 (元)</label>
                            <input type="number" id="max-price" value="15" min="0" step="0.01"
                                style="padding: 10px; width: 150px; background: rgba(17, 24, 39, 0.5); border: 1px solid rgba(102, 126, 234, 0.5); color: #e5e7eb; border-radius: 6px;">
                        </div>
                        <button onclick="generateCustomRecommendations()" 
                            style="padding: 10px 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                            生成推荐
                        </button>
                    </div>
                    <div id="generate-result" style="margin-top: 10px;"></div>
                </div>

                <div style="margin-bottom: 30px;">
                    <h4>📊 数据源配置</h4>
                    <p>当前使用 baostock 接口获取股票数据（免费、无需 Token）</p>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <h4>💾 数据库</h4>
                    <p>MySQL 本地数据库</p>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <h4>⏰ 任务调度</h4>
                    <p>定时任务更新数据并生成推荐（每日凌晨执行）</p>
                </div>
            </div>`;
        }}

        async function generateCustomRecommendations() {{
            const minPrice = document.getElementById('min-price').value;
            const maxPrice = document.getElementById('max-price').value;
            const resultDiv = document.getElementById('generate-result');

            if (parseFloat(minPrice) >= parseFloat(maxPrice)) {{
                resultDiv.innerHTML = '<span style="color: #ef4444;">Error: Min price must be less than max price</span>';
                return;
            }}

            resultDiv.innerHTML = '<span style="color: #667eea;">Generating...</span>';

            try {{
                const response = await fetch(`${{API_BASE}}/recommendations/generate?min_price=${{minPrice}}&max_price=${{maxPrice}}`, {{
                    method: 'POST'
                }});
                const data = await response.json();

                if (data.status === 'success') {{
                    resultDiv.innerHTML = '<span style="color: #10b981;">Success: ' + data.message + ' (Price: CNY' + minPrice + '-' + maxPrice + ')</span>';
                    setTimeout(() => showPage('recommendations', document.querySelector('.menu-item:nth-child(3)')), 2000);
                }} else {{
                    resultDiv.innerHTML = '<span style="color: #ef4444;">Failed: ' + data.message + '</span>';
                }}
            }} catch (error) {{
                resultDiv.innerHTML = '<span style="color: #ef4444;">Error: ' + error.message + '</span>';
            }}
        }}
        
        // 初始加载
        loadDashboard();
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
async def get_today_recommendations(date: str = None, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    """获取推荐（支持日期查询和分页）"""
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取指定日期的推荐
        recs = db.query(Recommendation).filter(
            Recommendation.recommend_date == date
        ).order_by(Recommendation.rank).all()
        
        # 转换为字典
        today = []
        for rec in recs:
            today.append({
                "rank": rec.rank,
                "ts_code": rec.ts_code,
                "name": rec.name,
                "predicted_return": rec.predicted_return,
                "current_price": rec.current_price,
                "target_price": rec.current_price * (1 + rec.predicted_return / 100) if rec.current_price else None,
                "reasons": rec.reasons.split('\\n') if rec.reasons else [],
                "created_at": rec.created_at.isoformat() if rec.created_at else None
            })

        # 计算分页
        total = len(today)
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        paginated = today[offset:offset + page_size]

        return {
            "date": date,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "recommendations": paginated
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
async def generate_recommendations(min_price: float = 0, max_price: float = 15):
    """生成新的推荐（可设置价格范围）"""
    try:
        recs = recommender.generate_recommendations(
            top_n=10,
            min_price=min_price,
            max_price=max_price
        )
        return {
            "status": "success",
            "count": len(recs),
            "price_range": f"¥{min_price}-{max_price}",
            "message": f"成功生成 {len(recs)} 个推荐"
        }
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def list_stocks(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    """获取股票列表（支持分页）"""
    try:
        # 获取总数
        total = db.query(Stock).count()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取当前页数据
        stocks = db.query(Stock).offset(offset).limit(page_size).all()
        
        result = []
        for stock in stocks:
            stock_url = getattr(stock, 'url', None)
            if not stock_url:
                # 自动生成雪球链接
                stock_url = f"https://xueqiu.com/S/{stock.ts_code}"
            
            result.append({
                "ts_code": stock.ts_code,
                "name": stock.name,
                "industry": stock.industry,
                "market": stock.market,
                "url": stock_url
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
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


@app.get("/api/stocks/{ts_code}")
async def get_stock_detail(ts_code: str, db: Session = Depends(get_db)):
    """获取股票详情（价格走势 + 新闻）"""
    try:
        # 获取股票基本信息
        stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"股票 {ts_code} 不存在")
        
        # 获取近20日价格数据
        prices = db.query(StockPrice).filter(
            StockPrice.ts_code == ts_code
        ).order_by(StockPrice.trade_date.desc()).limit(20).all()
        
        prices_list = [{
            "trade_date": p.trade_date,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "vol": p.vol,
            "amount": p.amount,
            "pct_chg": p.pct_chg
        } for p in prices]
        
        # 获取相关新闻（这里简单返回所有新闻，实际可以按股票代码过滤）
        news = db.query(StockNews).order_by(
            StockNews.pub_date.desc()
        ).limit(10).all()
        
        news_list = [{
            "title": n.title,
            "content": n.content,
            "url": n.url,
            "pub_date": n.pub_date.isoformat() if n.pub_date else None,
            "sentiment": n.sentiment
        } for n in news]
        
        return {
            "stock": {
                "ts_code": stock.ts_code,
                "name": stock.name,
                "industry": stock.industry,
                "market": stock.market
            },
            "prices": prices_list,
            "news": news_list
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/recent")
async def get_recent_tasks(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    """获取最近任务日志（支持分页）"""
    try:
        # 获取总数
        total = db.query(func.count(TaskLog.id)).scalar()

        # 计算分页
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # 获取分页数据
        tasks = db.query(TaskLog).order_by(
            TaskLog.start_time.desc()
        ).offset(offset).limit(page_size).all()

        # 统计
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
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
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
