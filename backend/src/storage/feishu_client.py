"""
飞书多维表格客户端 - 异步版本支持高并发
"""
import time
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from src.config.settings import state

FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_RECORDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
FEISHU_LIST_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
FEISHU_TABLES_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
FEISHU_CREATE_TABLE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"

# 默认的表格字段配置
DEFAULT_FIELDS = {
    "观点库": [
        {"field_name": "原文", "field_type": "Text"},
        {"field_name": "观点", "field_type": "Text"},
        {"field_name": "标签", "field_type": "MultiSelect"},
        {"field_name": "来源", "field_type": "Text"},
        {"field_name": "来源URL", "field_type": "URL"},
        {"field_name": "创建时间", "field_type": "CreatedTime"},
    ],
    "案例库": [
        {"field_name": "原文", "field_type": "Text"},
        {"field_name": "案例", "field_type": "Text"},
        {"field_name": "标签", "field_type": "MultiSelect"},
        {"field_name": "来源", "field_type": "Text"},
        {"field_name": "来源URL", "field_type": "URL"},
        {"field_name": "创建时间", "field_type": "CreatedTime"},
    ],
    "金句库": [
        {"field_name": "原文", "field_type": "Text"},
        {"field_name": "金句", "field_type": "Text"},
        {"field_name": "适用场景", "field_type": "Text"},
        {"field_name": "标签", "field_type": "MultiSelect"},
        {"field_name": "来源", "field_type": "Text"},
        {"field_name": "来源URL", "field_type": "URL"},
        {"field_name": "创建时间", "field_type": "CreatedTime"},
    ],
    "结构库": [
        {"field_name": "标题", "field_type": "Text"},
        {"field_name": "结构", "field_type": "Text"},
        {"field_name": "标签", "field_type": "MultiSelect"},
        {"field_name": "创建时间", "field_type": "CreatedTime"},
    ],
}

FIELD_TYPE_MAP = {
    "Text": "1",
    "Number": "2",
    "SingleSelect": "3",
    "MultiSelect": "4",
    "DateTime": "5",
    "Checkbox": "7",
    "URL": "15",
    "CreatedTime": "1001",
}


def get_tenant_access_token_sync() -> Optional[str]:
    """同步版本 - 保留兼容"""
    s = state.feishu_settings
    if not s.app_id or not s.app_secret:
        return None
    now = int(time.time())
    if s.tenant_token and s.tenant_token_expire_ts and s.tenant_token_expire_ts - now > 60:
        return s.tenant_token
    payload = {"app_id": s.app_id, "app_secret": s.app_secret}
    try:
        import httpx
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


async def get_tenant_access_token_async() -> Optional[str]:
    """异步版本 - 支持高并发"""
    s = state.feishu_settings
    if not s.app_id or not s.app_secret:
        return None
    now = int(time.time())
    if s.tenant_token and s.tenant_token_expire_ts and s.tenant_token_expire_ts - now > 60:
        return s.tenant_token
    
    payload = {"app_id": s.app_id, "app_secret": s.app_secret}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10.0)) as session:
            async with session.post(FEISHU_TOKEN_URL, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
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
    """同步版本 - 保留兼容"""
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = get_tenant_access_token_sync()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_RECORDS_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    body = {"records": [{"fields": rec} for rec in records]}
    try:
        import httpx
        with httpx.Client(timeout=15.0) as c:
            r = c.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def create_records_async(table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """异步版本 - 支持高并发"""
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = await get_tenant_access_token_async()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_RECORDS_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    body = {"records": [{"fields": rec} for rec in records]}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15.0)) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_records(table_id: str, page_size: int = 100) -> Dict[str, Any]:
    """同步版本"""
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = get_tenant_access_token_sync()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_LIST_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": page_size}
    try:
        import httpx
        with httpx.Client(timeout=15.0) as c:
            r = c.get(url, params=params, headers=headers)
            r.raise_for_status()
            return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_records_async(table_id: str, page_size: int = 100) -> Dict[str, Any]:
    """异步版本"""
    s = state.feishu_settings
    if not s.app_token or not table_id:
        return {"success": False, "error": "missing_app_or_table"}
    token = await get_tenant_access_token_async()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_LIST_URL.format(app_token=s.app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": page_size}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15.0)) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                resp.raise_for_status()
                return {"success": True, "data": await resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_tables() -> Dict[str, Any]:
    """获取当前 Bitable 的所有表格（同步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    token = get_tenant_access_token_sync()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_TABLES_URL.format(app_token=s.app_token)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        import httpx
        with httpx.Client(timeout=15.0) as c:
            r = c.get(url, headers=headers)
            r.raise_for_status()
            return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_tables_async() -> Dict[str, Any]:
    """获取当前 Bitable 的所有表格（异步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    token = await get_tenant_access_token_async()
    if not token:
        return {"success": False, "error": "missing_token"}
    url = FEISHU_TABLES_URL.format(app_token=s.app_token)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15.0)) as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return {"success": True, "data": await resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_table(table_name: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """创建一个新表格并设置字段（同步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    token = get_tenant_access_token_sync()
    if not token:
        return {"success": False, "error": "missing_token"}
    
    url = FEISHU_CREATE_TABLE_URL.format(app_token=s.app_token)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 构建字段配置
    field_configs = []
    for f in fields:
        field_config = {"field_name": f["field_name"], "type": FIELD_TYPE_MAP.get(f["field_type"], "1")}
        if f["field_type"] == "MultiSelect":
            field_config["options"] = [{"name": "重要"}, {"name": "待处理"}, {"name": "已用"}]
        field_configs.append(field_config)
    
    body = {"table_name": table_name, "fields": field_configs}
    
    try:
        import httpx
        with httpx.Client(timeout=15.0) as c:
            r = c.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def create_table_async(table_name: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """创建一个新表格并设置字段（异步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    token = await get_tenant_access_token_async()
    if not token:
        return {"success": False, "error": "missing_token"}
    
    url = FEISHU_CREATE_TABLE_URL.format(app_token=s.app_token)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 构建字段配置
    field_configs = []
    for f in fields:
        field_config = {"field_name": f["field_name"], "type": FIELD_TYPE_MAP.get(f["field_type"], "1")}
        if f["field_type"] == "MultiSelect":
            field_config["options"] = [{"name": "重要"}, {"name": "待处理"}, {"name": "已用"}]
        field_configs.append(field_config)
    
    body = {"table_name": table_name, "fields": field_configs}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15.0)) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def init_default_tables() -> Dict[str, Any]:
    """初始化默认的 4 个表格（同步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    
    # 获取现有表格
    result = list_tables()
    if not result.get("success"):
        return result
    
    existing_tables = result.get("data", {}).get("data", {}).get("items", [])
    existing_names = {t.get("name", ""): t.get("table_id", "") for t in existing_tables}
    
    created = []
    for table_name, fields in DEFAULT_FIELDS.items():
        if table_name in existing_names:
            # 已存在，跳过
            continue
        
        result = create_table(table_name, fields)
        if result.get("success"):
            table_id = result.get("data", {}).get("data", {}).get("table_id", "")
            created.append({"name": table_name, "table_id": table_id})
            _save_table_id(table_name, table_id)
        else:
            return result
    
    return {"success": True, "created": created, "existing": existing_names}


async def init_default_tables_async() -> Dict[str, Any]:
    """初始化默认的 4 个表格（异步）"""
    s = state.feishu_settings
    if not s.app_token:
        return {"success": False, "error": "missing_app_token"}
    
    # 获取现有表格
    result = await list_tables_async()
    if not result.get("success"):
        return result
    
    existing_tables = result.get("data", {}).get("data", {}).get("items", [])
    existing_names = {t.get("name", ""): t.get("table_id", "") for t in existing_tables}
    
    created = []
    for table_name, fields in DEFAULT_FIELDS.items():
        if table_name in existing_names:
            continue
        
        result = await create_table_async(table_name, fields)
        if result.get("success"):
            table_id = result.get("data", {}).get("data", {}).get("table_id", "")
            created.append({"name": table_name, "table_id": table_id})
            _save_table_id(table_name, table_id)
        else:
            return result
    
    return {"success": True, "created": created, "existing": existing_names}


def _save_table_id(table_name: str, table_id: str):
    """保存 table_id 到配置"""
    s = state.feishu_settings
    if table_name == "观点库":
        s.table_points = table_id
    elif table_name == "案例库":
        s.table_cases = table_id
    elif table_name == "金句库":
        s.table_quotes = table_id
    elif table_name == "结构库":
        s.table_structures = table_id