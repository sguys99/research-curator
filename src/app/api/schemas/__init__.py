"""API 스키마 패키지."""

from app.api.schemas.articles import (
    ArticleBase,
    ArticleCreate,
    ArticleListRequest,
    ArticleListResponse,
    ArticleResponse,
    ArticleSearchRequest,
    ArticleSearchResponse,
    ArticleSearchResult,
    ArticleUpdate,
    SimilarArticlesRequest,
    SimilarArticlesResponse,
)
from app.api.schemas.auth import (
    MagicLinkRequest,
    MagicLinkResponse,
    TokenPayload,
    TokenResponse,
)
from app.api.schemas.common import (
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
)
from app.api.schemas.feedback import (
    FeedbackBase,
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackUpdate,
)
from app.api.schemas.llm import (
    ArticleAnalysisRequest,
    ArticleAnalysisResponse,
    ArticleSummaryRequest,
    ArticleSummaryResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.api.schemas.scheduler import (
    JobInfo,
    JobListResponse,
    SchedulerControlRequest,
    SchedulerControlResponse,
    SchedulerStatusResponse,
    TriggerJobRequest,
    TriggerJobResponse,
)
from app.api.schemas.users import (
    DigestListResponse,
    DigestResponse,
    UserBase,
    UserCreate,
    UserPreferenceBase,
    UserPreferenceCreate,
    UserPreferenceResponse,
    UserPreferenceUpdate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # 공통
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationParams",
    # 인증
    "MagicLinkRequest",
    "MagicLinkResponse",
    "TokenPayload",
    "TokenResponse",
    # 사용자
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPreferenceBase",
    "UserPreferenceCreate",
    "UserPreferenceUpdate",
    "UserPreferenceResponse",
    "DigestResponse",
    "DigestListResponse",
    # 아티클
    "ArticleBase",
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleResponse",
    "ArticleSearchRequest",
    "ArticleSearchResponse",
    "ArticleSearchResult",
    "SimilarArticlesRequest",
    "SimilarArticlesResponse",
    "ArticleListRequest",
    "ArticleListResponse",
    # 피드백
    "FeedbackBase",
    "FeedbackCreate",
    "FeedbackUpdate",
    "FeedbackResponse",
    "FeedbackListResponse",
    # LLM
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "ArticleSummaryRequest",
    "ArticleSummaryResponse",
    "ArticleAnalysisRequest",
    "ArticleAnalysisResponse",
    # 스케줄러
    "JobInfo",
    "JobListResponse",
    "SchedulerControlRequest",
    "SchedulerControlResponse",
    "SchedulerStatusResponse",
    "TriggerJobRequest",
    "TriggerJobResponse",
]
