import time
from typing import Dict, Any, List, Optional
import httpx
from src.config.settings import state

FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_RECORDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
FEISHU_LIST_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

def get_tenant_access_token() -> Optional[str]:
    s = state.feishu_settings
    if not s.app_id or not s.app_secret:
        return None
    now = int(time.time())
    if s.tenant_token and s.tenant_token_expire_ts and s.tenant_token_expire_ts - now > 60:
        return s.tenant_token
    payload = {"app_id": s.app_id, "app_secret": s.app_secret}
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.post(FEISHU_TOKEN_URL, json=payload)
            r.raise_for_status()
            data = r.json()
            token = data.get("tenant_access_token")
            expire = data.get("expire", 3600)
            if token:
                s.tenant_token = token
                s.tenant_token_expire_ts = now + int(expire)
                return token
    except Exception:
        return None
    return None

def create_records(table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = get_tenant_access_token()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_RECORDS_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    body = {"records": [{"fields": rec} for rec in records]}
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_records(table_id: str, page_size: int = 100) -> Dict[str, Any]:
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = get_tenant_access_token()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_LIST_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": page_size}
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(url, params=params, headers=headers)
            r.raise_for_status()
            return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}
