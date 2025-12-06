"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field  # 메타 데이터 검증규칙을 정의할 떄 사용
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # pydantic v2에서 제공하는 설정 딕셔너리, extra="ignore"는 정의되지 않은 필드는 무시하겠다는 의미
    # 설정 정보 자체를 담는 것이 아니라 설정을 어떻게 로드하고 처리할지에 대한 메타설정을 담은 딕셔너리
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "Research Curator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production"] = "development"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/research_curator",
    )

    # Vector Database (Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "research_articles"
    QDRANT_VECTOR_SIZE: int = 1536  # OpenAI embedding size

    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "claude"] = "openai"

    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = Field(default="")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # Search APIs
    SERPER_API_KEY: str = Field(default="")
    BRAVE_API_KEY: str = Field(default="")

    # Email (SMTP)
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = 587
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="")
    SMTP_FROM_NAME: str = Field(default="Research Curator")

    # Authentication
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    # Scheduler
    COLLECT_SCHEDULE_HOUR: int = 1  # 01:00
    COLLECT_SCHEDULE_MINUTE: int = 0
    SEND_EMAIL_SCHEDULE_HOUR: int = 8  # 08:00
    SEND_EMAIL_SCHEDULE_MINUTE: int = 0

    # Data Collection
    DEFAULT_ARTICLES_PER_DAY: int = 5
    MAX_ARTICLES_PER_SOURCE: int = 10

    # CORS(Cross-Origin Resource Sharing), 보안 정책으로 두 도메인의 요청만 받기위해 설정
    # 3000은 리엑트, 뷰에서 사용하는포트, 8501은 streamlit에서 사용하는 포트
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"

    @property  # origin 문자열을 리스트로 변환
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def database_url_str(self) -> str:
        """Get database URL as string."""
        return str(self.DATABASE_URL)


# lru_cache: 함수가 호출되면 결과를 캐시에 저장
# 같은 인자로 다시 호출되면 캐시된 결과를 즉시 반환(함수실행 안함)
@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
# 전역 인스턴스, 이렇게 미리 생성해두면 import로 바로 사용 가능
# from app.core.config import settings
# pring(settings.APP_NAME) # "Research Curator"
settings = get_settings()
