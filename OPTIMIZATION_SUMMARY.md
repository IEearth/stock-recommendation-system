# 股票推荐系统优化总结

## 优化时间
2026-02-28

## 优化目标
1. **优化股票推荐逻辑 - 只在交易日执行**
2. **新闻数据真实化 + 分页**

---

## 1. 交易日判断模块 ✅

### 新增文件
- `/backend/utils/trading_day_checker.py` - 交易日判断核心模块

### 功能特性
- ✅ 支持 Tushare API 获取交易日历（优先）
- ✅ 本地节假日缓存作为降级方案
- ✅ 自动识别周末（周六、周日）
- ✅ 支持获取上一个/下一个交易日
- ✅ 支持获取日期范围内的所有交易日
- ✅ 提供 `should_run_today()` 方法判断是否应该执行任务
- ✅ 支持强制执行选项（忽略交易日检查）

### 核心方法
```python
from utils.trading_day_checker import get_trading_day_checker

checker = get_trading_day_checker()

# 判断是否为交易日
is_trading = checker.is_trading_day(datetime.now())

# 获取下一个交易日
next_trading = checker.get_next_trading_day()

# 判断是否应该执行
should_run, reason = checker.should_run_today(force=False)
```

### 本地节假日数据
- 手动维护了 2024-2027 年的中国主要节假日
- 包括春节、清明、五一、端午、中秋、国庆等

---

## 2. 推荐逻辑优化 ✅

### 修改文件
- `/backend/models/recommender.py` - 推荐引擎

### 优化内容
- ✅ 集成交易日检查器
- ✅ 在生成推荐前检查是否为交易日
- ✅ 非交易日自动跳过并记录日志
- ✅ 支持 `force=True` 强制执行（用于测试或手动触发）
- ✅ 提供清晰的跳过原因说明

### 使用示例
```python
from models.recommender import StockRecommender

recommender = StockRecommender()

# 正常生成（会检查交易日）
recs = recommender.generate_recommendations(top_n=10, force=False)

# 强制生成（忽略交易日）
recs = recommender.generate_recommendations(top_n=10, force=True)

# 检查是否应该运行
should_run, reason = recommender.should_run_today()
```

---

## 3. 调度器逻辑优化 ✅

### 修改文件
- `/backend/scheduler.py` - 定时任务调度器

### 优化内容
- ✅ 集成交易日检查器
- ✅ 模型训练任务只在交易日执行
- ✅ 推荐生成任务只在交易日执行
- ✅ 新闻更新任务不限制交易日（每天执行）
- ✅ 健康检查智能判断：如果是交易日但无推荐，标记为警告
- ✅ 调整调度时间：交易日任务移至 09:30（开盘时间）

### 调度配置
```python
# 每20分钟健康检查
- health_check: 每20分钟

# 每日交易日数据更新（仅交易日）
- daily_trading_update: 每天 09:30 (仅交易日)

# 每日新闻更新（不限交易日）
- daily_news_update: 每天 02:00
```

---

## 4. 新闻数据真实化 ✅

### 修改文件
- `/backend/models/news_collector.py` - 新闻数据采集器

### 新增功能
- ✅ 支持从东方财富网获取真实新闻
- ✅ 支持从新浪财经获取滚动新闻
- ✅ 自动数据清洗和去重（基于标题）
- ✅ 新闻情感分析（支持 SnowNLP 和简单关键词分析）
- ✅ 情感标签分类（positive/negative/neutral）
- ✅ 支持模拟数据降级

### 情感分析
```python
# 使用 SnowNLP（需安装）
from snownlp import SnowNLP
s = SnowNLP("文本")
score = s.sentiments  # 0-1，转换到 -1 到 1

# 或使用简单关键词分析
# 正面：增长、上涨、利好、突破、创新...
# 负面：下跌、亏损、风险、下滑、暴跌...
```

### 新闻数据源
1. **东方财富网**（优先）
   - API: `http://api.eastmoney.com/aapi/st/cgt/list/...`
   - 实时财经新闻数据

2. **新浪财经**（备用）
   - 滚动新闻页面
   - 时效性强

3. **模拟数据**（降级）
   - 当真实API失败时使用

---

## 5. 新闻分页 API ✅

### 新增方法
```python
def get_news_by_page(self, page=1, page_size=20, stock_code=None,
                     sentiment_label=None, db_session=None):
    """
    分页获取新闻
    - 支持按页码和每页数量查询
    - 支持按股票代码筛选
    - 支持按情感标签筛选（positive/negative/neutral）
    - 返回总数、页数等信息
    """
```

### API 端点（已集成到 main.py）
```
GET /api/news?page=1&page_size=20&stock_code=600000&sentiment_label=positive
```

### 响应格式
```json
{
  "total": 49,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "data": [
    {
      "id": 1,
      "title": "新闻标题",
      "content": "新闻内容",
      "url": "新闻链接",
      "sentiment": 0.8,
      "sentiment_label": "positive",
      "pub_date": "2026-02-28 10:00:00",
      "created_at": "2026-02-28 10:00:00"
    }
  ]
}
```

---

## 6. 新增 API 端点 ✅

### 交易日检查 API
```
GET /api/trading-day?date=2026-02-28
```

响应:
```json
{
  "date": "2026-02-28",
  "is_trading_day": false,
  "weekday": "Saturday",
  "next_trading_day": "2026-03-02",
  "previous_trading_day": "2026-02-27"
}
```

### 系统状态 API（增强）
```
GET /api/system/status
```

响应:
```json
{
  "status": "running",
  "is_trading_day": false,
  "next_trading_day": "2026-03-02T09:30:00",
  "last_health_check": "2026-02-28T10:00:00",
  "last_recommendation": "2026-02-27T09:30:00",
  "timestamp": "2026-02-28T10:00:00"
}
```

### 新闻分页 API（增强）
```
GET /api/news?page=1&page_size=20&stock_code=600000&sentiment_label=positive
```

---

## 测试验证 ✅

### 测试文件
- `/backend/test_improvements.py` - 完整的优化功能测试

### 测试结果
```
✅ 所有测试完成！

测试总结:
1. ✅ 交易日检查器 - 正常工作，正确识别周末
2. ✅ 新闻收集器 - 获取数据、情感分析、分页功能正常
3. ✅ 推荐器 - 交易日感知、强制执行功能正常
4. ✅ 调度器 - 交易日感知功能正常
```

---

## 环境配置

### 可选依赖（安装以获得更好体验）

```bash
# SnowNLP - 中文情感分析
pip install snownlp

# Tushare - 专业交易日历（需要注册获取 token）
pip install tushare
# 设置环境变量
export TUSHARE_TOKEN="your_token_here"
```

### 环境变量
```bash
# 使用真实新闻 API
USE_REAL_NEWS_API=true

# Tushare Token（可选）
TUSHARE_TOKEN=your_token_here
```

---

## 执行要求对照

| 要求 | 状态 | 说明 |
|------|------|------|
| 1. 添加交易日判断模块 | ✅ 完成 | `utils/trading_day_checker.py` |
| 2. 实现真实新闻数据获取 | ✅ 完成 | 支持东方财富、新浪财经 |
| 3. 添加新闻情感分析 | ✅ 完成 | SnowNLP + 关键词分析 |
| 4. 实现新闻分页 API | ✅ 完成 | `GET /api/news?...` |
| 5. 测试验证非交易日跳过逻辑 | ✅ 完成 | 非交易日自动跳过 |
| 6. 测试验证新闻数据获取和分页 | ✅ 完成 | 已测试 |

---

## 使用建议

### 1. 正常运行
```bash
cd /root/stock-recommendation-system/backend
python3 scheduler.py
```
- 推荐任务会自动在交易日执行
- 非交易日会自动跳过并记录日志

### 2. 手动触发推荐（强制执行）
```bash
# API 方式
curl -X POST "http://localhost:8000/api/recommendations/generate?force=true"

# Python 方式
from models.recommender import StockRecommender
recommender = StockRecommender()
recs = recommender.generate_recommendations(force=True)
```

### 3. 查看交易日信息
```bash
# API 方式
curl "http://localhost:8000/api/trading-day"

# Python 方式
from utils.trading_day_checker import get_trading_day_checker
checker = get_trading_day_checker()
print(f"今天是交易日? {checker.is_trading_day()}")
print(f"下一个交易日: {checker.get_next_trading_day()}")
```

---

## 未来扩展建议

1. **交易日历增强**
   - 定期同步 Tushare 节假日数据
   - 或使用其他交易日历数据源

2. **新闻源扩展**
   - 添加更多财经网站（同花顺、腾讯财经等）
   - 支持爬虫获取深层数据

3. **情感分析优化**
   - 使用预训练模型（BERT、RoBERTa等）
   - 针对财经领域微调

4. **调度器增强**
   - 支持动态配置调度时间
   - 支持任务依赖关系

---

## 总结

本次优化完成了以下核心目标：

1. ✅ **交易日感知** - 推荐逻辑只在交易日执行，非交易日自动跳过
2. ✅ **新闻真实化** - 支持真实新闻API（东方财富、新浪财经）
3. ✅ **情感分析** - 自动对新闻进行情感打分和分类
4. ✅ **新闻分页** - 完整的分页API，支持多种筛选条件
5. ✅ **强制执行** - 提供手动强制执行选项用于测试和特殊情况
6. ✅ **降级策略** - Tushare失败使用本地缓存，API失败使用模拟数据

系统现在更加智能、可靠，符合A股市场的实际交易规律。
