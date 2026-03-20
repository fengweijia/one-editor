import sys
import uuid
import asyncio
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.models.schemas import IngestUrlRequest, StoreIndexRequest
from src.services.fetcher import fetch_async
from src.providers.llm import get_provider
from src.storage.feishu_client import create_records_async
from src.config.settings import (
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
