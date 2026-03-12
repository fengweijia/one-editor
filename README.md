# OneEditor 🧠

AI 驱动的阅读效率工具，把"读"和"拆"的时间压缩 80%，并构建可检索的灵感资产库。

## ✨ 核心功能

- **URL 智能解析** - 支持公众号、知乎、36kr、即刻等平台自动识别抓取
- **AI 要点提炼** - 自动提取文章核心观点、金句、案例
- **持久化归档** - 自动同步到飞书多维表格，构建个人知识库
- **语义搜索** - 跨文章检索灵感，精准定位引用素材

## 🛠️ 技术栈

- **后端**: Python FastAPI
- **前端**: React/Taro
- **存储**: 飞书多维表格
- **部署**: Serverless

## 🚀 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn oneeditor.app:app --reload
```

### API 列表

| 接口 | 方法 | 说明 |
|:---|:---:|:---|
| `/ingest/url` | POST | URL 抓取解析 |
| `/ingest/text` | POST | 文本直接输入 |
| `/analyze` | POST | AI 分析要点 |
| `/store-index` | POST | 存入索引库 |
| `/assets/search` | POST | 语义搜索 |
| `/themes/aggregate` | POST | 主题聚合 |

## 📋 环境变量

```env
# 飞书配置
FEISHU_APP_ID=xxx
FEISHU_APP_SECRET=xxx
FEISHU_BITABLE_APP_TOKEN=xxx

# AI 配置
OPENAI_API_KEY=sk-xxx
```

## 📄 协议

MIT License