"""Pydantic schemas for LLM API endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""

    role: Literal["system", "user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ChatCompletionRequest(BaseModel):
    """Request schema for chat completion endpoint."""

    messages: list[ChatMessage] = Field(..., description="List of chat messages")
    provider: Literal["openai", "claude"] = Field(default="openai", description="LLM provider to use")
    model: str | None = Field(default=None, description="Model name (optional)")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)",
    )
    max_tokens: int = Field(default=2000, ge=1, le=4096, description="Maximum tokens in response")
    response_format: Literal["text", "json"] = Field(default="text", description="Response format")

    class Config:
        json_schema_extra = {
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
        }


class ChatCompletionResponse(BaseModel):
    """Response schema for chat completion endpoint."""

    content: str = Field(..., description="Generated response content")
    provider: str = Field(..., description="Provider used for generation")
    model: str = Field(..., description="Model used for generation")
    finish_reason: str = Field(default="stop", description="Reason for completion")


class EmbeddingRequest(BaseModel):
    """Request schema for embedding generation endpoint."""

    text: str = Field(..., description="Text to embed")
    model: str | None = Field(default=None, description="Embedding model name (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "AI research trends in 2024",
                "model": "text-embedding-3-small",
            },
        }


class EmbeddingResponse(BaseModel):
    """Response schema for embedding generation endpoint."""

    embedding: list[float] = Field(..., description="Embedding vector")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used for embedding")


class ArticleSummaryRequest(BaseModel):
    """Request schema for article summarization."""

    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    language: Literal["ko", "en"] = Field(default="ko", description="Summary language")
    max_sentences: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of sentences in summary",
    )
    provider: Literal["openai", "claude"] = Field(default="openai", description="LLM provider to use")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "GPT-5 Achieves Human-Level Performance",
                "content": "Researchers have developed...",
                "language": "ko",
                "max_sentences": 4,
                "provider": "openai",
            },
        }


class ArticleSummaryResponse(BaseModel):
    """Response schema for article summarization."""

    summary: str = Field(..., description="Generated summary")
    original_length: int = Field(..., description="Original content length in chars")
    summary_length: int = Field(..., description="Summary length in chars")


class ArticleAnalysisRequest(BaseModel):
    """Request schema for article analysis."""

    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content or abstract")
    provider: Literal["openai", "claude"] = Field(default="openai", description="LLM provider to use")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Attention Is All You Need",
                "content": "The dominant sequence transduction models...",
                "provider": "openai",
            },
        }


class ArticleAnalysisResponse(BaseModel):
    """Response schema for article analysis."""

    category: Literal["paper", "news", "report"] = Field(..., description="Article category")
    importance_score: float = Field(..., ge=0.0, le=1.0, description="Importance score (0.0 to 1.0)")
    keywords: list[str] = Field(..., description="Extracted keywords")
    field: str = Field(..., description="Research field")
    summary_korean: str = Field(..., description="Korean summary")
