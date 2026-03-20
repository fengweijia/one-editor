from typing import Dict, Any, Optional, List
import httpx
import json
import re
from src.config.settings import state
from src.models.schemas import LLMExtractionResult

def build_prompt(normalized_text: str) -> str:
    return (
        "你是一名“对话知识萃取师”，负责把一段非结构化文本（文章或对话）"
        "转化为结构化的知识资产。你必须严格按照提供的 JSON Schema 输出，不要输出解释文字，不要使用 Markdown 代码块。\n\n"
        "你的输出 JSON 必须符合以下要求：\n"
        "- quality_rating: 对原文的质量评分(1-10)及论证是否扎实的评价，如果有论证薄弱的地方必须在 concerns 中指出，不要美化原文。\n"
        "- structured_analysis: 提炼3-5个核心观点（包含论点、论据、写作手法），生成分类标签，以及建议的写作方向。\n"
        "- raw_essence: 提取原文中的金句和案例。金句必须是原文，不能改写，并提供上下文。案例需包含总结、细节和可借用的角度。\n\n"
        "规则：\n"
        "- 忠于原意，金句必须原文\n"
        "- 必须指出原文的逻辑漏洞（如果有）\n\n"
        "全文原文如下（供理解用）：\n" + normalized_text
    )

class LLMProvider:
    async def analyze_async(self, text: str, meta: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        return None

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, profile: Any):
        self.profile = profile

    async def analyze_async(self, text: str, meta: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        p = self.profile
        if not p.api_key:
            return None
        max_chars = 12000
        use_text = text if len(text) <= max_chars else text[:max_chars]
        base = (p.base_url or "https://api.openai.com/v1").rstrip("/")
        endpoint = f"{base}/chat/completions"
        model_id = p.model_id or "gpt-4o-mini"
        prompt = build_prompt(use_text)
        
        # 使用 Pydantic 的 model_json_schema 强制约束输出
        schema = LLMExtractionResult.model_json_schema()
        
        payload: Dict[str, Any] = {
            "model": model_id,
            "messages": [
                {
                    "role": "system", 
                    "content": f"You must output a single valid JSON object that strictly adheres to the following JSON schema:\n{json.dumps(schema)}\nDo not include any extra text."
                },
                {"role": "user", "content": prompt},
            ],
        }
        
        # Some providers support response_format for strict JSON output
        if (p.api or "openai-chat") == "openai-chat":
            payload["response_format"] = {"type": "json_object"}
            
        payload["temperature"] = 0.2
        payload["max_tokens"] = 3000
        headers = {"Authorization": f"Bearer {p.api_key}"}
        
        async with httpx.AsyncClient(timeout=120.0) as c:
            for attempt in range(2):
                try:
                    r = await c.post(endpoint, json=payload, headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    txt = content.strip()
                    
                    if txt.startswith("```"):
                        txt = re.sub(r"^```[a-zA-Z0-9]*\s*", "", txt)
                        if txt.endswith("```"):
                            txt = txt[:-3]
                        txt = txt.strip()
                        
                    # 尝试用 Pydantic 验证
                    parsed_obj = json.loads(txt)
                    validated_result = LLMExtractionResult(**parsed_obj)
                    return validated_result.model_dump()
                    
                except Exception as e:
                    print(f"LLM Extraction failed on attempt {attempt}: {e}")
                    if attempt == 0 and "response_format" in payload:
                        payload.pop("response_format", None)
                        continue
            return None

def get_provider() -> Optional[LLMProvider]:
    cfg = state.model_config
    if not cfg.active or cfg.active not in cfg.profiles:
        return None
    p = cfg.profiles[cfg.active]
    if not p.api_key:
        return None
    return OpenAICompatibleProvider(p)
