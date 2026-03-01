# A股智能推荐系统

基于机器学习的A股股票智能推荐系统，专注于推荐**15元以下**有投资潜力的低价股，适合小额投资者。

## 功能特性

- 📰 **新闻采集**：每日收集财经新闻和相关信息（支持东方财富、新浪财经财经新闻API）
- 📊 **行情数据**：通过 baostock 获取实时行情和历史数据
- 🧠 **预测模型**：基于历史数据构建预测模型
- 💡 **智能推荐**：每日推荐10只**15元以下**的潜力股票（仅在交易日执行）
- 📅 **交易日感知**：自动识别A股交易日，非交易日自动跳过推荐任务
- 😊 **情感分析**：自动对新闻进行情感打分（正面/负面/中性）
- 💾 **数据存储**：MySQL 数据库持久化
- 🌐 **Web管理后台**：内置管理界面，查看推荐和系统状态
- 💹 **股票分页**：支持股票列表分页浏览
- 📄 **新闻分页**：支持新闻列表分页和情感筛选
- 🏥 **健康检查**：定时监控系统状态（智能判断交易日无推荐情况）
- ⏰ **定时任务**：自动化数据更新和推荐生成（交易日智能调度）
- 🔧 **强制执行**：支持手动强制执行推荐任务（忽略交易日检查）

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
- **数据源**: baostock（免费、开源）+ 东方财富/新浪财经新闻API
- **调度**: APScheduler
- **机器学习**: pandas + numpy（统计模型）
- **情感分析**: SnowNLP / 关键词分析
- **交易日历**: Tushare / 本地节假日缓存

## 项目结构

```
stock-recommendation-system/
├── backend/
│   ├── main.py              # FastAPI 主应用（内置Web界面）
│   ├── database.py          # 数据库模型
│   ├── scheduler.py         # 定时任务调度器（交易日感知）
│   ├── health_check.py      # 健康检查模块
│   ├── run_tasks.py         # 手动执行任务
│   ├── test_improvements.py # 优化功能测试
│   ├── utils/
│   │   ├── __init__.py
│   │   └── trading_day_checker.py  # 交易日判断模块
│   └── models/
│       ├── market_collector_baostock.py  # 行情数据采集（baostock）
│       ├── news_collector.py     # 新闻采集（真实API+情感分析）
│       ├── predictor.py          # 预测模型
│       └── recommender.py       # 推荐引擎（交易日感知）
├── frontend/               # 前端目录（保留）
├── logs/                  # 日志目录
├── requirements.txt        # Python 依赖
├── .env                   # 环境变量配置
├── OPTIMIZATION_SUMMARY.md # 优化总结文档
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

# 可选：安装SnowNLP（中文情感分析）
pip install snownlp

# 可选：安装Tushare（专业交易日历，需要注册）
pip install tushare
```

### 2. 配置数据库和环境

编辑 `.env` 文件：

```env
# 数据库配置（MySQL）
DATABASE_URL=mysql+mysqlconnector://username:password@localhost:3306/stock_recommendation

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO

# 使用真实新闻API
USE_REAL_NEWS_API=true

# Tushare Token（可选，用于更准确的交易日历）
TUSHARE_TOKEN=your_token_here
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
- 更新新闻数据（真实API）
- 训练预测模型
- 生成今日推荐（仅在交易日）

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

### 获取今日推荐（支持分页和日期查询）
```http
GET /api/recommendations/today?date=2026-02-27&page=1&page_size=10
```

### 获取历史推荐
```http
GET /api/recommendations/history?days=7
```

### 手动生成推荐（支持强制执行）
```http
POST /api/recommendations/generate?min_price=0&max_price=15&force=true
```

### 获取股票列表（支持分页）
```http
GET /api/stocks?page=1&page_size=10
```

### 获取股票详情
```http
GET /api/stocks/600000.SH
```

### 获取新闻列表（支持分页和情感筛选）
```http
GET /api/news?page=1&page_size=20&stock_code=600000&sentiment_label=positive
```

### 检查交易日
```http
GET /api/trading-day?date=2026-02-28
```

### 获取系统状态
```http
GET /api/system/status
```

### 获取任务日志（支持分页）
```http
GET /api/tasks/recent?page=1&page_size=10
```

## 核心逻辑

### 股票筛选标准

系统只关注**15元以下**的股票，原因：

1. **门槛低** - 小额投资者更容易参与
2. **空间大** - 低价股上涨空间相对较大
3. **流动性好** - 成交活跃，便于买卖

### 交易日感知

系统智能识别A股交易日：

- 自动识别周末（周六、周日）
- 支持节假日判断（使用Tushare或本地缓存）
- 非交易日自动跳过推荐任务
- 支持强制执行（用于测试和特殊情况）

```python
from utils.trading_day_checker import get_trading_day_checker

checker = get_trading_day_checker()
is_trading = checker.is_trading_day()  # True/False
next_trading = checker.get_next_trading_day()  # datetime
```

### 推荐算法

基于历史数据的统计分析：

1. **动量分析** - 分析近期价格走势
2. **波动率评估** - 评估风险水平
3. **趋势判断** - 判断上涨趋势
4. **置信度计算** - 评估预测可靠性

### 新闻情感分析

自动对新闻标题和内容进行情感分析：

- 使用 SnowNLP 进行中文情感分析
- 降级使用关键词分析方法
- 情感得分范围：-1 到 1
- 情感标签：positive/negative/neutral

## 定时任务

系统可配置以下定时任务：

- **健康检查**：每 20 分钟执行一次
- **交易日数据更新**：每天 09:30（仅在交易日）
  - 更新股票列表
  - 更新行情数据（90天）
  - 训练预测模型
  - 生成今日推荐
- **新闻更新**：每天 02:00（不限交易日）

## 风险提示

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

### 新闻数据源

1. **东方财富网**（优先）
   - 实时财经新闻API
   - 时效性强

2. **新浪财经**（备用）
   - 滚动新闻页面
   - 实时更新

3. **模拟数据**（降级）
   - 当真实API失败时使用

## 数据库表结构

### stocks
股票基本信息（代码、名称、行业）

### stock_prices
股票行情数据（开高低收、成交量、涨跌幅）

### stock_news
股票新闻数据（标题、内容、情感得分）

### recommendations
每日推荐股票（预期收益、理由）

### system_health
系统健康状态

### task_logs
任务执行日志

## 开发说明

### 测试优化功能

```bash
cd backend
python test_improvements.py
```

### 手动生成推荐

```bash
cd backend
python -c "from models.recommender import StockRecommender; StockRecommender().generate_recommendations()"
```

### 强制生成推荐（忽略交易日检查）

```bash
cd backend
python -c "from models.recommender import StockRecommender; StockRecommender().generate_recommendations(force=True)"
```

### 检查交易日

```bash
cd backend
python -c "from utils.trading_day_checker import get_trading_day_checker; c = get_trading_day_checker(); print(c.is_trading_day())"
```

### 健康检查

```bash
cd backend
python health_check.py
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

- 行情数据：建议每日更新（交易日）
- 新闻数据：建议每日更新
- 推荐生成：每日自动生成（交易日09:30）

### 5. 非交易日会执行推荐吗？

不会。系统会自动识别交易日：
- 周末（周六、周日）自动跳过
- 节假日自动跳过
- 只有交易日才会执行推荐任务

如需强制执行，可使用 `force=True` 参数。

## 最新优化 (2026-02-28)

### 1. 交易日感知 ✅
- 自动识别A股交易日
- 非交易日自动跳过推荐任务
- 支持强制执行选项

### 2. 新闻数据真实化 ✅
- 支持东方财富网真实API
- 支持新浪财经真实API
- 自动降级到模拟数据

### 3. 新闻情感分析 ✅
- 集成 SnowNLP 中文情感分析
- 降级到关键词分析方法
- 情感标签：positive/negative/neutral

### 4. 新闻分页API ✅
- 支持分页查询
- 支持情感筛选
- 支持股票代码筛选

详情见 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)

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
