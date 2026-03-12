from typing import List, Optional, Dict, Any
from src.storage.state import repo
from src.config.settings import state
from src.storage.feishu_client import list_records

def search(q: str, tags: Optional[List[str]] = None, type: Optional[str] = None, semantic: bool = False, filters: Optional[Dict[str, Any]] = None) -> Dict:
    results: List[Dict[str, Any]] = []
    corpus = []
    fs = state.feishu_settings
    if fs.app_token:
        if type in (None, "points") and fs.table_points:
            r = list_records(fs.table_points, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    corpus.append({"type": "points", "text": f.get("claim_text", "") or "", "ref": rec.get("record_id", ""), "raw": f})
        if type in (None, "cases") and fs.table_cases:
            r = list_records(fs.table_cases, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    corpus.append({"type": "cases", "text": f.get("details", "") or "", "ref": rec.get("record_id", ""), "raw": f})
        if type in (None, "quotes") and fs.table_quotes:
            r = list_records(fs.table_quotes, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    corpus.append({"type": "quotes", "text": f.get("text", "") or "", "ref": rec.get("record_id", ""), "raw": f})
        if type in (None, "structures") and fs.table_structures:
            r = list_records(fs.table_structures, page_size=100)
            if r.get("success"):
                for rec in r["data"].get("data", {}).get("items", []):
                    f = rec.get("fields", {})
                    corpus.append({"type": "structures", "text": f.get("outline", "") or "", "ref": rec.get("record_id", ""), "raw": f})
    else:
        if type in (None, "points"):
            corpus.extend([{"type": "points", "text": item.get("claim_text", ""), "ref": idx} for idx, item in enumerate(repo.assets["points"])])
        if type in (None, "cases"):
            corpus.extend([{"type": "cases", "text": item.get("details", ""), "ref": idx} for idx, item in enumerate(repo.assets["cases"])])
        if type in (None, "quotes"):
            corpus.extend([{"type": "quotes", "text": item.get("text", ""), "ref": idx} for idx, item in enumerate(repo.assets["quotes"])])
        if type in (None, "structures"):
            corpus.extend([{"type": "structures", "text": " ".join(item.get("outline", [])), "ref": idx} for idx, item in enumerate(repo.assets["structures"])])
    ql = q.lower()
    for item in corpus:
        text = item["text"]
        if ql and ql in text.lower():
            results.append({"asset_ref": {"type": item["type"], "id": item["ref"]}, "score": 1.0, "highlights": text[:200], "reason": "keyword"})
    return {"results": results}
