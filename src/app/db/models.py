"""SQLAlchemy database models.(ORM 데이터베이스 모델을 정의)"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid_extensions import uuid7


def utcnow() -> datetime:
    """Get current UTC time with timezone."""
    return datetime.now(UTC)


# SQLAlchemy ORM 데이터베이스 모델의 공통 부모 클래스
class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class User(Base):
    """User account model."""

    __tablename__ = "users"  # Base를 상속 받은 모델은 자동 등록됨

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    # Relationships
    # 1:1 관계
    preference: Mapped["UserPreference"] = relationship(
        "UserPreference",
        back_populates="user",  # 양방향 관계 설정, UserPreference의 user 속성과 연결
        uselist=False,
        cascade="all, delete-orphan",  # User 삭제시 관련 데이터 자동삭제(다른 테이블)
    )
    # 1:N 관계
    digests: Mapped[list["SentDigest"]] = relationship(
        "SentDigest",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # 1:N 관계
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    #

    def __repr__(self) -> str:  # 디버깅용 문자열 표현
        return f"<User(id={self.id}, email={self.email})>"


class UserPreference(Base):
    """User preferences and settings."""

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Research interests: 논문/ 뉴스 수집 시 아래 키워드로 필터링
    research_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Source configuration(소스 설정), 사용자마다 다른 소스에서 데이터를 수집하도록 함
    # 저장 예시
    #     preference.sources = {
    #     "arxiv": {"enabled": True, "categories": ["cs.AI", "cs.CL"]},
    #     "google_scholar": {"enabled": True, "max_results": 10},
    #     "techcrunch": {"enabled": False},
    #     "github": {"enabled": True, "topics": ["machine-learning", "nlp"]}
    #      }
    sources: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Content preferences(컨텐츠 선호도, 비율)
    info_types: Mapped[dict[str, int]] = mapped_column(
        JSON,
        default={"paper": 40, "news": 40, "report": 20},
    )

    # Email settings: 발송시간, 일일아티클수 제한, 이메일 활성화
    email_time: Mapped[str] = mapped_column(String(5), default="08:00")  # HH:MM format
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    # Relationships
    # 양방향 접근이 가능(아래 예시)
    # UserPreference → User
    # preference.user.email  # "user@example.com"
    # # User → UserPreference
    # user.preference.research_fields  # ["NLP", "CV"]
    user: Mapped["User"] = relationship("User", back_populates="preference")

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id})>"


# 수집된 논문, 뉴스, 리포트를 저장하는 핵심 테이블
class CollectedArticle(Base):
    """Collected research articles, news, and reports."""

    __tablename__ = "collected_articles"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # 길이 제한 없음
    summary: Mapped[str] = mapped_column(Text, nullable=True)  # LLM이 생성한 요약
    source_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
    )  # 같은 아티클 중복 방지
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # paper, news, report 세종류 값만 가능
    # LLM이 분류한 카테고리: 예) "NLP", "Computer Vision", "Reinforcement Learning"
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=True, index=True)  # 0.0~1.0

    # Article metadata (authors, publish_date, citations, etc.)
    # 추가 정보를 유연하게 저장. 아래 예시
    # article.article_metadata = {
    #     "authors": ["Vaswani", "Shazeer", "Parmar"],
    #     "publish_date": "2017-06-12",
    #     "citations": 50000,
    #     "arxiv_id": "1706.03762",
    #     "conference": "NeurIPS 2017",
    #     "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
    # }

    # # 뉴스의 경우
    # article.article_metadata = {
    #     "author": "John Doe",
    #     "media_outlet": "TechCrunch",
    #     "tags": ["AI", "Startup", "Funding"]
    # }
    article_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Vector DB reference: Qdrant 참조 ID
    vector_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)

    # 아티클 수집 시간
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    # 원본 발행 시간: 예) 논문 발표일
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    feedbacks: Mapped[list["Feedback"]] = relationship(  # 사용자 피드백
        "Feedback",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CollectedArticle(id={self.id}, title={self.title[:50]})>"


# CollectedArticle을 포함한 전체 사용 예시
# # 1. 논문 수집
# article = CollectedArticle(
#     title="Attention Is All You Need",
#     content="Abstract: The dominant sequence...",
#     source_url="https://arxiv.org/abs/1706.03762",
#     source_type="paper",
#     article_metadata={
#         "authors": ["Vaswani", "Shazeer"],
#         "arxiv_id": "1706.03762",
#         "citations": 50000
#     },
#     published_at=datetime(2017, 6, 12, tzinfo=UTC)
# )
# db.add(article)
# db.commit()

# # 2. LLM으로 요약 및 평가
# article.summary = llm.summarize(article.content)
# article.importance_score = llm.evaluate_importance(article.content)
# article.category = llm.classify_category(article.content)
# db.commit()

# # 3. 임베딩 생성 및 Vector DB 저장
# embedding = openai.embeddings.create(input=article.content)
# qdrant_client.upsert(
#     collection_name="research_articles",
#     points=[{"id": str(article.id), "vector": embedding}]
# )
# article.vector_id = str(article.id)
# db.commit()

# # 4. 상위 아티클 선택하여 이메일 발송
# top_articles = db.query(CollectedArticle)\
#     .filter(CollectedArticle.importance_score >= 0.7)\
#     .order_by(CollectedArticle.importance_score.desc())\
#     .limit(5)\
#     .all()

# for article in top_articles:
#     send_email(
#         subject=article.title,
#         body=article.summary,
#         url=article.source_url
#     )


# 이메일 발송 기록(히스토리)을 추적하는 테이블
# 누구에게, 언제, 어떤 아티클들을 보냈는지, 이메일을 열어봤는지
class SentDigest(Base):
    """Email digest sending history."""

    __tablename__ = "sent_digests"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(  # 수신자 아이디
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Articles included in this digest: 이메일에 포함된 아티클 목록, ID, JSON 배열로 저장됨
    article_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Email tracking
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    email_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships, 발송 대상 사용자 테이블과 연결
    user: Mapped["User"] = relationship("User", back_populates="digests")

    def __repr__(self) -> str:
        return f"<SentDigest(id={self.id}, user_id={self.user_id}, sent_at={self.sent_at})>"


class Feedback(Base):
    """User feedback on articles."""

    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 피드백 대상 아티클
    article_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "collected_articles.id",
            ondelete="CASCADE",
        ),  # 아티클이 삭제되면, 관련 피드백도 삭제됨
        nullable=False,
        index=True,
    )

    # Rating (1-5 stars), 별점 없이 코멘트만 잠길수도 있음
    rating: Mapped[int] = mapped_column(Integer, nullable=True)

    # Optional comment, 코멘트 없이 별점만 남길수도 있음
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")  # 피드백 작성자
    article: Mapped["CollectedArticle"] = relationship(
        "CollectedArticle",
        back_populates="feedbacks",
    )  # 피드백 대상 아티클

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, user_id={self.user_id}, rating={self.rating})>"
