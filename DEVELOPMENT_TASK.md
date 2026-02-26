# 开发任务
创建一个完整的A股智能推荐系统，包含以下功能：

## 核心要求
1. 使用 Python + FastAPI 作为后端
2. 使用 SQLite 存储数据
3. 使用 Tushare Pro 获取股票数据
4. 实现新闻采集、行情数据、预测模型、推荐引擎
5. 创建一个 React + Ant Design 前端展示推荐结果
6. 实现定时任务每20分钟检查系统健康状态

## 项目结构
```
stock-recommendation-system/
├── backend/
│   ├── main.py              # FastAPI 主应用
│   ├── database.py          # 数据库模型
│   ├── models/
│   │   ├── news_collector.py     # 新闻采集
│   │   ├── market_collector.py    # 行情数据
│   │   ├── predictor.py           # 预测模型
│   │   └── recommender.py        # 推荐引擎
│   ├── scheduler.py         # 定时任务
│   └── health_check.py      # 健康检查
├── frontend/               # React 前端
├── requirements.txt
└── README.md
```

请开发完整系统，确保代码可运行，包含错误处理和日志。
