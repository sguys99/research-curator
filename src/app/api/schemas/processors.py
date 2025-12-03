"""
Processors API 스키마

데이터 처리 관련 요청/응답 모델
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ====================================
# 요약 생성 (Summarization)
# ====================================
class SummarizeRequest(BaseModel):
    """요약 생성 요청"""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용")
    language: str = Field(default="ko", description="요약 언어 (ko: 한국어, en: 영어)")
    length: str = Field(default="medium", description="요약 길이 (short/medium/long)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Attention Is All You Need",
                    "content": "We propose a new simple network architecture...",
                    "language": "ko",
                    "length": "medium",
                },
            ],
        },
    }


class SummarizeResponse(BaseModel):
    """요약 생성 응답"""

    summary: str = Field(..., description="생성된 요약")
    language: str = Field(..., description="요약 언어")
    length: str = Field(..., description="요약 길이")


# ====================================
# 중요도 평가 (Evaluation)
# ====================================
class EvaluateRequest(BaseModel):
    """중요도 평가 요청"""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용")
    metadata: dict[str, Any] | None = Field(default=None, description="메타데이터 (인용수, 연도 등)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "GPT-4 Technical Report",
                    "content": "GPT-4 is a large multimodal model...",
                    "metadata": {"year": 2023, "citations": 5000},
                },
            ],
        },
    }


class EvaluateResponse(BaseModel):
    """중요도 평가 응답"""

    innovation_score: float = Field(..., description="혁신성 점수 (0.0-1.0)")
    relevance_score: float = Field(..., description="관련성 점수 (0.0-1.0)")
    impact_score: float = Field(..., description="영향력 점수 (0.0-1.0)")
    timeliness_score: float = Field(..., description="시의성 점수 (0.0-1.0)")
    final_score: float = Field(..., description="최종 중요도 점수 (0.0-1.0)")
    llm_score: float = Field(..., description="LLM 평가 점수")
    metadata_score: float = Field(..., description="메타데이터 평가 점수")
    reasoning: str | None = Field(default=None, description="평가 근거")


# ====================================
# 카테고리 분류 (Classification)
# ====================================
class ClassifyRequest(BaseModel):
    """카테고리 분류 요청"""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용")
    source_name: str = Field(default="", description="소스 이름 (예: arXiv)")
    url: str = Field(default="", description="원문 URL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Attention Is All You Need",
                    "content": "We propose the Transformer...",
                    "source_name": "arXiv",
                    "url": "https://arxiv.org/abs/1706.03762",
                },
            ],
        },
    }


class ClassifyResponse(BaseModel):
    """카테고리 분류 응답"""

    category: str = Field(..., description="카테고리 (paper/news/report/blog/other)")
    confidence: float = Field(..., description="신뢰도 (0.0-1.0)")
    keywords: list[str] = Field(..., description="키워드 리스트")
    research_field: str = Field(..., description="연구 분야")
    sub_fields: list[str] = Field(default_factory=list, description="세부 분야")
    reasoning: str | None = Field(default=None, description="분류 근거")


# ====================================
# 통합 처리 (Processing Pipeline)
# ====================================
class ProcessArticleRequest(BaseModel):
    """단일 아티클 처리 요청"""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용")
    url: str = Field(default="", description="원문 URL")
    source_name: str = Field(default="", description="소스 이름")
    source_type: str = Field(default="", description="소스 타입")
    metadata: dict[str, Any] | None = Field(default=None, description="메타데이터")
    summary_language: str = Field(default="ko", description="요약 언어")
    summary_length: str = Field(default="medium", description="요약 길이")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Attention Is All You Need",
                    "content": "We propose the Transformer...",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "source_name": "arXiv",
                    "metadata": {"year": 2017, "citations": 50000},
                    "summary_language": "ko",
                    "summary_length": "medium",
                },
            ],
        },
    }


class ProcessedArticleResponse(BaseModel):
    """처리된 아티클 응답"""

    # 원본 데이터
    title: str
    content: str
    url: str
    source_name: str
    source_type: str

    # 처리 결과
    summary: str
    importance_score: float
    category: str
    keywords: list[str]
    research_field: str
    embedding: list[float]

    # 상세 평가
    innovation_score: float
    relevance_score: float
    impact_score: float
    timeliness_score: float

    # 메타데이터
    metadata: dict[str, Any]
    processed_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Attention Is All You Need",
                    "content": "We propose the Transformer...",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "source_name": "arXiv",
                    "source_type": "paper",
                    "summary": "트랜스포머 아키텍처를 제안하는 논문...",
                    "importance_score": 0.94,
                    "category": "paper",
                    "keywords": ["Transformer", "Attention"],
                    "research_field": "Machine Learning",
                    "embedding": [0.1, 0.2],  # 실제로는 1536 dims
                    "innovation_score": 1.0,
                    "relevance_score": 1.0,
                    "impact_score": 1.0,
                    "timeliness_score": 0.8,
                    "metadata": {"year": 2017, "citations": 50000},
                    "processed_at": "2025-12-03T10:00:00",
                },
            ],
        },
    }


class BatchProcessRequest(BaseModel):
    """배치 처리 요청"""

    articles: list[ProcessArticleRequest] = Field(..., description="처리할 아티클 리스트")
    max_concurrent: int = Field(default=5, description="최대 동시 처리 개수", ge=1, le=10)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "articles": [
                        {
                            "title": "Paper 1",
                            "content": "Content 1...",
                            "url": "https://...",
                        },
                        {
                            "title": "Paper 2",
                            "content": "Content 2...",
                            "url": "https://...",
                        },
                    ],
                    "max_concurrent": 5,
                },
            ],
        },
    }


class BatchProcessResponse(BaseModel):
    """배치 처리 응답"""

    total: int = Field(..., description="총 아티클 수")
    success: int = Field(..., description="성공한 아티클 수")
    failed: int = Field(..., description="실패한 아티클 수")
    results: list[ProcessedArticleResponse] = Field(..., description="처리 결과 리스트")
    processing_time: float = Field(..., description="처리 시간 (초)")


# ====================================
# 통계 및 필터링
# ====================================
class StatisticsResponse(BaseModel):
    """통계 응답"""

    total: int
    category_distribution: dict[str, int]
    average_score: float
    max_score: float
    min_score: float
    high_quality_count: int
