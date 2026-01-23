"""LLM API 엔드포인트용 Pydantic 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """단일 채팅 메시지."""

    role: Literal["system", "user", "assistant"] = Field(..., description="메시지 발신자 역할")
    content: str = Field(..., description="메시지 내용")


class ChatCompletionRequest(BaseModel):
    """채팅 완료 요청 스키마."""

    messages: list[ChatMessage] = Field(..., description="채팅 메시지 목록")
    provider: Literal["openai", "claude"] = Field(default="openai", description="사용할 LLM 제공자")
    model: str | None = Field(default=None, description="모델 이름(선택)")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="샘플링 온도(0.0~2.0)",
    )
    max_tokens: int = Field(default=2000, ge=1, le=4096, description="응답 최대 토큰 수")
    response_format: Literal["text", "json"] = Field(default="text", description="응답 형식")
    stream: bool = Field(default=False, description="스트리밍 모드 사용")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is machine learning?"},
                ],
                "provider": "openai",
                "temperature": 0.7,
                "max_tokens": 500,
                "response_format": "text",
            },
        },
    )


class ChatCompletionResponse(BaseModel):
    """채팅 완료 응답 스키마."""

    content: str = Field(..., description="생성된 응답 내용")
    provider: str = Field(..., description="사용한 제공자")
    model: str = Field(..., description="사용한 모델")
    finish_reason: str = Field(default="stop", description="완료 이유")


class EmbeddingRequest(BaseModel):
    """임베딩 생성 요청 스키마."""

    text: str = Field(..., description="임베딩할 텍스트")
    model: str | None = Field(default=None, description="임베딩 모델 이름(선택)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "AI research trends in 2024",
                "model": "text-embedding-3-small",
            },
        },
    )


class EmbeddingResponse(BaseModel):
    """임베딩 생성 응답 스키마."""

    embedding: list[float] = Field(..., description="임베딩 벡터")
    dimension: int = Field(..., description="임베딩 차원")
    model: str = Field(..., description="사용한 모델")


class ArticleSummaryRequest(BaseModel):
    """아티클 요약 요청 스키마."""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용")
    language: Literal["ko", "en"] = Field(default="ko", description="요약 언어")
    max_sentences: int = Field(
        default=4,
        ge=1,
        le=10,
        description="요약 최대 문장 수",
    )
    provider: Literal["openai", "claude"] = Field(default="openai", description="사용할 LLM 제공자")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "GPT-5 Achieves Human-Level Performance",
                "content": "Researchers have developed...",
                "language": "ko",
                "max_sentences": 4,
                "provider": "openai",
            },
        },
    )


class ArticleSummaryResponse(BaseModel):
    """아티클 요약 응답 스키마."""

    summary: str = Field(..., description="생성된 요약")
    original_length: int = Field(..., description="원문 길이(문자 수)")
    summary_length: int = Field(..., description="요약 길이(문자 수)")


class ArticleAnalysisRequest(BaseModel):
    """아티클 분석 요청 스키마."""

    title: str = Field(..., description="아티클 제목")
    content: str = Field(..., description="아티클 내용 또는 초록")
    provider: Literal["openai", "claude"] = Field(default="openai", description="사용할 LLM 제공자")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Attention Is All You Need",
                "content": "The dominant sequence transduction models...",
                "provider": "openai",
            },
        },
    )


class ArticleAnalysisResponse(BaseModel):
    """아티클 분석 응답 스키마."""

    category: Literal["paper", "news", "report"] = Field(..., description="아티클 카테고리")
    importance_score: float = Field(..., ge=0.0, le=1.0, description="중요도 점수(0.0~1.0)")
    keywords: list[str] = Field(..., description="추출된 키워드")
    field: str = Field(..., description="연구 분야")
    summary_korean: str = Field(..., description="한국어 요약")
