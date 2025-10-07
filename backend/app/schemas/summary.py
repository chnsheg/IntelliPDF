"""
Summary and keywords extraction schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    """文档摘要请求"""
    max_length: Optional[int] = Field(
        default=500,
        description="摘要最大长度",
        ge=100,
        le=2000
    )
    language: Optional[str] = Field(
        default="zh",
        description="摘要语言"
    )


class SummaryResponse(BaseModel):
    """文档摘要响应"""
    summary: str = Field(description="生成的摘要")
    word_count: int = Field(description="摘要字数")
    processing_time: float = Field(description="处理时间（秒）")


class KeywordsRequest(BaseModel):
    """关键词提取请求"""
    max_keywords: Optional[int] = Field(
        default=10,
        description="最大关键词数量",
        ge=3,
        le=50
    )
    language: Optional[str] = Field(
        default="zh",
        description="语言"
    )


class KeywordsResponse(BaseModel):
    """关键词提取响应"""
    keywords: List[str] = Field(description="提取的关键词列表")
    scores: Optional[List[float]] = Field(
        default=None,
        description="关键词重要性分数"
    )
    processing_time: float = Field(description="处理时间（秒）")
