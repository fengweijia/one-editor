from typing import Dict
import trafilatura

def extract_main(html: str) -> Dict:
    # 如果是Jina Reader的Markdown格式，直接返回
    if "Title:" in html or "# " in html:
        return extract_from_markdown(html)
    
    downloaded = trafilatura.extract(html, include_comments=False, include_tables=False)
    text = downloaded or ""
    meta = {"title": "", "author": "", "publish_at": None, "language": "zh"}
    return {"content_text": text, "content_html": html, "meta": meta}

def extract_from_markdown(markdown_text: str) -> Dict:
    """处理Jina Reader返回的Markdown格式"""
    lines = markdown_text.split('\n')
    title = ""
    content_lines = []
    in_content = False
    
    for line in lines:
        if line.startswith("Title:"):
            title = line.replace("Title:", "").strip()
        elif line.startswith("URL Source:") or line.startswith("Published Time:"):
            continue
        elif line.startswith("Warning:"):
            continue
        elif line.strip():
            in_content = True
            content_lines.append(line)
    
    return {
        "content_text": '\n'.join(content_lines),
        "content_html": markdown_text,
        "meta": {"title": title, "author": "", "publish_at": None, "language": "zh"}
    }
