from typing import Dict, Any, Optional
from src.storage.state import repo
from src.config.settings import state
from src.storage.feishu_client import list_records

def aggregate(topic: str, filters: Optional[Dict[str, Any]] = None) -> Dict:
    t = topic.lower()
    agg = {"points": [], "cases": [], "quotes": [], "structures": []}
    fs = state.feishu_settings
    if fs.app_token:
        if fs.table_points:
            r = list_records(fs.table_points, page_size=100)
            if r.get("success"):
                items = r["data"].get("data", {}).get("items", [])
                for rec in items:
                    f = rec.get("fields", {})
                    if t in (",".join(f.get("tags", []))).lower() or t in (f.get("claim_text", "") or "").lower():
                        agg["points"].append({"id": rec.get("record_id", ""), "item": f})
        if fs.table_cases:
            r = list_records(fs.table_cases, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    if t in (",".join(f.get("tags", []))).lower() or t in (f.get("details", "") or "").lower():
                        agg["cases"].append({"id": rec.get("record_id", ""), "item": f})
        if fs.table_quotes:
            r = list_records(fs.table_quotes, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    if t in (",".join(f.get("tags", []))).lower() or t in (f.get("text", "") or "").lower():
                        agg["quotes"].append({"id": rec.get("record_id", ""), "item": f})
        if fs.table_structures:
            r = list_records(fs.table_structures, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    if t in (",".join(f.get("tags", []))).lower() or t in (f.get("outline", "") or "").lower():
                        agg["structures"].append({"id": rec.get("record_id", ""), "item": f})
    else:
        for idx, item in enumerate(repo.assets["points"]):
            if t in " ".join(item.get("tags", [])).lower() or t in item.get("claim_text", "").lower():
                agg["points"].append({"id": idx, "item": item})
        for idx, item in enumerate(repo.assets["cases"]):
            if t in " ".join(item.get("tags", [])).lower() or t in item.get("details", "").lower():
                agg["cases"].append({"id": idx, "item": item})
        for idx, item in enumerate(repo.assets["quotes"]):
            if t in " ".join(item.get("tags", [])).lower() or t in item.get("text", "").lower():
                agg["quotes"].append({"id": idx, "item": item})
        for idx, item in enumerate(repo.assets["structures"]):
            if t in " ".join(item.get("tags", [])).lower() or t in " ".join(item.get("outline", [])).lower():
                agg["structures"].append({"id": idx, "item": item})
    summary = ""
    related_topics = []
    return {"aggregated": agg, "summary": summary, "related_topics": related_topics}
