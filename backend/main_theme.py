"""
FastAPI 主应用 - 带主题切换功能
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, Recommendation, StockPrediction, SystemHealth, TaskLog, Stock, StockPrice, StockNews

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A股智能推荐系统API")

# CORS 配置
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
    """应用启动事件"""
    logger.info("初始化数据库...")
    init_db()
    logger.info("系统启动完成！")
    
    # 初始化推荐器
    global recommender
    try:
        from models.recommender import StockRecommender
        recommender = StockRecommender()
    except Exception as e:
        logger.warning(f"推荐器初始化失败: {e}")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """管理后台首页"""
    host = request.headers.get('host', 'localhost:8000')
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股智能推荐系统 - 管理后台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        /* CSS 变量定义 - 默认暗色主题 */
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --sidebar-bg-start: #1f2937;
            --sidebar-bg-end: #111827;
            --card-bg: rgba(31, 41, 55, 0.8);
            --card-border: rgba(255,255,255, 0.05);
            --text-primary: #e2e8f0;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent-primary: #667eea;
            --accent-secondary: #764ba2;
            --stat-box-bg: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
            --stat-box-border: rgba(102, 126, 234, 0.3);
            --hover-bg: rgba(102, 126, 234, 0.08);
            --table-bg: rgba(17, 24, 39, 0.5);
            --table-border: rgba(255,255, 255, 0.05);
            --sidebar-text: #f3f4f6;
            --shadow-color: rgba(0, 0, 0, 0.3);
            --gradient-start: #1a1a2e;
            --gradient-end: #16213e;
        }}
        
        /* 亮色主题 */
        [data-theme="light"] {{
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --sidebar-bg-start: #ffffff;
            --sidebar-bg-end: #f1f5f9;
            --card-bg: rgba(255,255, 255, 0.95);
            --card-border: rgba(0, 0, 0, 0.1);
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --accent-primary: #667eea;
            --accent-secondary: #764ba2;
            --stat-box-bg: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            --stat-box-border: rgba(102, 126, 234, 0.2);
            --hover-bg: rgba(102, 126, 234, 0.05);
            --table-bg: rgba(241, 245, 249, 0.8);
            --table-border: rgba(0, 0, 0, 0.1);
            --sidebar-text: #1e293b;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --gradient-start: #f0f4f8;
            --gradient-end: #e2e8f0;
        }}
        
        /* 跟随系统主题 */
        @media (prefers-color-scheme: light) {{
            :root:not([data-theme="dark"]) {{
                --bg-primary: #f8fafc;
                --bg-secondary: #ffffff;
                --sidebar-bg-start: #ffffff;
                --sidebar-bg-end: #f1f5f9;
                --card-bg: rgba(255,255, 255, 0.95);
                --card-border: rgba(0, 0, 0, 0.1);
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --text-muted: #94a3b8;
                --table-bg: rgba(241, 245, 249, 0.8);
                --table-border: rgba(0, 0, 0, 0.1);
                --sidebar-text: #1e293b;
                --shadow-color: rgba(0, 0, 0, 0.1);
                --gradient-start: #f0f4f8;
                --gradient-end: #e2e8f0;
            }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        
        .container {{
            display: flex;
            min-height: 100vh;
        }}
        
        .sidebar {{
            width: 260px;
            background: linear-gradient(180deg, var(--sidebar-bg-start) 0%, var(--sidebar-bg-end) 100%);
            color: var(--sidebar-text);
            padding: 24px 0;
            box-shadow: 4px 0 24px var(--shadow-color);
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            transition: background 0.3s ease;
        }}
        
        .sidebar h2 {{
            padding: 0 24px 24px;
            font-size: 18px;
            font-weight: 700;
            border-bottom: 1px solid var(--card-border);
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
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
            color: var(--text-secondary);
        }}
        
        .menu-item:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: var(--text-primary);
            border-left-color: var(--accent-primary);
        }}
        
        .menu-item.active {{
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.2), transparent);
            color: var(--text-primary);
            border-left-color: var(--accent-primary);
            font-weight: 600;
        }}
        
        .content {{
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            position: relative;
        }}
        
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px var(--shadow-color), 0 10px 20px var(--shadow-color);
            border: 1px solid var(--card-border);
            transition: background 0.3s ease, border-color 0.3s ease;
        }}
        
        .card h3 {{
            color: var(--accent-primary);
            margin-bottom: 20px;
            font-size: 20px;
            font-weight: 600;
            padding-bottom: 12px;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) 1;
        }}
        
        .card h4 {{
            color: var(--text-primary);
            margin-bottom: 12px;
            font-size: 16px;
            font-weight: 500;
        }}
        
        .card p {{
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 12px;
        }}
        
        .card strong {{
            color: var(--text-primary);
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .stat-box {{
            background: var(--stat-box-bg);
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--stat-box-border);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-box:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }}
        
        .stat-box .number {{
            font-size: 36px;
            font-weight: 700;
            color: var(--accent-primary);
            margin-bottom: 8px;
        }}
        
        .stat-box .label {{
            color: var(--text-secondary);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            background: var(--table-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .data-table th {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 2px solid rgba(102, 126, 234, 0.5);
            color: var(--accent-primary);
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(102, 126, 234, 0.1);
        }}
        
        .data-table td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid var(--table-border);
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .data-table tr:hover {{
            background: var(--hover-bg);
        }}
        
        .data-table tr:last-child td {{
            border-bottom: none;
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
        
        /* 主题切换按钮 */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1001;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 50px;
            padding: 10px;
            cursor: pointer;
            box-shadow: 0 4px 6px var(--shadow-color);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .theme-toggle svg {{
            width: 24px;
            height: 24px;
            fill: var(--text-primary);
        }}
        
        /* 移动端适配 */
        @media (max-width: 768px) {{
            body {{
                background: var(--bg-primary);
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
                background: var(--sidebar-bg-start);
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
                color: var(--text-secondary);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 2px;
            }}
            
            .menu-item:hover {{
                border-bottom-color: var(--accent-primary);
                color: var(--text-primary);
            }}
            
            .menu-item.active {{
                border-bottom-color: var(--accent-primary);
                background: rgba(102, 126, 234, 0.2);
                color: var(--text-primary);
            }}
            
            .content {{
                flex: 1;
                padding: 16px;
                padding-bottom: 80px;
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
            
            .stat-box .number{{
                font-size: 24px;
            }}
            
            .card {{
                padding: 14px;
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
            
            .theme-toggle {{
                top: 10px;
                right: 10px;
                padding: 8px;
            }}
            
            .theme-toggle svg {{
                width: 20px;
                height: 20px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            
            .card {{
                padding: 12px;
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
            background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 4px;
        }}
        
        /* 链接样式 */
        a {{
            color: var(--accent-primary);
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        a:hover {{
            color: var(--accent-secondary);
            text-decoration: underline;
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
    </div>
    
    <!-- 主题切换按钮 -->
    <div class="theme-toggle" onclick="toggleTheme()" id="themeToggle" title="切换主题">
        <svg id="themeIcon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
        </svg>
    </div>
    
    <script>
        const API_BASE = 'http://{host}/api';
        
        // 主题管理
        let currentTheme = localStorage.getItem('theme') || 'auto';
        
        function applyTheme(theme) {{
            if (theme === 'auto') {{
                document.documentElement.removeAttribute('data-theme');
            }} else {{
                document.documentElement.setAttribute('data-theme', theme);
            }}
            updateThemeIcon(theme);
        }}
        
        function updateThemeIcon(theme) {{
            const svg = document.getElementById('themeIcon');
            if (theme === 'light' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: light)').matches)) {{
                svg.innerHTML = '<path d="M20.354 15.354A9 9 0 018 9v4.586l3.293-3.293a1 1 0 001.414 1.414l-1 1a1 1 0 01-1.414 0l-2.293-2.293V21a1 1 0 01-1 1h-4a1 1 0 01-1-1v-2.586l-2.293 2.293a1 1 0 01-1.414 0l-1-1a1 1 0 010 1.414l3.293 3.293V15a9 9 0 01-9-9zm-6-10a7 7 0 100-14 0 7 7 0 0014 0z"/>';
            }} else {{
                svg.innerHTML = '<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>';
            }}
        }}
        
        function toggleTheme() {{
            const themes = ['auto', 'dark', 'light'];
            const currentIndex = themes.indexOf(currentTheme);
            current = (currentIndex + 1) % themes.length;
            currentTheme = themes[currentIndex];
            
            localStorage.setItem('theme', currentTheme);
            applyTheme(currentTheme);
            
            // 显示提示
            showToast(`主题切换为: ${{getThemeName(currentTheme)}}`);
        }}
        
        function getThemeName(theme) {{
            switch(theme) {{
                case 'auto': return '自动';
                case 'dark': return '暗色';
                case 'light': return '亮色';
                default: return theme;
            }}
        }}
        
        function showToast(message) {{
            const toast = document.createElement('div');
            toast.style.cssText = 'position:fixed; top:80px; right:20px; background:rgba(102,126,234,0.9); color:white; padding:12px 20px; border-radius:8px; z-index:9999; animation: fadeIn 0.3s;';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 2000);
        }}
        
        // 初始化主题
        applyTheme(currentTheme);
        
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
            
            const response3 = await fetch(`${{API_BASE}}/tasks/recent?limit=10`);
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
                            <div class="number">${{data2.count}}</div>
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
            const response = await fetch(`${{API_BASE}}/recommendations/today`);
            const data = await response.json();
            
            const html = data.recommendations.map((rec, i) => `
                <tr>
                    <td>${{i + 1}}</td>
                    <td><strong>${{rec.name}}</strong> (${{rec.ts_code}})</td>
                    <td style="color: ${{rec.predicted_return > 0 ? '#10b981' : '#ef4444'}}">${{rec.predicted_return.toFixed(2)}}%</td>
                    <td>¥${{rec.current_price?.toFixed(2) || 'N/A'}}</td>
                    <td>${{rec.reasons?.join('<br>') || '无'}}</td>
                </tr>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>💡 今日推荐 (${{data.date}})</h3>
                <table>
                    <thead>
                        <tr><th>排名</th><th>股票名称</th><th>预期收益</th><th>当前价格</th><th>推荐理由</th></tr>
                    </thead>
                    <tbody>${{html || '<tr><td colspan="5">暂无推荐数据</td></tr>'}}</tbody>
                </table>
            </div>`;
        }}
        
        async function loadStocks() {{
            const response = await fetch(`${{API_BASE}}/stocks`);
            const data = await response.json();
            
            const html = data.stocks.map(stock => `
                <tr>
                    <td><strong>${{stock.name}}</strong> (${{stock.ts_code}})</td>
                    <td>${{stock.industry || 'N/A'}}</td>
                    <td>${{stock.market || 'N/A'}}</td>
                    <td><a href="${{stock.url}}" target="_blank">查看详情</a></td>
                </tr>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>📈 股票列表</h3>
                <p style="margin-bottom: 12px; color: #9ca3af;">共有 ${{data.count}} 只股票</p>
                <table>
                    <thead>
                        <tr><th>股票名称</th><th>行业</th><th>市场</th><th>操作</th></tr>
                    </thead>
                    <tbody>${{html || '<tr><td colspan="4">暂无股票数据</td></tr>'}}</tbody>
                </table>
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
            const response = await fetch(`${{API_BASE}}/tasks/recent?limit=50`);
            const data = await response.json();
            
            const html = data.logs.map(log => `
                <tr>
                    <td>${{new Date(log.start_time).toLocaleString('zh-CN')}}</td>
                    <td><strong>${{log.task_name}}</strong></td>
                    <td><span class="status-badge ${{log.status === 'success' ? 'status-success' : 'status-error'}}">${{log.status}}</span></td>
                    <td>${{log.error_message || '-'}}</td>
                </tr>
            `).join('');
            
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>⏰ 任务日志</h3>
                <div style="margin-bottom: 15px;">
                    <span>总任务数: ${{data.total || 0}}</span> |
                    <span style="color: #10b981;">成功: ${{data.success || 0}}</span> |
                    <span style="color: #ef4444;">失败: ${{data.failed || 0}}</span>
                </div>
                <table>
                    <thead>
                        <tr><th>时间</th><th>任务名称</th><th>状态</th><th>错误信息</th></tr>
                    </thead>
                    <tbody>${{html || '<tr><td colspan="4">暂无任务日志</td></tr>'}}</tbody>
                </table>
            </div>`;
        }}
        
        async function loadSettings() {{
            document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h3>⚙️ 系统设置</h3>
                <h4>主题设置</h4>
                <p>当前主题: <strong>${{getThemeName(currentTheme)}}</strong></p>
                <p>点击右上角按钮可在 <strong>自动/暗色/亮色</strong> 之间切换</p>
                <h4>数据源配置</h4>
                <p>当前使用 Tushare 接口获取股票数据</p>
                <h4>数据库</h4>
                <p>MySQL 本地数据库</p>
                <h4>任务调度</h4>
                <p>Celery Beat 定时任务 (每日早上9:00生成推荐)</p>
                <div style="margin-top: 20px; padding: 15px; background: rgba(102, 126, 234, 0.1); border-radius: 5px;">
                    <strong>提示:</strong> 更多配置请修改 .env 文件或联系管理员
                </div>
            </div>`;
        }}
        
        // 初始加载
        loadDashboard();
        
        // 自动刷新
        setInterval(loadDashboard, 30000);
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}`;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""


# API endpoints
@app.get("/api/recommendations/today")
async def get_today_recommendations(db: Session = Depends(get_db)):
    """获取今日推荐"""
    try:
        if recommender:
            today = recommender.get_today_recommendations(db)
        else:
            today = db.query(Recommendation).filter(
                Recommendation.recommend_date == datetime.now().strftime('%Y-%m-%d')
            ).all()
            today = [{
                "rank": rec.rank,
                "ts_code": rec.ts_code,
                "name": rec.name,
                "predicted_return": rec.predicted_return,
                "current_price": rec.current_price,
                "reasons": rec.reasons.split('\\n') if rec.reasons else []
            } for rec in today]
        
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
        if recommender:
            recs = recommender.generate_recommendations(top_n=10)
        else:
            recs = []
        return {
            "status": "success",
            "count": len(recs),
            "message": f"成功生成 {len(recs)} 个推荐"
        }
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def get_stocks(db: Session = Depends(get_db)):
    """获取股票列表"""
    try:
        stocks = db.query(Stock).order_by(Stock.ts_code).all()
        return {
            "count": len(stocks),
            "stocks": [{
                "ts_code": stock.ts_code,
                "name": stock.name,
                "industry": stock.industry,
                "market": stock.market,
                "url": stock.url,
                "updated_at": stock.updated_at.isoformat() if stock.updated_at else None
            } for stock in stocks]
        }
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news")
async def get_news(db: Session = Depends(get_db)):
    """获取新闻数据"""
    try:
        news = db.query(StockNews).order_by(StockNews.pub_date.desc()).limit(50).all()
        return {
            "count": len(news),
            "news": [{
                "title": item.title,
                "content": item.content,
                "url": item.url,
                "pub_time": item.pub_date.isoformat() if item.pub_date else None,
                "sentiment": item