from typing import Tuple, Optional, Dict, Any
import httpx
import json
from src.config.settings import state
from src.services.extractor import extract_main
from src.utils.markdown import strip_images_markdown

def fetch_universal_text(url: str) -> Tuple[str, Optional[str]]:
    """
    Calls a user-configured universal scraping service.
    Expected behavior:
    - POST { url } to endpoint with Authorization: Bearer <token>
    - Response may be JSON with keys like markdown|content_markdown|text|html or plain text
    Returns (text, title) where text is plain/markdown without images.
    """
    u = state.universal_settings
    if not u.endpoint or not u.token:
        return "", None
    headers = {"Authorization": f"Bearer {u.token}"}
    try:
        with httpx.Client(timeout=30.0, headers=headers) as c:
            r = c.post(u.endpoint, json={"url": url})
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            title: Optional[str] = None
            if "application/json" in ct:
                data = r.json()
                text = data.get("markdown") or data.get("content_markdown")
                if not text:
                    if data.get("text"):
                        text = data.get("text")
                    elif data.get("html"):
                        # run local extractor on html
                        ex = extract_main(data.get("html"))
                        text = ex.get("content_text") or ""
                        if not title:
                            title = (ex.get("meta") or {}).get("title")
                title = title or data.get("title")
            else:
                raw = r.text
                # Try to parse as JSON string containing markdown
                text = None
                try:
                    obj = json.loads(raw)
                    text = obj.get("markdown") or obj.get("content") or obj.get("text")
                    title = obj.get("title")
                except Exception:
                    # treat as plain text
                    text = raw
            if not text:
                return "", title
            if u.prefer_markdown:
                text = strip_images_markdown(text)
            return text, title
    except Exception:
        return "", None
