import httpx
import requests

def fetch(url: str, timeout: float = 15.0) -> str:
    # 优先使用 Jina Reader (更稳定，支持微信)
    try:
        resp = requests.get(f"https://r.jina.ai/{url}", timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return resp.text
    except Exception:
        pass
    
    # Fallback: 直接请求 (跳过SSL验证)
    headers = {"User-Agent": "OneEditorBot/0.1"}
    try:
        with httpx.Client(timeout=timeout, headers=headers, verify=False) as client:
            resp = client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        return ""
