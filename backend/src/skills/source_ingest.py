from typing import Optional, Dict
from src.utils.platform import detect
from src.services.fetcher import fetch
from src.services.extractor import extract_main
from src.utils.hash import checksum as calc_checksum
from src.storage.state import repo
from src.services.dynamic_fetcher import fetch_rendered_wechat
from src.services.universal_client import fetch_universal_text
from src.config.settings import state

def ingest_url(url: str) -> Dict:
    det = detect(url)
    platform = det["platform"]
    canonical_url = url
    
    # 优先使用 Jina Reader 进行抓取（支持微信）
    html = fetch(url)
    
    # 如果Jina Reader失败，使用universal_client
    if not html or len(html) < 100:
        try:
            html, title = fetch_universal_text(url)
            if html:
                return {
                    "platform": platform,
                    "canonical_url": url,
                    "meta": {"title": title or "", "author": "", "publish_at": None, "language": "zh"},
                    "normalized_text": html,
                    "snapshot_uri": "",
                    "checksum": calc_checksum(html) if html else "",
                    "duplicated": False,
                    "status": "success"
                }
        except Exception:
            pass
        
        return {"platform": platform, "canonical_url": url, "status": "error", "message": "抓取失败"}
    
    try:
        from src.services.extractor import extract_from_markdown
        normalized_text = extract_from_markdown(html).get("content_text", "")
    except:
        normalized_text = html
    
    meta = {"title": "", "author": "", "publish_at": None, "language": "zh"}
    
    # 如果是Jina Reader返回的格式，尝试提取标题
    if "Title:" in html:
        for line in html.split('\n'):
            if line.startswith("Title:"):
                meta["title"] = line.replace("Title:", "").strip()
                break
    
    snapshot_uri = ""
    cs = calc_checksum(normalized_text) if normalized_text else ""
    duplicated = bool(cs and repo.has_article(cs))
    article = {
        "platform": platform,
        "canonical_url": canonical_url,
        "meta": meta,
        "normalized_text": normalized_text,
        "snapshot_uri": snapshot_uri,
        "checksum": cs,
    }
    if cs and not duplicated:
        repo.save_article(cs, article)
    article["duplicated"] = duplicated
    return article

def ingest_text(text: str, meta: Optional[Dict] = None) -> Dict:
    canonical_url = None
    normalized_text = text.strip()
    cs = calc_checksum(normalized_text) if normalized_text else ""
    duplicated = bool(cs and repo.has_article(cs))
    article = {
        "platform": "manual",
        "canonical_url": canonical_url,
        "meta": meta or {},
        "normalized_text": normalized_text,
        "snapshot_uri": "",
        "checksum": cs,
        "duplicated": duplicated,
    }
    if cs and not duplicated:
        repo.save_article(cs, article)
    return article
