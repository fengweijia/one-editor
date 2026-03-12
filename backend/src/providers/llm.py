from typing import Dict, Any, Optional, List
import httpx
from src.config.settings import state

def build_prompt(normalized_text: str, segments: List[Dict[str, Any]]) -> str:
    seg_lines = []
    for s in segments[:120]:
        sid = s.get("id")
        stxt = (s.get("text") or "").strip()
        if len(stxt) > 600:
            stxt = stxt[:600] + "..."
        if sid:
            seg_lines.append(f"- {sid}: {stxt}")
    seg_block = "\n".join(seg_lines)
    return (
        "你是一名“对话知识萃取师”，负责把一段非结构化文本（文章或对话）"
        "转化为结构化的知识资产。你必须只输出一个 JSON 对象，不要输出解释文字，不要使用 Markdown 代码块。\n\n"
        "已为你预先切分了段落片段（anchors 只能从这些 id 中选择）：\n"
        f"{seg_block}\n\n"
        "你的输出 JSON 必须包含以下键：summary_one_line, points, cases, quotes, structure, extensions。\n"
        "字段规范：\n"
        "- summary_one_line: 一句话总结\n"
        "- points: [{title, claim_text, evidence_text, method, anchors: [segment_id], tags: [tag]}]\n"
        "- cases: [{summary, details, transferable_scenarios: [scenario], anchors: [segment_id], tags: [tag]}]\n"
        "- quotes: [{text(必须为原文), scene, anchors: [segment_id], tags: [tag]}]\n"
        "- structure: {structure_name, outline:[node], techniques:[t], anchors:[segment_id], tags:[tag]}\n"
        "- extensions: [{idea, description, anchors:[segment_id]}]\n\n"
        "规则：\n"
        "- 忠于原意，金句必须原文\n"
        "- anchors 必须来自上面的段 id，禁止编造\n"
        "- 不确定时返回空数组，不要瞎填\n\n"
        "全文原文如下（供理解用）：\n" + normalized_text
    )

class LLMProvider:
    def analyze(self, text: str, meta: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        return None

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, profile: Any):
        self.profile = profile

    def analyze(self, text: str, meta: Dict[str, Any], platform: str, segments: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        p = self.profile
        if not p.api_key:
            return None
        max_chars = 8000
        use_text = text if len(text) <= max_chars else text[:max_chars]
        segs = segments or []
        base = (p.base_url or "https://api.openai.com/v1").rstrip("/")
        endpoint = f"{base}/chat/completions"
        model_id = p.model_id or "gpt-4o-mini"
        prompt = build_prompt(use_text, segs)
        payload: Dict[str, Any] = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You must output a single valid JSON object and nothing else."},
                {"role": "user", "content": prompt},
            ],
        }
        if (p.api or "openai-chat") == "openai-chat":
            payload["response_format"] = {"type": "json_object"}
        payload["temperature"] = 0.2
        payload["max_tokens"] = 2000
        headers = {"Authorization": f"Bearer {p.api_key}"}
        last_error: Optional[str] = None
        try:
            with httpx.Client(timeout=60.0) as c:
                for attempt in range(2):
                    try:
                        r = c.post(endpoint, json=payload, headers=headers)
                        r.raise_for_status()
                        data = r.json()
                        content = data["choices"][0]["message"]["content"]
                        import json, re
                        txt = content.strip()
                    except Exception as e:
                        last_error = str(e)
                        # some providers reject response_format; retry once without it
                        if attempt == 0 and "response_format" in payload:
                            payload.pop("response_format", None)
                            continue
                        return None
                if txt.startswith("```"):
                    # strip fenced code block
                    txt = re.sub(r"^```[a-zA-Z0-9]*\s*", "", txt)
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    txt = txt.strip()
                def _loads(s: str):
                    try:
                        return json.loads(s)
                    except Exception:
                        start = s.find("{")
                        end = s.rfind("}")
                        if start != -1 and end != -1 and end > start:
                            try:
                                return json.loads(s[start:end+1])
                            except Exception:
                                return None
                        return None
                obj = _loads(txt)
                if isinstance(obj, dict):
                    return obj
                return None
        except Exception:
            return None

def get_provider() -> Optional[LLMProvider]:
    cfg = state.model_config
    if not cfg.active or cfg.active not in cfg.profiles:
        return None
    p = cfg.profiles[cfg.active]
    if not p.api_key:
        return None
    # currently support OpenAI-compatible chat endpoints (OpenAI, SiliconFlow, DeepSeek 等)
    return OpenAICompatibleProvider(p)
