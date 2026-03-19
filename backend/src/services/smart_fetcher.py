"""
智能 URL 抓取服务
支持多个备选方案：Jina Reader -> Playwright(微信) -> 通用请求 -> 手动粘贴提示
"""
from typing import Tuple, Optional
import requests
import httpx

class FetchResult:
    def __init__(self, success: bool, content: str = "", title: str = "", error: str = "", method: str = ""):
        self.success = success
        self.content = content
        self.title = title
        self.error = error
        self.method = method

def fetch_with_jina(url: str) -> FetchResult:
    """方案1: Jina Reader (最常用)"""
    try:
        resp = requests.get(f"https://r.jina.ai/{url}", timeout=15.0)
        if resp.status_code == 200 and resp.text:
            # 解析 title
            title = ""
            lines = resp.text.split('\n')
            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                    break
            return FetchResult(
                success=True,
                content=resp.text,
                title=title,
                method="jina"
            )
    except Exception as e:
        pass
    return FetchResult(success=False, error=str(e), method="jina")

def fetch_with_playwright(url: str) -> FetchResult:
    """方案2: Playwright (用于微信等需要 JavaScript 的网站)"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # 尝试获取微信内容
            text = ""
            title = ""
            try:
                page.wait_for_selector("#js_content", timeout=5000)
                elem = page.query_selector("#js_content")
                if elem:
                    text = (elem.inner_text() or "").strip()
            except:
                pass
            
            try:
                t = page.query_selector("#activity-name")
                if t:
                    title = (t.inner_text() or "").strip()
            except:
                pass
                
            context.close()
            browser.close()
            
            if text:
                return FetchResult(
                    success=True,
                    content=text,
                    title=title,
                    method="playwright"
                )
    except Exception as e:
        pass
    return FetchResult(success=False, error=str(e), method="playwright")

def fetch_with_direct(url: str) -> FetchResult:
    """方案3: 直接请求 (通用)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(timeout=15.0, headers=headers, verify=False) as client:
            resp = client.get(url, follow_redirects=True)
            resp.raise_for_status()
            
            # 尝试提取 title
            title = ""
            import re
            title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            
            return FetchResult(
                success=True,
                content=resp.text,
                title=title,
                method="direct"
            )
    except Exception as e:
        return FetchResult(success=False, error=str(e), method="direct")

def detect_url_type(url: str) -> str:
    """检测 URL 类型"""
    url_lower = url.lower()
    if "mp.weixin.qq.com" in url_lower:
        return "wechat"
    elif "zhihu.com" in url_lower or "zhuanlan.zhihu.com" in url_lower:
        return "zhihu"
    elif "36kr.com" in url_lower:
        return "36kr"
    elif "juejin.cn" in url_lower:
        return "juejin"
    elif "xiaohongshu.com" in url_lower:
        return "xiaohongshu"
    else:
        return "general"

def smart_fetch(url: str) -> FetchResult:
    """
    智能抓取：自动选择最佳方案
    
    返回 FetchResult:
    - success: 是否成功
    - content: 提取的内容
    - title: 页面标题
    - error: 错误信息（如果失败）
    - method: 使用的抓取方案
    """
    url_type = detect_url_type(url)
    
    # 根据 URL 类型选择策略
    if url_type == "wechat":
        # 微信：优先 Playwright -> Jina -> Direct
        result = fetch_with_playwright(url)
        if not result.success:
            result = fetch_with_jina(url)
        if not result.success:
            result = fetch_with_direct(url)
        return result
    
    elif url_type in ["zhihu", "36kr", "juejin", "xiaohongshu"]:
        # 其他需要 JavaScript 的网站：Jina -> Playwright -> Direct
        result = fetch_with_jina(url)
        if not result.success:
            result = fetch_with_playwright(url)
        if not result.success:
            result = fetch_with_direct(url)
        return result
    
    else:
        # 通用：Jina -> Direct -> Playwright
        result = fetch_with_jina(url)
        if not result.success:
            result = fetch_with_direct(url)
        if not result.success:
            result = fetch_with_playwright(url)
        return result

# 为了兼容旧代码
def fetch(url: str, timeout: float = 15.0) -> str:
    """旧接口兼容"""
    result = smart_fetch(url)
    return result.content if result.success else ""