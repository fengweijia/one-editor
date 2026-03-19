"""
通用 URL 抓取服务 - 异步版本支持高并发
支持多个备选方案：Jina Reader → URLtoMarkdown → Playwright → 手动粘贴
"""
import asyncio
import aiohttp
from typing import Tuple, Optional
from loguru import logger
import concurrent.futures


class UniversalFetcher:
    """通用抓取器，支持多种方案自动切换（异步版本）"""
    
    def __init__(self, max_concurrent: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=30.0)
        self.semaphore = asyncio.Semaphore(max_concurrent)  # 并发限制
    
    async def fetch(self, url: str) -> Tuple[str, str, str]:
        """
        尝试多种方案抓取内容（异步）
        Returns: (content, title, method_used)
        """
        async with self.semaphore:  # 并发控制
            # 方案1: Jina Reader (最常用)
            content, title = await self._fetch_jina(url)
            if content:
                logger.info(f"Jina Reader 成功抓取: {url[:50]}...")
                return content, title, "jina"
            
            # 方案2: URLtoMarkdown
            content, title = await self._fetch_url_to_markdown(url)
            if content:
                logger.info(f"URLtoMarkdown 成功抓取: {url[:50]}...")
                return content, title, "url_to_markdown"
            
            # 方案3: Fetch HTML + aiohttp (异步)
            content, title = await self._fetch_html_async(url)
            if content:
                logger.info(f"Async HTML 成功抓取: {url[:50]}...")
                return content, title, "html_async"
            
            # 方案4: Playwright (在线程池中运行，避免阻塞事件循环)
            try:
                content, title = await self._fetch_playwright_thread(url)
                if content:
                    logger.info(f"Playwright 成功抓取: {url[:50]}...")
                    return content, title, "playwright"
            except Exception as e:
                logger.warning(f"Playwright 失败: {e}")
            
            # 全部失败
            logger.error(f"所有抓取方案都失败: {url}")
            return "", "", "failed"
    
    async def _fetch_jina(self, url: str) -> Tuple[str, str]:
        """方案1: Jina Reader (异步)"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"https://r.jina.ai/{url}",
                    headers={"User-Agent": "OneEditorBot/1.0"}
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if text:
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
    
    async def _fetch_url_to_markdown(self, url: str) -> Tuple[str, str]:
        """方案2: URLtoMarkdown API (异步)"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"https://r.jina.ai/{url}",
                    headers={"User-Agent": "OneEditorBot/1.0"}
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if text and len(text) > 100:
                            return text, ""
        except Exception as e:
            logger.warning(f"URLtoMarkdown 失败: {e}")
        return "", ""
    
    async def _fetch_html_async(self, url: str) -> Tuple[str, str]:
        """方案3: 异步 HTTP 请求 + BeautifulSoup"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        
                        # 简单的正文提取
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        # 移除脚本和样式
                        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                            tag.decompose()
                        
                        # 获取标题
                        title = soup.title.string if soup.title else ""
                        
                        # 获取正文
                        content = soup.get_text(separator='\n', strip=True)
                        return content, title
        except Exception as e:
            logger.warning(f"Async HTML 失败: {e}")
        return "", ""
    
    async def _fetch_playwright_thread(self, url: str) -> Tuple[str, str]:
        """方案4: Playwright (在线程池中运行，避免阻塞事件循环)"""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                self._fetch_playwright_sync,
                url
            )
        return result
    
    def _fetch_playwright_sync(self, url: str) -> Tuple[str, str]:
        """Playwright 同步实现（供线程池调用）"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
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


# 全局实例（带并发限制）
_fetcher = UniversalFetcher(max_concurrent=15)  # 支持15用户并发


async def fetch_with_fallback_async(url: str) -> Tuple[str, str, str]:
    """
    异步便捷函数：使用自动备选方案抓取
    Returns: (content, title, method)
    """
    return await _fetcher.fetch(url)


# 同步版本（保留兼容）
def fetch_with_fallback(url: str) -> Tuple[str, str, str]:
    """
    同步便捷函数：使用自动备选方案抓取
    Returns: (content, title, method)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在异步环境中，创建新任务
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(fetch_with_fallback_async(url))
    except RuntimeError:
        # 如果没有 event loop，创建新的
        return asyncio.run(fetch_with_fallback_async(url))