from typing import Dict, Optional

def fallback(text: str, meta: Optional[Dict] = None) -> Dict:
    normalized_text = text.strip()
    return {"normalized_text": normalized_text, "meta": meta or {}}
