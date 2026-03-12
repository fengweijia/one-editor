from typing import Dict, List
from src.storage.state import repo
from src.config.settings import state
from src.storage.feishu_client import create_records

def store_and_index(analysis: Dict, meta: Dict) -> Dict:
    points = analysis.get("points", [])
    cases = analysis.get("cases", [])
    quotes = analysis.get("quotes", [])
    structure = analysis.get("structure", {})
    tags: List[Dict] = []
    ids = repo.save_assets(analysis)
    fs = state.feishu_settings
    if fs.app_token:
        if fs.table_points and points:
            recs = []
            for p in points:
                recs.append({
                    "article_title": meta.get("title", ""),
                    "point_title": p.get("title", ""),
                    "claim_text": p.get("claim_text", ""),
                    "evidence_text": p.get("evidence_text", ""),
                    "method": p.get("method", ""),
                    "anchors": ",".join(p.get("anchors", [])),
                    "tags": ",".join(p.get("tags", [])),
                })
            create_records(fs.table_points, recs)
        if fs.table_cases and cases:
            recs = []
            for c in cases:
                recs.append({
                    "article_title": meta.get("title", ""),
                    "summary": c.get("summary", ""),
                    "details": c.get("details", ""),
                    "transferable_scenarios": ",".join(c.get("transferable_scenarios", [])),
                    "anchors": ",".join(c.get("anchors", [])),
                    "tags": ",".join(c.get("tags", [])),
                })
            create_records(fs.table_cases, recs)
        if fs.table_quotes and quotes:
            recs = []
            for q in quotes:
                recs.append({
                    "article_title": meta.get("title", ""),
                    "text": q.get("text", ""),
                    "scene": q.get("scene", ""),
                    "anchors": ",".join(q.get("anchors", [])),
                    "tags": ",".join(q.get("tags", [])),
                })
            create_records(fs.table_quotes, recs)
        if fs.table_structures and structure:
            recs = [{
                "article_title": meta.get("title", ""),
                "structure_name": structure.get("structure_name", ""),
                "outline": ",".join(structure.get("outline", [])),
                "techniques": ",".join(structure.get("techniques", [])),
                "anchors": ",".join(structure.get("anchors", [])),
                "tags": ",".join(structure.get("tags", [])),
            }]
            create_records(fs.table_structures, recs)
    persisted = True
    fts_indexed = True
    embeddings_indexed = True
    return {
        "persisted": persisted,
        "asset_ids": ids,
        "tags": tags,
        "fts_indexed": fts_indexed,
        "embeddings_indexed": embeddings_indexed,
    }
