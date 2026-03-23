# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

OneEditor V2.0 是一个**可检索的个性化灵感写作系统**。核心功能是从文章（微信公众号、知乎、普通网页）中提取结构化数据，而非 AI 总结。

- **反 AI 垃圾（Anti-AI Slop）设计**：通过 Pydantic 强制 LLM 输出严格 JSON 格式
- **存储**：飞书多维表格（Feishu Bitable）作为唯一数据源
- **前端**：Vanilla JS，无构建工具
- **后端**：FastAPI + SSE 实时流式反馈

## 常用命令

### 后端服务

```bash
cd backend

# 安装依赖
pip install -r requirements.min.txt  # 生产环境最小依赖
# 或
pip install -r requirements.txt      # 完整依赖

# 运行开发服务器
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 前端服务

```bash
cd frontend/public
python -m http.server 3000
```

访问：`http://localhost:3000`

## 代码架构

### 目录结构

```
one-editor/
├── backend/
│   ├── app.py                          # FastAPI 主入口
│   ├── config.json                     # 配置文件（LLM + 飞书）
│   ├── requirements.min.txt            # 最小依赖
│   └── src/
│       ├── config/settings.py          # 全局状态 + 配置管理
│       ├── models/schemas.py           # Pydantic 数据模型
│       ├── providers/llm.py            # LLM 提供商（OpenAI 兼容）
│       ├── services/fetcher.py         # 内容抓取（Jina Reader）
│       └── storage/feishu_client.py    # 飞书异步客户端
└── frontend/public/
    ├── index.html                      # 主提取界面
    └── writer.html                     # 写作伴侣界面
```

### 核心数据流程

1. **URL 输入** → `POST /api/v2/extract` 返回 `task_id`
2. **SSE 流式连接** → `GET /api/v2/tasks/{task_id}/stream`
3. **后台任务**：
   - Jina Reader 抓取内容
   - LLM 按 `LLMExtractionResult` Schema 提取
   - 实时推送状态：`fetching` → `analyzing` → `complete`
4. **保存** → `POST /api/v2/save` 写入飞书

### 关键模块

| 模块 | 作用 |
|------|------|
| `app.py` | API 路由 + SSE 事件流 + 后台任务 |
| `schemas.py` | `LLMExtractionResult` 等 Pydantic 模型，定义 LLM 输出格式 |
| `llm.py` | `OpenAICompatibleProvider`，支持 DeepSeek/GPT-4o/Claude 等 |
| `settings.py` | `State` 单例，管理 `~/.oneeditor/settings.json` |
| `feishu_client.py` | 飞书多维表格异步 API，支持批量写入 |

### LLM 提取 Schema (`LLMExtractionResult`)

```python
- quality_rating: {score, summary, concerns}  # 质量评分 + 逻辑缺陷指出
- structured_analysis: {tags, core_arguments (point, evidence, writing_technique), writing_directions}
- raw_essence: {golden_sentences (text, position, context_before, context_after), cases}
```

## 配置文件

`backend/config.json` 格式：

```json
{
  "model": {
    "active": "openai",
    "profiles": {
      "openai": {
        "api_key": "sk-...",
        "model_id": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1"
      }
    }
  },
  "feishu": {
    "app_id": "cli_...",
    "app_secret": "...",
    "app_token": "...",
    "default_table_id": "tbl_..."
  }
}
```

## 设计理念

- **不做 AI 总结**：只做结构化提取，保留原文上下文
- **内联编辑 UI**：提取结果可直接编辑，无需表单
- **全异步**：FastAPI + httpx + aiohttp
- **零构建前端**：原生 JS，直接运行
