from typing import Tuple
from playwright.sync_api import sync_playwright

def fetch_rendered_wechat(url: str, timeout_ms: int = 20000) -> Tuple[str, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        title = ""
        text = ""
        try:
            page.wait_for_selector("#js_content", timeout=timeout_ms)
            elem = page.query_selector("#js_content")
            if elem:
                text = (elem.inner_text() or "").strip()
        except Exception:
            pass
        try:
            t = page.query_selector("#activity-name")
            if t:
                title = (t.inner_text() or "").strip()
        except Exception:
            pass
        context.close()
        browser.close()
        return text, title
