import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from src.models.schemas import IngestUrlRequest, IngestTextRequest, AnalyzeRequest, StoreIndexRequest, SearchRequest, AggregateRequest
from src.skills.source_ingest import ingest_url, ingest_text
from src.skills.content_analyze import analyze_content
from src.skills.asset_store_index import store_and_index
from src.skills.retrieval import search
from src.skills.theme_aggregate import aggregate
from src.config.settings import (
    set_model_settings,
    get_model_settings_public,
    set_model_settings_json,
    get_model_settings_json,
    set_feishu_settings,
    get_feishu_settings_public,
    set_universal_settings,
    get_universal_settings_public,
)
from src.services.universal_client import fetch_universal_text
from src.api.writing_agent import router as writing_agent_router

app = FastAPI(title="OneEditor API")

# 注册写作Agent路由（2.0预留）
app.include_router(writing_agent_router, prefix="/writing", tags=["writing-agent"])

@app.post("/ingest/url")
async def ingest_url_endpoint(req: IngestUrlRequest):
    return {"status": "ok", "data": ingest_url(req.url)}

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
