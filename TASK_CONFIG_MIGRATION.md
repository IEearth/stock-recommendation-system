# 任务配置迁移 + 页面管理 - 使用文档

## 功能概述

本系统已成功将硬编码的任务配置迁移到数据库，并增加了前端页面管理任务配置的能力。

## 主要功能

### 1. 数据库设计
- 新增 `task_configs` 表，包含以下字段：
  - `id` (主键)
  - `task_name` (任务名称，唯一)
  - `task_type` (任务类型)
  - `is_enabled` (是否启用)
  - `interval_seconds` (执行间隔，秒)
  - `cron_expression` (Cron表达式，可选)
  - `last_run_time` (上次执行时间)
  - `next_run_time` (下次执行时间)
  - `config_json` (JSON格式的额外配置)
  - `description` (任务描述)
  - `created_at`, `updated_at` (时间戳)

### 2. 后端 API

**任务配置相关接口：**
- `GET /api/task-configs` - 获取所有任务配置
- `GET /api/task-configs/{task_name}` - 获取单个任务配置
- `POST /api/task-configs` - 创建新任务配置
- `PUT /api/task-configs/{task_name}` - 更新任务配置
- `DELETE /api/task-configs/{task_name}` - 删除任务配置
- `POST /api/task-configs/{task_name}/toggle` - 切换启用/禁用状态
- `POST /api/task-configs/{task_name}/trigger` - 手动触发任务执行

### 3. 前端页面

在管理后台新增 **任务配置管理** 页面，提供：
- 任务配置列表展示
- 启用/禁用开关
- 执行间隔编辑
- Cron表达式支持
- 编辑配置
- 手动触发
- 删除任务
- 新建任务

### 4. 数据库驱动调度器

新增 `scheduler_db.py` 模块：
- 从数据库读取任务配置
- 支持热更新任务配置
- 自动创建默认任务配置
- 支持间隔和 Cron 两种触发方式

## 部署步骤

### 1. 数据库迁移

```bash
cd /root/stock-recommendation-system/backend
python migrate_task_configs.py
```

这将：
- 初始化数据库表（包括新的 `task_configs` 表）
- 创建默认任务配置

### 2. 启动后端服务

使用新的数据库驱动调度器：

```bash
cd /root/stock-recommendation-system/backend

# 方式1：仅启动调度器
python run_scheduler_db.py

# 方式2：启动 FastAPI 服务（推荐）
python main.py
```

FastAPI 服务将自动启动后台任务调度器。

### 3. 访问管理后台

打开浏览器访问：`http://localhost:8000`

点击侧边栏的 **⚙️ 任务配置** 菜单，即可管理任务配置。

## 默认任务配置

迁移脚本会创建以下默认任务配置：

| 任务名称 | 类型 | 启用 | 触发方式 | 说明 |
|---------|------|------|----------|------|
| health_check | health_check | ✅ | 每20分钟 | 系统健康检查 |
| update_news | data_fetch | ✅ | 每1小时 | 更新新闻数据 |
| full_data_update | daily_update | ✅ | 每天02:00 | 完整数据更新 |
| update_stock_list | data_fetch | ❌ | 每天 | 更新股票列表 |
| update_market_data | data_fetch | ❌ | 每1小时 | 更新行情数据 |
| train_model | daily_update | ❌ | 每天 | 训练预测模型 |
| generate_recommendations | recommendation | ❌ | 每天 | 生成推荐 |

## Cron 表达式说明

Cron表达式格式：`分 时 日 月 周`

示例：
- `0 2 * * *` - 每天凌晨2点
- `0 */4 * * *` - 每4小时
- `0 9,18 * * *` - 每天9点和18点
- `0 0 * * 0` - 每周日午夜

## 热更新任务配置

当你通过前端或API修改任务配置后，调度器会自动重新加载配置（下次调度时生效）。

如需立即生效，可以：
1. 重启后端服务
2. 手动触发任务

## 文件变更

### 新增文件
- `backend/scheduler_db.py` - 数据库驱动的任务调度器
- `backend/migrate_task_configs.py` - 数据库迁移脚本
- `backend/run_scheduler_db.py` - 新调度器启动脚本
- `frontend/task-config-page.html` - 任务配置管理页面片段

### 修改文件
- `backend/database.py` - 添加 TaskConfig 模型
- `backend/main.py` - 添加任务配置 API 端点
- `frontend/index.html` - 添加任务配置管理页面

## 向后兼容性

- 旧的 `scheduler.py` 仍然可用
- 新的 `scheduler_db.py` 完全兼容旧的任务函数
- 迁移不会影响现有数据

## 故障排查

### 问题：任务配置表未创建

**解决方案：**
```bash
cd /root/stock-recommendation-system/backend
python migrate_task_configs.py
```

### 问题：任务未按预期执行

**解决方案：**
1. 检查任务配置是否启用
2. 检查间隔或 Cron 表达式是否正确
3. 查看任务日志确认执行状态
4. 查看后端日志中的错误信息

### 问题：前端页面无法加载

**解决方案：**
1. 确认后端服务已启动
2. 检查 API 端点是否正常
3. 打开浏览器开发者工具查看错误

## 总结

✅ 数据库模型已更新
✅ API 端点已实现
✅ 前端页面已集成
✅ 数据库驱动调度器已创建
✅ 默认任务配置已设置
✅ 向后兼容性已保证

系统已成功迁移到数据库驱动的任务配置管理方式！
