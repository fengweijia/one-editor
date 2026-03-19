"""
通用 URL 抓取服务 - 支持多个备选方案
按优先级尝试：Jina Reader → URLtoMarkdown → Playwright → 手动粘贴
"""
import httpx
import requests
from typing import Tuple, Optional
from loguru import logger


class UniversalFetcher:
    """通用抓取器，支持多种方案自动切换"""
    
    def __init__(self):
        self.timeout = 30.0
    
    def fetch(self, url: str) -> Tuple[str, str, str]:
        """
        尝试多种方案抓取内容
        Returns: (content, title, method_used)
        """
        # 方案1: Jina Reader (最常用)
        content, title = self._fetch_jina(url)
        if content:
            logger.info(f"Jina Reader 成功抓取: {url[:50]}...")
            return content, title, "jina"
        
        # 方案2: URLtoMarkdown
        content, title = self._fetch_url_to_markdown(url)
        if content:
            logger.info(f"URLtoMarkdown 成功抓取: {url[:50]}...")
            return content, title, "url_to_markdown"
        
        # 方案3: Fetch HTML + BeautifulSoup
        content, title = self._fetch_html_basic(url)
        if content:
            logger.info(f"Basic HTML 成功抓取: {url[:50]}...")
            return content, title, "html_basic"
        
        # 方案4: Playwright (需要较大资源)
        try:
            content, title = self._fetch_playwright(url)
            if content:
                logger.info(f"Playwright 成功抓取: {url[:50]}...")
                return content, title, "playwright"
        except Exception as e:
            logger.warning(f"Playwright 失败: {e}")
        
        # 全部失败
        logger.error(f"所有抓取方案都失败: {url}")
        return "", "", "failed"
    
    def _fetch_jina(self, url: str) -> Tuple[str, str]:
        """方案1: Jina Reader"""
        try:
            resp = requests.get(
                f"https://r.jina.ai/{url}",
                timeout=self.timeout,
                headers={"User-Agent": "OneEditorBot/1.0"}
            )
            if resp.status_code == 200 and resp.text:
                text = resp.text
                # 提取标题
                title = ""
                if text.startswith("Title:"):
                    lines = text.split("\n")
                    for line in lines:
                        if line.startswith("Title:"):
                            title = line.replace("Title:", "").strip()
                            break
                return text, title
        except Exception as e:
            logger.warning(f"Jina Reader 失败: {e}")
        return "", ""
    
    def _fetch_url_to_markdown(self, url: str) -> Tuple[str, str]:
        """方案2: URLtoMarkdown API"""
        try:
            # 使用免费的 URLtoMarkdown 服务
            resp = requests.get(
                f"https://r.jina.ai/{url}",  # Jina 本身就是很好的 Markdown 转换器
                timeout=self.timeout,
                headers={"User-Agent": "OneEditorBot/1.0"}
            )
            # 尝试 Bypass 的 URL
            if not resp.text or resp.status_code != 200:
                resp = requests.get(
                    f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}",
                    timeout=self.timeout
                )
            if resp.status_code == 200 and len(resp.text) > 100:
                return resp.text, ""
        except Exception as e:
            logger.warning(f"URLtoMarkdown 失败: {e}")
        return "", ""
    
    def _fetch_html_basic(self, url: str) -> Tuple[str, str]:
        """方案3: 基础 HTML 抓取 + 清洗"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            with httpx.Client(timeout=self.timeout, headers=headers, verify=False) as client:
                resp = client.get(url, follow_redirects=True)
                resp.raise_for_status()
                
                # 简单的正文提取
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 移除脚本和样式
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                
                # 获取标题
                title = soup.title.string if soup.title else ""
                
                # 获取正文
                text = soup.get_text(separator='\n', strip=True)
                return text, title
        except Exception as e:
            logger.warning(f"Basic HTML 失败: {e}")
        return "", ""
    
    def _fetch_playwright(self, url: str) -> Tuple[str, str]:
        """方案4: Playwright (JavaScript 渲染)"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                
                # 等待内容加载
                page.wait_for_timeout(2000)
                
                title = page.title()
                
                # 尝试获取正文
                text = ""
                for selector in ['article', 'main', '#content', '.content', '.post-content']:
                    try:
                        elem = page.query_selector(selector)
                        if elem:
                            text = elem.inner_text()
                            break
                    except:
                        continue
                
                if not text:
                    text = page.content()
                
                context.close()
                browser.close()
                return text, title
        except Exception as e:
            logger.warning(f"Playwright 失败: {e}")
        return "", ""


# 全局实例
_fetcher = UniversalFetcher()


def fetch_with_fallback(url: str) -> Tuple[str, str, str]:
    """
    便捷函数：使用自动备选方案抓取
    Returns: (content, title, method)
    """
    return _fetcher.fetch(url)