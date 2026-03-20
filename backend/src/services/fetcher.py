import httpx
import requests

async def fetch_async(url: str, timeout: float = 15.0) -> str:
    """Async fetch using Jina Reader with fallback."""
    # 优先使用 Jina Reader (更稳定，支持微信，直接转Markdown)
    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(jina_url)
            if resp.status_code == 200 and resp.text:
                return resp.text
    except Exception as e:
        print(f"Jina Reader fetch failed: {e}")
    
    # Fallback: 直接请求
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, verify=False) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            # If fallback succeeds, we should ideally use trafilatura to extract text, 
            # but returning raw HTML for now as fallback.
            return resp.text
    except Exception as e:
        print(f"Fallback fetch failed: {e}")
        return ""
