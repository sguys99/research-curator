"""애플리케이션 설정."""

import warnings
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator  # 메타 데이터 검증 규칙 정의에 사용
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경 변수로부터 로드되는 애플리케이션 설정."""

    # pydantic v2 설정 딕셔너리: extra="ignore"는 정의되지 않은 필드를 무시
    # 설정 값을 담는 것이 아니라, 로드/처리 방식에 대한 메타설정
    # Settings 인스턴스화 시 .env를 읽어 각 변수에 저장됨(예: OPENAI_API_KEY)
    # 값 조회 우선순위:
    # 1) 환경변수 (실제 OS 환경변수)
    # 2) .env 파일 (model_config에서 지정)
    # 3) 기본값 (Field의 default)
    # 아래 설정이 없으면 .env를 읽지 못하고 default=""를 사용한다.
    # 아래 설정이 있으면 .env의 실제 키 값이 자동 로드된다.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 애플리케이션
    APP_NAME: str = "Research Curator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production"] = "development"

    # 데이터베이스
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/research_curator",
    )

    # 벡터 DB(Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "research_articles"
    QDRANT_VECTOR_SIZE: int = 1536  # OpenAI 임베딩 크기

    # LLM 설정
    LLM_PROVIDER: Literal["openai", "claude"] = "openai"

    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = Field(default="")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # 검색 API
    SERPER_API_KEY: str = Field(default="")
    BRAVE_API_KEY: str = Field(default="")

    # 이메일(SMTP)
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = 587
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="")
    SMTP_FROM_NAME: str = Field(default="Research Curator")

    # 인증
    JWT_SECRET_KEY: str | None = Field(default=None)
    JWT_ALGORITHM: str = "HS256"
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    # 스케줄러
    COLLECT_SCHEDULE_HOUR: int = 1  # 01:00
    COLLECT_SCHEDULE_MINUTE: int = 0
    SEND_EMAIL_SCHEDULE_HOUR: int = 8  # 08:00
    SEND_EMAIL_SCHEDULE_MINUTE: int = 0

    # 데이터 수집
    DEFAULT_ARTICLES_PER_DAY: int = 5
    MAX_ARTICLES_PER_SOURCE: int = 10

    # CORS(교차 출처 리소스 공유): 보안 정책상 허용 도메인만 요청 허용
    # 3000은 React/Vue, 8501은 Streamlit에서 사용하는 포트
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"

    @property  # origin 문자열을 리스트로 변환
    def cors_origins_list(self) -> list[str]:
        """CORS origin 문자열을 리스트로 변환한다."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def database_url_str(self) -> str:
        """DB URL을 문자열로 반환한다."""
        return str(self.DATABASE_URL)

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        """환경에 맞는 JWT 시크릿 설정을 보장한다."""
        if self.JWT_SECRET_KEY:
            return self

        if self.ENVIRONMENT == "production":
            raise ValueError("JWT_SECRET_KEY must be set in production.")

        warnings.warn(
            "JWT_SECRET_KEY is not set; using an insecure development default.",
            RuntimeWarning,
            stacklevel=2,
        )
        self.JWT_SECRET_KEY = "dev-insecure-secret"
        return self

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """제공자/환경에 따라 필요한 API 키를 검증한다."""
        if self.LLM_PROVIDER == "openai":
            if not self.OPENAI_API_KEY:
                if self.ENVIRONMENT == "production":
                    raise ValueError("OPENAI_API_KEY must be set in production.")
                warnings.warn(
                    "OPENAI_API_KEY is not set; OpenAI calls will fail in development.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        elif self.LLM_PROVIDER == "claude":
            if not self.ANTHROPIC_API_KEY:
                if self.ENVIRONMENT == "production":
                    raise ValueError("ANTHROPIC_API_KEY must be set in production.")
                warnings.warn(
                    "ANTHROPIC_API_KEY is not set; Claude calls will fail in development.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        return self


# lru_cache: 함수 호출 결과를 캐시에 저장
# 같은 인자로 다시 호출되면 캐시된 결과를 즉시 반환(함수 실행 안 함)
@lru_cache
def get_settings() -> Settings:
    """캐시된 Settings 인스턴스를 반환한다."""
    return Settings()


# 전역 설정 인스턴스
# 전역 인스턴스는 미리 생성해두면 import로 바로 사용 가능
# from app.core.config import settings
# print(settings.APP_NAME)  # "Research Curator"
settings = get_settings()
