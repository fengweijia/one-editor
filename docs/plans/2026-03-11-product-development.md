# OneEditor 项目开发计划 (v1.0 完整版)

> **For Claude:** 使用 superpowers:executing-plans 来逐步执行此计划

**Goal:** 将OneEditor开发到1.0完整版本

**Architecture:** Python FastAPI后端 + HTML静态前端 + 飞书多维表格存储

**Tech Stack:** FastAPI, Jina Reader, 微信文章抓取, Claude/GPT-4, 飞书多维表格

**扩展预留:** 为写作Agent预留接口（非1.0范围，但架构预留）

---

## 一、产品需求总结

| 需求 | 说明 |
|:---|:---|
| **核心价值** | 把"读"和"拆"时间压缩80%，构建可检索灵感库 |
| **工作流** | 读文章 → 提炼要点 → 内化思考 → 产出文章 |
| **产品形态** | Web应用 + 飞书归档 |
| **输入源** | 普通网页 + 微信公众号文章 |
| **扩展预留** | 写作Agent接口（2.0） |

---

## 二、当前代码状态

| 模块 | 已完成 | 待开发 |
|:---|:---:|:---:|
| **services/** | fetcher, extractor, universal_client | 完善URL路由 |
| **skills/** | content_analyze, asset_store_index, retrieval | 飞书归档、检索 |
| **providers/** | llm | - |
| **frontend/** | index.html, writer.html | 完善交互 |

---

## 三、开发阶段（1.0完整版）

### 阶段一：基础架构

| 任务 | 内容 | 优先级 |
|:---|:---|:---:|
| 1.1 | 修复后端import路径，确保可启动 | P0 |
| 1.2 | URL抓取服务（通用网页 + 微信公众号） | P0 |
| 1.3 | 微信文章防盗链处理 | P0 |
| 1.4 | AI解析引擎完善 | P0 |

### 阶段二：核心功能

| 任务 | 内容 | 优先级 |
|:---|:---|:---:|
| 2.1 | 飞书多维表格归档（文章库） | P0 |
| 2.2 | 飞书归档（观点库+案例库+金句库） | P0 |
| 2.3 | 前后端API对接 | P0 |
| 2.4 | 前端页面交互完善 | P1 |

### 阶段三：增强功能

| 任务 | 内容 | 优先级 |
|:---|:---|:---:|
| 3.1 | 历史记录管理 | P1 |
| 3.2 | 批量导入 | P1 |
| 3.3 | 自定义标签 | P1 |
| 3.4 | 灵感库语义检索 | P1 |

### 阶段四：扩展预留（接口）

| 任务 | 内容 | 优先级 |
|:---|:---|:---:|
| 4.1 | 写作Agent接口定义 | P2 |
| 4.2 | 素材推荐API | P2 |
| 4.3 | 大纲生成API | P2 |

> **注：** 4.x为2.0写作Agent预留接口，1.0只完成接口定义，不实现具体功能

---

## 四、MVP任务详情

### Task 1.1: 修复后端启动

**Goal:** 确保后端可正常启动

**Files:**
- Modify: `backend/app.py` - 检查import路径
- Modify: `backend/src/` - 配置PYTHONPATH

**Step 1: 测试当前启动**

```bash
cd backend
PYTHONPATH=. python -c "from app import app; print('OK')"
```

**Step 2: 修复import问题**

可能需要修改：
- `from oneeditor.models` → `from src.models`
- 或设置 `sys.path`

**Step 3: 验证启动**

```bash
PYTHONPATH=. uvicorn app:app --host 0.0.0.0 --port 8000
```

---

### Task 1.2: URL抓取服务（通用网页 + 微信公众号）

**Goal:** 实现URL输入→内容抓取，支持微信公众号

**Files:**
- Modify: `backend/src/services/fetcher.py`
- Modify: `backend/src/services/wechat_fetcher.py` (新建)
- Modify: `backend/src/skills/source_ingest.py`

**Step 1: URL类型识别**

```python
def detect_url_type(url):
    if "mp.weixin.qq.com" in url:
        return "wechat"
    elif "zhihu.com" in url:
        return "zhihu"
    elif "36kr.com" in url:
        return "36kr"
    else:
        return "general"
```

**Step 2: 通用网页 - Jina Reader**

```python
import requests

def fetch_general(url):
    response = requests.get(f"https://r.jina.ai/{url}")
    return response.text
```

**Step 3: 微信公众号 - 特殊处理**

```python
def fetch_wechat(url):
    # 方法1: WeChat API (需要token)
    # 方法2: wechat-fetch 等库
    # 方法3: Jina Reader (部分有效)
    response = requests.get(f"https://r.jina.ai/{url}")
    return response.text
```

**Step 4: 测试抓取**

```bash
# 通用网页
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'

# 微信公众号
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxx"}'
```

---

### Task 1.3: AI解析

**Goal:** 实现结构化内容解析

**Files:**
- Modify: `backend/src/skills/content_analyze.py`
- Modify: `backend/src/providers/llm.py`

**Step 1: 检查现有Prompt**

```python
# 查看 content_analyze.py 中的 prompt
```

**Step 2: 测试解析**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "文章内容...", "options": {}}'
```

---

### Task 1.4: 前后端API对接

**Goal:** 前端页面可调用后端API

**Files:**
- Modify: `frontend/public/index.html`
- Create: `frontend/src/services/api.js`

**Step 1: 前端API封装**

```javascript
async function analyzeUrl(url) {
  const res = await fetch('/analyze', {
    method: 'POST',
    body: JSON.stringify({ url })
  });
  return res.json();
}
```

**Step 2: 联调测试**

---

### Task 1.5: 前端交互完善

**Goal:** 页面可展示解析结果

**Files:**
- Modify: `frontend/public/index.html`
- Modify: `frontend/public/writer.html`

---

## 五、执行计划

**1.0完整版执行顺序：**
1. 修复后端启动 → 测试通过
2. URL抓取 + 微信 → 测试通过
3. AI解析 → 测试通过
4. 飞书归档 → 测试通过
5. API对接 → 测试通过
6. 前端展示 → 测试通过
7. 扩展接口 → 完成定义

---

## 六、需要的资源

| 资源 | 说明 |
|:---|:---|
| Jina Reader API | 免费，用于URL抓取 |
| 微信文章抓取方案 | wechat-fetch / 自建Proxy |
| Claude/GPT API | 需要配置key |
| 飞书多维表格 | 存储归档 |

---

**需要我开始执行吗？确认后按Task顺序逐步执行 🦞**