# OneEditor V2.0

OneEditor 是一个**可检索的个性化灵感写作系统**。它的核心目标是：把你阅读和拆解文章的时间压缩 80%，并将其转化为结构化的灵感资产。

> **V2.0 核心更新：** 
> 彻底抛弃了"AI 摘要"的伪命题，转向**"严格的结构化数据提取"**。引入了基于 SSE 的异步处理架构和防爹味（Anti-AI Slop）的内联编辑前端。

## 🌟 核心特性 (The 10-Star Experience)

- **无缝抓取**：基于 Jina Reader API，一键抓取微信公众号、知乎及普通网页。
- **严格结构化提取 (Anti-AI Slop)**：通过 Pydantic 强制 LLM 输出严格的 JSON 格式（包含原文金句、案例细节、质量评级），彻底杜绝 AI 的废话前缀。
- **内联编辑卡片 (Interactive Cards)**：提取的内容不是只读的 Markdown，而是可直接点击编辑的 UI 卡片。你可以在入库前微调任何不满意的观点。
- **Serverless 数据库 (飞书多维表格)**：砍掉了复杂的本地数据库，直接利用飞书 Bitable 作为唯一的云端数据中心。支持批量写入（Batch Insert）绕过限流。
- **SSE 实时流式反馈**：告别干等的菊花图，实时展示"抓取中 -> 拆解中 -> 完成"的多阶段进度。

## 🏗 技术栈

- **后端**：Python FastAPI + Pydantic V2 + SSE (Server-Sent Events)
- **大模型接入**：支持兼容 OpenAI 接口的任意模型（如 DeepSeek, GPT-4o, Claude 等）
- **前端**：Vanilla JS + HTML5 + Tailwind CSS（极简无构建，直接跑）
- **存储层**：Feishu (Lark) Bitable API

## 🚀 快速启动

### 1. 后端服务

```bash
cd backend
python -m pip install -r requirements.txt
python -m pip install uvicorn fastapi httpx aiohttp pydantic sse-starlette

# 运行后端
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 配置文件
在 `backend/config.json` 中配置你的 LLM API Key 和 飞书 App Token：
```json
{
  "model": {
    "active": "openai",
    "profiles": {
      "openai": {
        "api": "openai-chat",
        "api_key": "sk-your-key",
        "model_id": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1"
      }
    }
  },
  "feishu": {
    "app_id": "cli_your_app_id",
    "app_secret": "your_app_secret",
    "app_token": "your_bitable_app_token",
    "default_table_id": "tbl_your_table_id"
  }
}
```

### 3. 前端服务
在另一个终端中启动前端静态服务器：
```bash
cd frontend/public
python -m http.server 3000
```
打开浏览器访问：`http://localhost:3000` 即可开始使用！

## 🗺 实施路线图 (Roadmap)
- [x] Phase 1: MVP (Jina抓取 + 结构化JSON解析 + 零爹味可编辑UI)
- [x] Phase 2: 飞书多维表格打通 (Batch Insert 支持)
- [ ] Phase 3: 灵感唤醒机制 (利用飞书API聚合素材，辅助组合创作)