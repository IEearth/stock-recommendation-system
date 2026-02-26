# A股智能推荐系统

基于机器学习的A股股票智能推荐系统，每日收集新闻、行情数据，分析预测并推荐10只优质股票。

## 功能特性

- 📰 **新闻采集**：每日收集财经新闻和相关信息
- 📊 **行情数据**：通过 Tushare Pro 获取实时行情和历史数据
- 🧠 **预测模型**：使用 scikit-learn 构建预测模型
- 💡 **智能推荐**：每日推荐10只潜力股票
- 💾 **数据存储**：SQLite 数据库持久化
- 🌐 **API服务**：FastAPI 提供 RESTful API
- 🏥 **健康检查**：定时监控系统状态
- ⏰ **定时任务**：自动化数据更新和推荐生成

## 技术栈

- **后端**: Python 3.10+ + FastAPI
- **前端**: React + Ant Design
- **数据库**: SQLite (可迁移至 PostgreSQL)
- **数据源**: Tushare Pro
- **调度**: APScheduler
- **机器学习**: scikit-learn + pandas + numpy

## 项目结构

```
stock-recommendation-system/
├── backend/
│   ├── main.py              # FastAPI 主应用
│   ├── database.py          # 数据库模型
│   ├── scheduler.py         # 定时任务调度器
│   ├── health_check.py      # 健康检查模块
│   └── models/
│       ├── market_collector.py    # 行情数据采集
│       ├── news_collector.py     # 新闻采集
│       ├── predictor.py          # 预测模型
│       └── recommender.py       # 推荐引擎
├── frontend/               # React 前端（待开发）
├── logs/                  # 日志目录
├── requirements.txt        # Python 依赖
├── .env.example         # 环境变量模板
└── README.md            # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/IEearth/stock-recommendation-system.git
cd stock-recommendation-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入 Tushare Token
# TUSHARE_TOKEN=your_token_here
```

**获取 Tushare Token**：
1. 访问 https://tushare.pro
2. 注册账号
3. 在个人中心获取 API Token

### 3. 初始化数据库

```bash
cd backend
python database.py
```

### 4. 采集数据

```bash
# 更新股票列表
python -c "from models.market_collector import MarketCollector; MarketCollector().update_stock_list()"

# 更新行情数据
python -c "from models.market_collector import MarketCollector; MarketCollector().update_daily_quotes(days=30)"

# 更新新闻数据
python -c "from models.news_collector import NewsCollector; NewsCollector().update_news()"
```

### 5. 启动 API 服务

```bash
cd backend
python main.py
```

API 将在 `http://localhost:8000` 启动

访问文档：`http://localhost:8000/docs`

### 6. 启动定时任务

```bash
cd backend
python scheduler.py
```

## API 接口

### 健康检查
```http
GET /health
```

### 获取今日推荐
```http
GET /api/recommendations/today
```

### 获取历史推荐
```http
GET /api/recommendations/history?days=7
```

### 生成新推荐
```http
POST /api/recommendations/generate
```

### 获取股票列表
```http
GET /api/stocks
```

### 系统状态
```http
GET /api/system/status
```

## 定时任务

系统配置了以下定时任务：

- **健康检查**：每 20 分钟执行一次
- **数据更新**：每天凌晨 02:00 执行
  - 更新股票列表
  - 更新行情数据
  - 更新新闻数据
  - 训练预测模型
  - 生成今日推荐

## 数据库表结构

### stocks
股票基本信息

### stock_prices
股票行情数据

### stock_news
股票新闻

### stock_predictions
股票预测结果

### recommendations
每日推荐股票

### system_health
系统健康状态

## 开发说明

### 手动生成推荐

```bash
python -c "from models.recommender import StockRecommender; StockRecommender().generate_recommendations()"
```

### 健康检查

```bash
python health_check.py
```

## 注意事项

⚠️ **重要提示**：

1. 本系统仅供学习和研究使用，不构成投资建议
2. 股票投资有风险，预测结果仅供参考
3. 请遵守 Tushare Pro 的 API 使用规范
4. 定期备份数据库文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: https://github.com/IEearthGEarth/stock-recommendation-system
- Email: 945930900@qq.com
