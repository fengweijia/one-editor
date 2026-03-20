from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- Request Schemas ---

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

# --- Output Schemas for LLM Extraction (Strict JSON) ---

class QualityRating(BaseModel):
    score: int = Field(..., description="评分，1-10分")
    summary: str = Field(..., description="原文质量总结，是否论证扎实、案例丰富")
    concerns: List[str] = Field(..., description="指出的原文论证薄弱或逻辑不通之处")

class CoreArgument(BaseModel):
    point: str = Field(..., description="核心论点")
    evidence: str = Field(..., description="支撑该论点的论据")
    writing_technique: str = Field(..., description="该论点使用的写作手法")

class StructuredAnalysis(BaseModel):
    tags: List[str] = Field(..., description="文章的分类标签，如 #认知 #方法论")
    core_arguments: List[CoreArgument] = Field(..., description="提炼出的3-5个核心观点")
    writing_directions: List[str] = Field(..., description="基于此文章可以延展的写作方向")

class GoldenSentence(BaseModel):
    text: str = Field(..., description="金句原文，绝对不能改写")
    position: str = Field(..., description="该金句在文章中的大概位置")
    context_before: str = Field(..., description="金句前面的上下文")
    context_after: str = Field(..., description="金句后面的上下文")

class CaseStudy(BaseModel):
    summary: str = Field(..., description="案例的一句话总结")
    key_details: str = Field(..., description="案例的关键细节（人物/数据/转折点）")
    usable_angle: str = Field(..., description="该案例可被借用的角度")

class RawEssence(BaseModel):
    golden_sentences: List[GoldenSentence] = Field(..., description="提取出的金句列表")
    cases: List[CaseStudy] = Field(..., description="提取出的案例列表")

class LLMExtractionResult(BaseModel):
    quality_rating: QualityRating = Field(..., description="原文质量评级")
    structured_analysis: StructuredAnalysis = Field(..., description="结构化分析数据")
    raw_essence: RawEssence = Field(..., description="原始精华摘录")
