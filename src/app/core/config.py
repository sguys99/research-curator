"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "Research Curator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production"] = "development"

    # Database
    DATABASE_URL: PostgresDsn = Field(
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
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

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

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def database_url_str(self) -> str:
        """Get database URL as string."""
        return str(self.DATABASE_URL)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
