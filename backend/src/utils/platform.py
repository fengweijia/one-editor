from typing import Dict, Optional
from urllib.parse import urlparse

def detect(url: str, html: Optional[str] = None) -> Dict:
    netloc = urlparse(url).netloc.lower()
    platform = "web"
    selectors = {}
    confidence = 0.5
    if "mp.weixin.qq.com" in netloc:
        platform = "wechat"
        selectors = {"content": "#js_content", "title": "#activity-name"}
        confidence = 0.9
    elif "zhihu.com" in netloc:
        platform = "zhihu"
        selectors = {"content": ".Post-RichText", "title": ".Post-Title"}
        confidence = 0.8
    return {"platform": platform, "selectors": selectors, "confidence": confidence}
