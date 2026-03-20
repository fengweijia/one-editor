import sys
import uuid
import asyncio
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.models.schemas import IngestUrlRequest, StoreIndexRequest, LLMExtractionResult
from src.services.fetcher import fetch_async
from src.providers.llm import get_provider
from src.storage.feishu_client import create_records_async
from src.config.settings import (
    set_model_settings,
    get_model_settings_public,
    set_model_settings_json,
    get_model_settings_json,
    set_feishu_settings,
    get_feishu_settings_public,
    state,
)

app = FastAPI(title="OneEditor API V2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory Task Store for SSE ---
# In a real app, use Redis. For MVP, memory is fine.
tasks_db = {}

async def process_url_task(task_id: str, url: str):
    """Background task to fetch and analyze URL, emitting SSE events."""
    try:
        # Step 1: Fetching
        tasks_db[task_id]["status"] = "fetching"
        tasks_db[task_id]["message"] = "正在通过 Jina Reader 读取网页原文..."
        
        content = await fetch_async(url)
        if not content:
            tasks_db[task_id]["status"] = "error"
            tasks_db[task_id]["message"] = "无法抓取网页内容，请检查链接是否有效。"
            return
            
        # Step 2: Analyzing
        tasks_db[task_id]["status"] = "analyzing"
        tasks_db[task_id]["message"] = "读取成功，AI 正在深度拆解核心观点与案例..."
        
        llm = get_provider()
        if not llm:
            tasks_db[task_id]["status"] = "error"
            tasks_db[task_id]["message"] = "LLM 未配置，请先在设置中配置大模型。"
            return
            
        analysis = await llm.analyze_async(content, meta={"url": url}, platform="web")
        if not analysis:
            tasks_db[task_id]["status"] = "error"
            tasks_db[task_id]["message"] = "AI 解析失败或返回了错误的 JSON 格式。"
            return
            
        # Step 3: Complete
        tasks_db[task_id]["status"] = "complete"
        tasks_db[task_id]["message"] = "解析完成！"
        tasks_db[task_id]["data"] = analysis
        
    except Exception as e:
        tasks_db[task_id]["status"] = "error"
        tasks_db[task_id]["message"] = f"处理过程中发生未知错误: {str(e)}"

@app.post("/api/v2/extract")
async def extract_v2(req: IngestUrlRequest, background_tasks: BackgroundTasks):
    """
    V2.0 异步解析入口。返回 task_id 供前端连接 SSE。
    """
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "status": "pending",
        "message": "任务已加入队列...",
        "data": None
    }
    background_tasks.add_task(process_url_task, task_id, req.url)
    return {"status": "ok", "task_id": task_id}

@app.get("/api/v2/tasks/{task_id}/stream")
async def task_stream(task_id: str, request: Request):
    """SSE endpoint for task progress."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
                
            task = tasks_db.get(task_id)
            if not task:
                yield {"event": "error", "data": json.dumps({"message": "Task not found"})}
                break
                
            yield {"event": "message", "data": json.dumps(task)}
            
            if task["status"] in ["complete", "error"]:
                # Clean up memory after sending terminal state
                await asyncio.sleep(1) # give client time to receive
                tasks_db.pop(task_id, None)
                break
                
            await asyncio.sleep(0.5)
            
    return EventSourceResponse(event_generator())

@app.post("/api/v2/save")
async def save_to_feishu(req: StoreIndexRequest):
    """
    Save the parsed and user-edited analysis directly to Feishu Bitable.
    Maps the data to the specific tables.
    """
    try:
        analysis = req.analysis
        meta = req.meta
        url = meta.get("url", "")
        title = meta.get("title", analysis.get("structured_analysis", {}).get("title", "Untitled"))
        
        # 1. 写入文章表 (Articles)
        article_record = {
            "URL": {"link": url, "text": title},
            "Title": title,
            "QualityScore": analysis.get("quality_rating", {}).get("score", 0),
            "Tags": analysis.get("structured_analysis", {}).get("tags", []),
            "Status": "Parsed"
        }
        
        # 注意：这里为了简化 MVP，将所有数据写入默认的第一张表
        # 在完全体的实现中，应该通过 Table ID 区分 Articles / Quotes / Cases 并建立关联
        # 我们目前把核心内容序列化到一个长文本字段，或者如果有对应字段就映射
        
        full_text = json.dumps(analysis, ensure_ascii=False, indent=2)
        article_record["RawAnalysis"] = full_text[:50000] # Bitable text limit
        
        res = await create_records_async(state.feishu_settings.default_table_id, [article_record])
        
        if not res.get("success"):
            return {"status": "error", "message": res.get("error")}
            
        return {"status": "ok", "data": res.get("data")}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# Legacy API endpoints below (kept for UI compatibility)
# ==========================================

@app.post("/ingest/url")
async def ingest_url_endpoint(req: IngestUrlRequest):
    return {"status": "ok", "data": ingest_url(req.url)}

@app.post("/ingest/url-universal")
async def ingest_url_universal_endpoint(req: IngestUrlRequest):
    """使用通用备选方案抓取 URL"""
    content, title, method = await fetch_with_fallback_async(req.url)
    return {
        "status": "ok", 
        "data": {
            "url": req.url,
            "content": content,
            "title": title,
            "method": method,
            "success": bool(content)
        }
    }

@app.post("/ingest/text")
async def ingest_text_endpoint(req: IngestTextRequest):
    return {"status": "ok", "data": ingest_text(req.text, req.meta)}

@app.post("/analyze")
async def analyze_endpoint(req: AnalyzeRequest):
    return {"status": "ok", "data": analyze_content(req.text, req.meta, req.platform)}

@app.post("/store-index")
async def store_index_endpoint(req: StoreIndexRequest):
    return {"status": "ok", "data": store_and_index(req.analysis, req.meta)}

@app.post("/assets/search")
async def search_endpoint(req: SearchRequest):
    return {"status": "ok", "data": search(req.q, req.tags, req.type, req.semantic, req.filters)}

@app.post("/themes/aggregate")
async def aggregate_endpoint(req: AggregateRequest):
    return {"status": "ok", "data": aggregate(req.topic, req.filters)}

@app.get("/settings/model")
async def get_model_settings_endpoint():
    return {"status": "ok", "data": get_model_settings_public()}

@app.post("/settings/model")
async def set_model_settings_endpoint(request: Request):
    ct = request.headers.get("content-type", "")
    data = {}
    if "application/json" in ct:
        data = await request.json()
    else:
        form = await request.form()
        data = {k: form.get(k) for k in ["provider", "api_id", "api_key"]}
    return {"status": "ok", "data": set_model_settings(data)}

@app.get("/settings/model/json")
async def get_model_settings_json_endpoint():
    return {"status": "ok", "data": get_model_settings_json()}

@app.post("/settings/model/json")
async def set_model_settings_json_endpoint(payload: dict):
    return {"status": "ok", "data": set_model_settings_json(payload)}

@app.get("/settings", response_class=HTMLResponse)
async def settings_ui():
    html = """
    <html>
    <head>
    <meta charset="utf-8"/>
    <title>OneEditor 设置</title>
    <style>
    body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; padding: 24px; background:#0f1115; color:#e8ebf0;}
    h3 { margin-top: 24px; }
    form { margin-bottom: 16px; }
    label { display:inline-block; width:140px; }
    input { margin:4px 0; padding:4px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.15); background:#151821; color:#e8ebf0;}
    button { margin-top:8px; padding:6px 14px; border-radius:6px; border:1px solid rgba(255,255,255,0.2); background:#1c2534; color:#e8ebf0; cursor:pointer;}
    textarea { width:100%; min-height:200px; padding:8px; border-radius:6px; border:1px solid rgba(255,255,255,0.2); background:#151821; color:#e8ebf0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size:13px;}
    .row { display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap;}
    .col { flex:1; min-width:280px;}
    .pill { padding:4px 10px; border-radius:999px; border:1px solid rgba(255,255,255,0.25); background:#151821; color:#e8ebf0; cursor:pointer; font-size:12px; margin-right:6px; margin-top:6px; display:inline-block;}
    #modelJsonStatus { margin-top:6px; font-size:12px; color:#99a1ad;}
    </style>
    </head>
    <body>
    <h2>OneEditor 设置</h2>
    <div class="row">
      <div class="col">
        <h3>模型配置（简易）</h3>
        <form method="post" action="/settings/model">
        <label>Provider:</label><input name="provider" value="openai"/><br/>
        <label>API ID:</label><input name="api_id" placeholder="例如 openai-gpt4o"/><br/>
        <label>API Key:</label><input name="api_key" placeholder="sk-..."/><br/>
        <button type="submit">保存</button>
        </form>
      </div>
      <div class="col">
        <h3>模型配置（JSON）</h3>
        <div>
          <div style="margin-bottom:6px;font-size:12px;color:#99a1ad;">可一次性配置多厂商模型。左侧为简易方式，右侧为完整JSON。</div>
          <div style="margin-bottom:6px;">
            <span class="pill" id="tplOpenAI">填充 OpenAI 模板</span>
            <span class="pill" id="tplSilicon">填充 SiliconFlow + DeepSeek 模板</span>
            <span class="pill" id="tplDeepseek">填充 DeepSeek 官方模板</span>
          </div>
          <textarea id="modelJson" placeholder='{ "active": "...", "profiles": { "...": { "provider": "openai", "base_url": "...", "api": "openai-chat", "api_key": "xxx", "model_id": "gpt-4o-mini", "model_name": "GPT-4o Mini" } } }'></textarea>
          <button id="btnSaveModelJson" type="button">保存 JSON 配置</button>
          <div id="modelJsonStatus"></div>
        </div>
      </div>
    </div>
    <h3>飞书多维表格配置</h3>
    <form method="post" action="/settings/feishu">
    <label>App ID:</label><input name="app_id"/><br/>
    <label>App Secret:</label><input name="app_secret"/><br/>
    <label>Bitable App Token:</label><input name="app_token"/><br/>
    <label>Points表ID:</label><input name="table_points"/><br/>
    <label>Cases表ID:</label><input name="table_cases"/><br/>
    <label>Quotes表ID:</label><input name="table_quotes"/><br/>
    <label>Structures表ID:</label><input name="table_structures"/><br/>
    <button type="submit">保存</button>
    </form>
    <h3>Universal 抓取服务</h3>
    <form method="post" action="/settings/universal">
    <label>Endpoint:</label><input name="endpoint" placeholder="例如 https://api.example.com/universal"/><br/>
    <label>Token:</label><input name="token" placeholder="Bearer Token"/><br/>
    <label>Prefer Markdown:</label><input name="prefer_markdown" value="true"/><br/>
    <button type="submit">保存</button>
    </form>
    <script>
    async function loadModelJson() {
      try {
        const r = await fetch('/settings/model/json');
        if (!r.ok) return;
        const j = await r.json();
        if (j && j.data) {
          document.getElementById('modelJson').value = JSON.stringify(j.data, null, 2);
        }
      } catch (e) {}
    }
    function tplOpenAI() {
      const obj = {
        active: "openai-gpt4o",
        profiles: {
          "openai-gpt4o": {
            provider: "openai",
            base_url: "https://api.openai.com/v1",
            api: "openai-chat",
            api_key: "sk-your-openai-key",
            model_id: "gpt-4o-mini",
            model_name: "GPT-4o Mini"
          }
        }
      };
      document.getElementById('modelJson').value = JSON.stringify(obj, null, 2);
    }
    function tplSilicon() {
      const obj = {
        active: "siliconflow-deepseek",
        profiles: {
          "siliconflow-deepseek": {
            provider: "siliconflow",
            base_url: "https://api.siliconflow.cn/v1",
            api: "openai-chat",
            api_key: "your-siliconflow-api-key",
            model_id: "deepseek-ai/DeepSeek-V3.2",
            model_name: "DeepSeek-V3.2"
          }
        }
      };
      document.getElementById('modelJson').value = JSON.stringify(obj, null, 2);
    }
    function tplDeepseek() {
      const obj = {
        active: "deepseek-chat",
        profiles: {
          "deepseek-chat": {
            provider: "deepseek",
            base_url: "https://api.deepseek.com/v1",
            api: "openai-chat",
            api_key: "your-deepseek-api-key",
            model_id: "deepseek-chat",
            model_name: "DeepSeek-Chat"
          }
        }
      };
      document.getElementById('modelJson').value = JSON.stringify(obj, null, 2);
    }
    async function saveModelJson() {
      const el = document.getElementById('modelJson');
      const status = document.getElementById('modelJsonStatus');
      status.textContent = '保存中...';
      let payload;
      try {
        payload = JSON.parse(el.value || '{}');
      } catch (e) {
        status.textContent = 'JSON 解析失败：' + e;
        return;
      }
      try {
        const r = await fetch('/settings/model/json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!r.ok) {
          status.textContent = '保存失败，状态码：' + r.status;
          return;
        }
        status.textContent = '保存成功';
      } catch (e) {
        status.textContent = '请求失败：' + e;
      }
    }
    document.getElementById('tplOpenAI').addEventListener('click', tplOpenAI);
    document.getElementById('tplSilicon').addEventListener('click', tplSilicon);
    document.getElementById('tplDeepseek').addEventListener('click', tplDeepseek);
    document.getElementById('btnSaveModelJson').addEventListener('click', saveModelJson);
    loadModelJson();
    </script>
    </body>
    </html>
    """
    return html

@app.get("/", response_class=HTMLResponse)
async def home():
    p = Path(__file__).resolve().parent.parent / "frontend" / "public" / "index.html"
    return p.read_text(encoding="utf-8")

@app.get("/writer", response_class=HTMLResponse)
async def writer():
    p = Path(__file__).resolve().parent / "web" / "writer.html"
    return p.read_text(encoding="utf-8")

@app.get("/settings/feishu")
async def get_feishu_settings_endpoint():
    return {"status": "ok", "data": get_feishu_settings_public()}

@app.post("/settings/feishu")
async def set_feishu_settings_endpoint(request: Request):
    ct = request.headers.get("content-type", "")
    data = {}
    if "application/json" in ct:
        data = await request.json()
    else:
        form = await request.form()
        data = {k: form.get(k) for k in ["app_id", "app_secret", "app_token", "table_points", "table_cases", "table_quotes", "table_structures"]}
    return {"status": "ok", "data": set_feishu_settings(data)}

@app.get("/settings/universal")
async def get_universal_settings_endpoint():
    return {"status": "ok", "data": get_universal_settings_public()}

@app.post("/settings/universal")
async def set_universal_settings_endpoint(request: Request):
    ct = request.headers.get("content-type", "")
    data = {}
    if "application/json" in ct:
        data = await request.json()
    else:
        form = await request.form()
        data = {
            "endpoint": form.get("endpoint"),
            "token": form.get("token"),
            "prefer_markdown": form.get("prefer_markdown"),
        }
    return {"status": "ok", "data": set_universal_settings(data)}

@app.get("/settings/universal/test")
async def test_universal(url: str):
    text, title = fetch_universal_text(url)
    snippet = (text or "")[:300]
    return {
        "status": "ok",
        "data": {
            "title": title or "",
            "length": len(text or ""),
            "snippet": snippet
        }
    }

# === 提取配置相关 ===

@app.get("/settings/extract")
async def get_extract_settings():
    """获取提取配置（观点/案例/金句）"""
    return {"status": "ok", "data": state.extract_config.model_dump()}

@app.post("/settings/extract")
async def set_extract_settings(payload: dict):
    """设置提取配置"""
    types = payload.get("types", [])
    valid_types = []
    for t in types:
        if isinstance(t, dict) and t.get("name"):
            from src.config.settings import ExtractTypeConfig
            valid_types.append(ExtractTypeConfig(
                name=t.get("name", ""),
                enabled=t.get("enabled", True),
                prompt=t.get("prompt", "")
            ))
    state.extract_config.types = valid_types
    return {"status": "ok", "data": {"types": [t.model_dump() for t in valid_types]}}

@app.get("/settings/extract/reset")
async def reset_extract_settings():
    """重置为默认提取配置"""
    state.extract_config = DEFAULT_EXTRACT_CONFIG
    return {"status": "ok", "data": state.extract_config.model_dump()}

# === 飞书表格初始化 ===
from src.storage.feishu_client import init_default_tables_async, list_tables_async, create_records_async

@app.post("/feishu/init-tables")
async def init_feishu_tables():
    """自动创建默认的 4 个飞书表格（观点库/案例库/金句库/结构库）"""
    result = await init_default_tables_async()
    return {"status": "ok", "data": result}

@app.get("/feishu/tables")
async def get_feishu_tables():
    """获取飞书表格列表"""
    result = await list_tables_async()
    return {"status": "ok", "data": result}

# === 完整流程 API ===
@app.post("/extract/full")
async def full_extract流程(req: IngestUrlRequest):
    """
    完整流程：URL抓取 → AI提取 → 返回结果（供用户确认后存储）
    异步版本，支持高并发
    """
    from src.config.settings import state
    
    # 1. 异步抓取内容
    content, title, method = await fetch_with_fallback_async(req.url)
    if not content:
        return {"status": "error", "message": "无法抓取内容，请尝试手动粘贴"}
    
    # 2. AI 提取（CPU密集型，在线程池中运行）
    import asyncio
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(None, analyze_content, content, {"url": req.url, "title": title}, "web")
    
    # 3. 返回结果
    return {
        "status": "ok",
        "data": {
            "url": req.url,
            "title": title,
            "method": method,
            "analysis": analysis
        }
    }

@app.post("/extract/save")
async def save_to_feishu(req: StoreIndexRequest):
    """
    保存提取结果到飞书
    异步版本，支持高并发
    """
    from src.config.settings import state
    s = state.feishu_settings
    
    # 检查配置
    if not s.app_token or not (s.table_points and s.table_cases and s.table_quotes):
        return {"status": "error", "message": "请先配置飞书表格"}
    
    analysis = req.analysis
    meta = req.meta or {}
    
    results = []
    
    # 并发保存观点、案例、金句
    async def save_points():
        points = analysis.get("points", [])
        if points and s.table_points:
            records = []
            for p in points:
                records.append({
                    "原文": meta.get("title", ""),
                    "观点": p.get("claim_text", ""),
                    "标签": p.get("tags", []),
                    "来源": meta.get("source", ""),
                    "来源URL": meta.get("url", ""),
                })
            if records:
                r = await create_records_async(s.table_points, records)
                return {"type": "points", "count": len(records), "success": r.get("success")}
        return None
    
    async def save_cases():
        cases = analysis.get("cases", [])
        if cases and s.table_cases:
            records = []
            for c in cases:
                records.append({
                    "原文": meta.get("title", ""),
                    "案例": c.get("summary", ""),
                    "标签": c.get("tags", []),
                    "来源": meta.get("source", ""),
                    "来源URL": meta.get("url", ""),
                })
            if records:
                r = await create_records_async(s.table_cases, records)
                return {"type": "cases", "count": len(records), "success": r.get("success")}
        return None
    
    async def save_quotes():
        quotes = analysis.get("quotes", [])
        if quotes and s.table_quotes:
            records = []
            for q in quotes:
                records.append({
                    "原文": meta.get("title", ""),
                    "金句": q.get("text", ""),
                    "适用场景": q.get("scene", ""),
                    "标签": q.get("tags", []),
                    "来源": meta.get("source", ""),
                    "来源URL": meta.get("url", ""),
                })
            if records:
                r = await create_records_async(s.table_quotes, records)
                return {"type": "quotes", "count": len(records), "success": r.get("success")}
        return None
    
    # 并发执行
    saved = await asyncio.gather(save_points(), save_cases(), save_quotes())
    results = [r for r in saved if r]
    
    # 保存金句
    quotes = analysis.get("quotes", [])
    if quotes and s.table_quotes:
        records = []
        for q in quotes:
            records.append({
                "原文": meta.get("title", ""),
                "金句": q.get("text", ""),
                "适用场景": q.get("scene", ""),
                "标签": q.get("tags", []),
                "来源": meta.get("source", ""),
                "来源URL": meta.get("url", ""),
            })
        if records:
            r = create_records(s.table_quotes, records)
            results.append({"type": "quotes", "count": len(records), "success": r.get("success")})
    
    return {"status": "ok", "data": {"saved": results}}
