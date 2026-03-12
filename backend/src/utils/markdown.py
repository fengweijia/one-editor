import re

_IMG_MD = re.compile(r'!\[[^\]]*\]\([^)]+\)')
_IMG_HTML = re.compile(r'<img\b[^>]*>', flags=re.IGNORECASE)

def strip_images_markdown(text: str) -> str:
    text = _IMG_MD.sub('', text)
    text = _IMG_HTML.sub('', text)
    return text
