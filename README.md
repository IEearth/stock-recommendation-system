# A股智能推荐系统

基于机器学习的A股股票智能推荐系统，专注于推荐**15元以下**有投资潜力的低价股，适合小额投资者。

## 功能特性

- 📰 **新闻采集**：每日收集财经新闻和相关信息
- 📊 **行情数据**：通过 baostock 获取实时行情和历史数据
- 🧠 **预测模型**：基于历史数据构建预测模型
- 💡 **智能推荐**：每日推荐10只**15元以下**的潜力股票
- 💾 **数据存储**：MySQL 数据库持久化
- 🌐 **Web管理后台**：内置管理界面，查看推荐和系统状态
- 💹 **股票分页**：支持股票列表分页浏览
- 🏥 **健康检查**：定时监控系统状态
- ⏰ **定时任务**：自动化数据更新和推荐生成

## 适用场景

本系统专为以下人群设计：

- 💰 **小额投资者** - 资金有限，适合投资低价股
- 🎯 **价值投资者** - 寻找被低估的优质股
- 📚 **学习研究** - 研究量化投资策略
- 🔬 **数据爱好者** - 分析A股市场数据

## 技术栈

- **后端**: Python 3.8+ + FastAPI
- **前端**: 纯 HTML/CSS/JS（轻量级管理后台）
- **数据库**: MySQL
- **数据源**: baostock（免费、开源）
- **调度**: APScheduler
- **机器学习**: pandas + numpy（统计模型）

## 项目结构

```
stock-recommendation-system/
├── backend/
│   ├── main.py              # FastAPI 主应用（内置Web界面）
│   ├── database.py          # 数据库模型
│   ├── scheduler.py         # 定时任务调度器
│   ├── health_check.py      # 健康检查模块
│   └── models/
│       ├── market_collector_baostock.py  # 行情数据采集（baostock）
│       ├── news_collector.py     # 新闻采集
│       ├── predictor.py          # 预测模型
│       └── recommender.py       # 推荐引擎
├── frontend/               # 前端目录（保留）
├── logs/                  # 日志目录
├── requirements.txt        # Python 依赖
├── .env                   # 环境变量配置
└── README.md            # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/IEearthGEarth/stock-recommendation-system.git
cd stock-recommendation-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `.env` 文件，配置 MySQL 连接：

```env
# 数据库配置（MySQL）
DATABASE_URL=mysql+mysqlconnector://username:password@localhost:3306/stock_recommendation

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
```

### 3. 初始化数据库

```bash
cd backend
python -c "from database import init_db; init_db()"
```

### 4. 采集数据并生成推荐

```bash
cd backend
python run_tasks.py
```

这将执行：
- 更新股票列表（15元以下潜力股）
- 更新行情数据（90天历史）
- 更新新闻数据
- 训练预测模型
- 生成今日推荐

### 5. 启动 Web 服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

访问管理后台：`http://localhost:8000`

### 6. 启动定时任务（可选）

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

响应示例：
```json
{
  "date": "2026-02-27",
  "count": 10,
  "recommendations": [
    {
      "rank": 1,
      "ts_code": "000630.SZ",
      "name": "铜陵有色",
      "predicted_return": 2.38,
      "current_price": 7.59,
      "target_price": 7.77,
      "reasons": ["预测收益率: 2.38%", "当前价格: ¥7.59"]
    }
  ]
}
```

### 获取股票列表（支持分页）
```http
GET /api/stocks?page=1&page_size=10
```

### 获取系统状态
```http
GET /api/system/status
```

## 核心逻辑

### 股票筛选标准

系统只关注**15元以下**的股票，原因：

1. **门槛低** - 小额投资者更容易参与
2. **空间大** - 低价股上涨空间相对较大
3. **流动性好** - 成交活跃，便于买卖

### 推荐算法

基于历史数据的统计分析：

1. **动量分析** - 分析近期价格走势
2. **波动率评估** - 评估风险水平
3. **趋势判断** - 判断上涨趋势
4. **置信度计算** - 评估预测可靠性

### 风险提示

⚠️ **重要声明**：

1. 本系统仅供学习和研究使用
2. **不构成任何投资建议**
3. 股票投资有风险，入市需谨慎
4. 预测结果仅供参考，不保证准确性
5. 请根据个人风险承受能力做投资决策

## 数据源说明

### baostock

- **优点**：
  - ✅ 完全免费，无需 API Token
  - ✅ 开源社区维护
  - ✅ 数据质量可靠
  - ✅ 接口简单易用

- **数据范围**：
  - A股历史行情
  - 基本面数据
  - 财务数据

## 定时任务

系统可配置以下定时任务：

- **健康检查**：每 20 分钟执行一次
- **数据更新**：每天定时执行
  - 更新股票列表
  - 更新行情数据（90天）
  - 更新新闻数据
  - 训重新练预测模型
  - 生成今日推荐

## 数据库表结构

### stocks
股票基本信息（代码、名称、行业）

### stock_prices
股票行情数据（开高低收、成交量、涨跌幅）

### stock_news
股票新闻数据

### recommendations
每日推荐股票（预期收益、理由）

### system_health
系统健康状态

### task_logs
任务执行日志

## 开发说明

### 手动生成推荐

```bash
cd backend
python -c "from models.recommender import StockRecommender; StockRecommender().generate_recommendations()"
```

### 健康检查

```bash
cd backend
python health_check.py
```

### 查看数据库

```bash
cd backend
python -c "
from database import SessionLocal, Stock, Recommendation
db = SessionLocal()
print('股票数量:', db.query(Stock).count())
print('今日推荐:', db.query(Recommendation).filter(Recommendation.recommend_date == '2026-02-27').count())
"
```

## 常见问题

### 1. 为什么只推荐15元以下的股票？

这是系统设计的核心策略：
- 降低投资门槛
- 适合小额资金参与
- 低价股往往有更大的上涨空间

### 2. 预测准确率如何？

系统使用统计分析方法，基于历史数据预测。但：
- 股市受多种因素影响（政策、市场情绪等）
- 历史不代表未来
- 请将预测结果作为参考，不要作为决策依据

### 3. 如何添加自定义股票？

编辑 `backend/models/market_collector_baostock.py`，在 `fetch_stock_list()` 方法中添加：

```python
stocks = [
    ('sh.600000', '600000.SH', '浦发银行', '金融'),
    # 添加你的股票
    ('sh.xxxxxx', 'xxxxx.SH', '股票名称', '行业'),
]
```

### 4. 数据更新频率？

- 行情数据：建议每日更新
- 新闻数据：建议每日更新
- 推荐生成：每日凌晨自动生成

## 贡献

欢迎提交 Issue 和 Pull Request！

建议方向：
- 优化预测算法
- 增加更多数据源
- 完善风险控制
- 改进可视化

## 许可证

MIT License

## 联系方式

- GitHub: https://github.com/IEearthGEarth/stock-recommendation-system
- Email: 945930900@qq.com

---

**免责声明**：本系统所有内容仅供学习交流使用，不构成投资建议。投资有风险，入市需谨慎！
