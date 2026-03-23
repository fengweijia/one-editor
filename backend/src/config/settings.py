import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None


class ModelConfig(BaseModel):
    active: Optional[str] = None
    profiles: Dict[str, ModelProfile] = Field(default_factory=dict)


class UniversalSettings(BaseModel):
    endpoint: Optional[str] = None
    token: Optional[str] = None
    prefer_markdown: bool = True


class ExtractTypeConfig(BaseModel):
    name: str  # 如 "观点", "案例", "金句"
    enabled: bool = True
    prompt: str  # 提取的 prompt


class ExtractConfig(BaseModel):
    types: list[ExtractTypeConfig] = []


class FeishuSettings(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    app_token: Optional[str] = None
    table_points: Optional[str] = None
    table_cases: Optional[str] = None
    table_quotes: Optional[str] = None
    table_structures: Optional[str] = None
    default_table_id: Optional[str] = None
    tenant_token: Optional[str] = None
    tenant_token_expire_ts: Optional[int] = None


DEFAULT_EXTRACT_CONFIG = ExtractConfig(types=[
    ExtractTypeConfig(name="观点", enabled=True, prompt="请从文章中提取核心观点。每个观点需要包含：title（观点标题）、claim_text（观点内容）、evidence_text（支撑证据）。只输出观点，不要案例和金句。"),
    ExtractTypeConfig(name="案例", enabled=True, prompt="请从文章中提取具体案例。每个案例需要包含：summary（案例摘要）、details（案例详情）。只输出案例，不要观点和金句。"),
    ExtractTypeConfig(name="金句", enabled=True, prompt="请从文章中提取金句。原句原文引用，并标注适用场景。只输出金句，不要观点和案例。"),
])


class State:
    def __init__(self):
        self.model_config = ModelConfig()
        self.feishu_settings = FeishuSettings()
        self.universal_settings = UniversalSettings()
        self.extract_config = DEFAULT_EXTRACT_CONFIG


state = State()

# Paths
_SETTINGS_PATH = Path(__file__).resolve().parents[2] / ".oneeditor" / "settings.json"


def _find_legacy_config() -> Optional[Path]:
    """Find legacy config.json in possible locations."""
    possible_paths = [
        # backend/config.json (when running from project root)
        Path(__file__).resolve().parents[2] / "backend" / "config.json",
        # config.json (when running from backend dir)
        Path(__file__).resolve().parents[1] / "config.json",
        # ../config.json (direct parent)
        Path(__file__).resolve().parents[2] / "config.json",
    ]
    for p in possible_paths:
        if p.exists():
            return p
    return None


def _get_default_extract_types():
    return [
        {"name": "观点", "enabled": True, "prompt": "请从文章中提取核心观点。每个观点需要包含：title（观点标题）、claim_text（观点内容）、evidence_text（支撑证据）。只输出观点，不要案例和金句。"},
        {"name": "案例", "enabled": True, "prompt": "请从文章中提取具体案例。每个案例需要包含：summary（案例摘要）、details（案例详情）。只输出案例，不要观点和金句。"},
        {"name": "金句", "enabled": True, "prompt": "请从文章中提取金句。原句原文引用，并标注适用场景。只输出金句，不要观点和案例。"},
    ]


def _save_state() -> None:
    try:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        feishu_dict = state.feishu_settings.model_dump()
        # Ensure default_table_id is included
        if hasattr(state.feishu_settings, "default_table_id"):
            feishu_dict["default_table_id"] = state.feishu_settings.default_table_id
        data = {
            "model_config": state.model_config.model_dump(),
            "feishu_settings": feishu_dict,
            "universal_settings": state.universal_settings.model_dump(),
            "extract_config": {
                "types": _get_default_extract_types()
            }
        }
        _SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return


def _migrate_legacy_config() -> bool:
    """Migrate legacy backend/config.json to new format if it exists."""
    legacy_path = _find_legacy_config()
    if legacy_path is None:
        return False
    try:
        raw = json.loads(legacy_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return False

        # Migrate model config from legacy format
        legacy_model = raw.get("model", {})
        if legacy_model:
            profile_id = legacy_model.get("profile_id") or legacy_model.get("provider") or "default"
            profile = ModelProfile(
                provider=legacy_model.get("provider"),
                base_url=legacy_model.get("base_url"),
                api=legacy_model.get("api"),
                api_key=legacy_model.get("api_key"),
                model_id=legacy_model.get("model", {}).get("id"),
                model_name=legacy_model.get("model", {}).get("name"),
            )
            state.model_config.profiles[profile_id] = profile
            state.model_config.active = profile_id

        # Migrate feishu config from legacy format
        legacy_feishu = raw.get("feishu", {})
        if legacy_feishu:
            # Extract clean table_id (remove view params like &view=...)
            table_id = legacy_feishu.get("table_id", "")
            if table_id and "&" in table_id:
                table_id = table_id.split("&")[0]

            state.feishu_settings = FeishuSettings(
                app_id=legacy_feishu.get("app_id"),
                app_secret=legacy_feishu.get("app_secret"),
                app_token=legacy_feishu.get("app_token"),
                default_table_id=table_id,
                table_points=table_id,
                table_cases=table_id,
                table_quotes=table_id,
                table_structures=table_id,
            )

        # Save migrated config to new format
        _save_state()
        return True
    except Exception as e:
        print(f"Failed to migrate legacy config: {e}")
        return False


def _load_state() -> None:
    if _SETTINGS_PATH.exists():
        try:
            raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                if isinstance(raw.get("model_config"), dict):
                    state.model_config = ModelConfig(**raw["model_config"])
                if isinstance(raw.get("feishu_settings"), dict):
                    feishu_data = raw["feishu_settings"]
                    state.feishu_settings = FeishuSettings(**feishu_data)
                    if "default_table_id" in feishu_data:
                        state.feishu_settings.default_table_id = feishu_data["default_table_id"]
                if isinstance(raw.get("universal_settings"), dict):
                    state.universal_settings = UniversalSettings(**raw["universal_settings"])
            return
        except Exception:
            pass

    # Try migrating legacy config if new config doesn't exist or failed to load
    _migrate_legacy_config()


_load_state()


def set_model_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    provider = payload.get("provider") or "openai"
    api_id = payload.get("api_id") or provider
    api_key = payload.get("api_key")
    cfg = state.model_config
    profile = cfg.profiles.get(api_id) or ModelProfile()
    profile.provider = provider
    profile.api_key = api_key or profile.api_key
    # sane defaults for known providers
    if not profile.base_url:
        if provider == "openai":
            profile.base_url = "https://api.openai.com/v1"
        elif provider == "siliconflow":
            profile.base_url = "https://api.siliconflow.cn/v1"
    if not profile.api:
        profile.api = "openai-chat"
    if not profile.model_id:
        profile.model_id = "gpt-4o-mini"
        profile.model_name = "GPT-4o Mini"
    cfg.profiles[api_id] = profile
    cfg.active = api_id
    _save_state()
    return {"ok": True, "active": api_id}


def get_model_settings_public() -> Dict[str, Any]:
    cfg = state.model_config
    if not cfg.active or cfg.active not in cfg.profiles:
        return {"provider": None, "has_key": False, "api_id": False}
    p = cfg.profiles[cfg.active]
    return {"provider": p.provider, "has_key": bool(p.api_key), "api_id": True}


def set_model_settings_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = ModelConfig(**payload)
    state.model_config = cfg
    _save_state()
    return {"ok": True}


def get_model_settings_json() -> Dict[str, Any]:
    return state.model_config.model_dump()


def set_feishu_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    s = state.feishu_settings
    s.app_id = payload.get("app_id") or s.app_id
    s.app_secret = payload.get("app_secret") or s.app_secret
    s.app_token = payload.get("app_token") or s.app_token
    s.table_points = payload.get("table_points") or s.table_points
    s.table_cases = payload.get("table_cases") or s.table_cases
    s.table_quotes = payload.get("table_quotes") or s.table_quotes
    s.table_structures = payload.get("table_structures") or s.table_structures
    if "default_table_id" in payload:
        s.default_table_id = payload.get("default_table_id")
    _save_state()
    return {"ok": True}


def get_feishu_settings_public() -> Dict[str, Any]:
    s = state.feishu_settings
    return {
        "app_token_set": bool(s.app_token),
        "tables": {
            "points": bool(s.table_points),
            "cases": bool(s.table_cases),
            "quotes": bool(s.table_quotes),
            "structures": bool(s.table_structures),
        }
    }


def set_universal_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    u = state.universal_settings
    if "endpoint" in payload:
        u.endpoint = payload.get("endpoint") or None
    if "token" in payload:
        u.token = payload.get("token") or None
    if "prefer_markdown" in payload:
        v = payload.get("prefer_markdown")
        u.prefer_markdown = bool(v) if not isinstance(v, bool) else v
    _save_state()
    return {"ok": True}


def get_universal_settings_public() -> Dict[str, Any]:
    u = state.universal_settings
    return {
        "endpoint_set": bool(u.endpoint),
        "token_set": bool(u.token),
        "prefer_markdown": u.prefer_markdown,
    }

