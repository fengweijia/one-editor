from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class IngestUrlRequest(BaseModel):
    url: str

class IngestTextRequest(BaseModel):
    text: str
    meta: Optional[Dict[str, Any]] = None

class AnalyzeRequest(BaseModel):
    text: str
    meta: Dict[str, Any]
    platform: str

class StoreIndexRequest(BaseModel):
    analysis: Dict[str, Any]
    meta: Dict[str, Any]

class SearchRequest(BaseModel):
    q: str
    tags: Optional[List[str]] = None
    type: Optional[str] = None
    semantic: Optional[bool] = False
    filters: Optional[Dict[str, Any]] = None

class AggregateRequest(BaseModel):
    topic: str
    filters: Optional[Dict[str, Any]] = None
