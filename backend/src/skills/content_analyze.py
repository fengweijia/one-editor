import re
from typing import Dict, List, Any
from src.providers.llm import get_provider

def analyze_content(text: str, meta: Dict, platform: str) -> Dict:
    parts = [p for p in (text or "").split("\n\n") if p.strip()]
    provider = get_provider()
    segments: List[Dict] = []
    offset = 0
    for idx, p in enumerate(parts):
        seg_id = f"s{idx}"
        start = offset
        end = start + len(p)
        segments.append({"id": seg_id, "idx": idx, "text": p, "start_offset": start, "end_offset": end, "type": "paragraph"})
        offset = end + 2
    base: Dict[str, Any] = {
        "segments": segments,
        "summary_one_line": "",
        "points": [],
        "cases": [],
        "quotes": [],
        "structure": {"structure_name": "", "outline": [], "techniques": [], "anchors": [], "tags": []},
        "extensions": [],
    }
    if provider:
        llm_result = provider.analyze(text or "", meta or {}, platform or "web", segments)
        if isinstance(llm_result, dict):
            out = {**base, **llm_result}
            out["segments"] = segments
            valid_ids = {s["id"] for s in segments}

            def _clean_anchors(a):
                if not isinstance(a, list):
                    return []
                return [x for x in a if isinstance(x, str) and x in valid_ids]

            def _clean_list(items, key_fields):
                if not isinstance(items, list):
                    return []
                cleaned = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    for k in key_fields:
                        if k not in it:
                            it[k] = "" if k not in ("anchors", "tags", "transferable_scenarios") else []
                    if "anchors" in it:
                        it["anchors"] = _clean_anchors(it.get("anchors"))
                    if "tags" in it and not isinstance(it.get("tags"), list):
                        it["tags"] = []
                    cleaned.append(it)
                return cleaned

            out["points"] = _clean_list(out.get("points"), ["title", "claim_text", "evidence_text", "method", "anchors", "tags"])
            out["cases"] = _clean_list(out.get("cases"), ["summary", "details", "transferable_scenarios", "anchors", "tags"])
            out["quotes"] = _clean_list(out.get("quotes"), ["text", "scene", "anchors", "tags"])
            exts = out.get("extensions")
            if isinstance(exts, list):
                for e in exts:
                    if isinstance(e, dict):
                        if "anchors" in e:
                            e["anchors"] = _clean_anchors(e.get("anchors"))
                out["extensions"] = exts
            else:
                out["extensions"] = []
            st = out.get("structure")
            if not isinstance(st, dict):
                st = base["structure"]
            st["anchors"] = _clean_anchors(st.get("anchors"))
            if not isinstance(st.get("outline"), list):
                st["outline"] = []
            if not isinstance(st.get("techniques"), list):
                st["techniques"] = []
            if not isinstance(st.get("tags"), list):
                st["tags"] = []
            out["structure"] = st

            if not out.get("summary_one_line") and isinstance(out.get("response"), str):
                out["summary_one_line"] = out["response"].strip()
            s = out.get("summary_one_line") or ""
            if isinstance(s, str):
                s = s.strip()
            else:
                s = ""
            if len(s) <= 2 or re.fullmatch(r"[:：，,。.!！？?]+", s or ""):
                out["summary_one_line"] = ""
            if out.get("summary_one_line"):
                if not out["points"] and segments:
                    out["points"] = [{
                        "title": "要点摘要",
                        "claim_text": out["summary_one_line"],
                        "evidence_text": "",
                        "method": "",
                        "anchors": [segments[0]["id"]],
                        "tags": [],
                    }]
                return out
            if out["points"] or out["cases"] or out["quotes"] or out["structure"].get("outline"):
                return out

    if segments:
        first = segments[0]["text"].strip()
        sent = re.split(r"[。！？!?]\s*", first)[0].strip()
        base["summary_one_line"] = sent[:120] if sent else first[:120]
        if not base["points"]:
            base["points"] = [{
                "title": "要点摘要",
                "claim_text": base["summary_one_line"],
                "evidence_text": "",
                "method": "",
                "anchors": [segments[0]["id"]],
                "tags": [],
            }]
    return base
