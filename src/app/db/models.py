"""SQLAlchemy 데이터베이스 모델(ORM 모델 정의)."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid_extensions import uuid7


def utcnow() -> datetime:
    """타임존을 포함한 현재 UTC 시간을 반환한다."""
    return datetime.now(UTC)


# SQLAlchemy ORM 모델의 공통 베이스 클래스
class Base(DeclarativeBase):
    """모든 DB 모델의 베이스 클래스."""

    pass


class User(Base):
    """사용자 계정 모델."""

    __tablename__ = "users"  # Base를 상속받은 모델은 자동 등록됨

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    # 관계
    # 1:1 관계
    preference: Mapped["UserPreference"] = relationship(
        "UserPreference",
        back_populates="user",  # 양방향 관계 설정, UserPreference의 user 속성과 연결
        uselist=False,
        cascade="all, delete-orphan",  # User 삭제 시 관련 데이터 자동 삭제(다른 테이블)
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
    """사용자 선호도 및 설정."""

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 연구 관심사: 논문/뉴스 수집 시 아래 키워드로 필터링
    research_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)

    # 소스 설정: 사용자마다 다른 소스에서 데이터를 수집하도록 함
    # 저장 예시
    #     preference.sources = {
    #     "arxiv": {"enabled": True, "categories": ["cs.AI", "cs.CL"]},
    #     "google_scholar": {"enabled": True, "max_results": 10},
    #     "techcrunch": {"enabled": False},
    #     "github": {"enabled": True, "topics": ["machine-learning", "nlp"]}
    #      }
    sources: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # 콘텐츠 선호도(비율)
    info_types: Mapped[dict[str, int]] = mapped_column(
        JSON,
        default={"paper": 40, "news": 40, "report": 20},
    )

    # 이메일 설정: 발송 시간, 일일 아티클 수 제한, 이메일 활성화
    email_time: Mapped[str] = mapped_column(String(5), default="08:00")  # 시:분 형식(예: 08:00)
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    # 관계
    # 양방향 접근 예시
    # 예: UserPreference → User
    # preference.user.email  # "user@example.com"
    # 예: User → UserPreference
    # user.preference.research_fields  # ["NLP", "CV"]
    user: Mapped["User"] = relationship("User", back_populates="preference")

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id})>"


# 수집된 논문/뉴스/리포트를 저장하는 핵심 테이블
class CollectedArticle(Base):
    """수집된 연구 아티클, 뉴스, 리포트."""

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
    )  # paper, news, report 값만 허용
    # LLM이 분류한 카테고리 예시: "NLP", "Computer Vision", "Reinforcement Learning"
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=True, index=True)  # 0.0~1.0

    # 아티클 메타데이터(저자, 발행일, 인용 수 등)
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

    # 벡터 DB 참조 ID: Qdrant ID
    vector_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)

    # 아티클 수집 시간
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    # 원본 발행 시간: 예) 논문 발표일
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # 관계
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

# # 3. 임베딩 생성 및 벡터 DB 저장
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
# 누구에게, 언제, 어떤 아티클을 보냈는지, 이메일을 열었는지 기록
class SentDigest(Base):
    """이메일 다이제스트 발송 기록."""

    __tablename__ = "sent_digests"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(  # 수신자 ID
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 다이제스트에 포함된 아티클 목록: ID를 JSON 배열로 저장
    article_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

    # 이메일 추적
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    email_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # 관계: 발송 대상 사용자 테이블과 연결
    user: Mapped["User"] = relationship("User", back_populates="digests")

    def __repr__(self) -> str:
        return f"<SentDigest(id={self.id}, user_id={self.user_id}, sent_at={self.sent_at})>"


class Feedback(Base):
    """아티클에 대한 사용자 피드백."""

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
        ),  # 아티클이 삭제되면 관련 피드백도 삭제됨
        nullable=False,
        index=True,
    )

    # 평점(1-5), 별점 없이 코멘트만 남길 수도 있음
    rating: Mapped[int] = mapped_column(Integer, nullable=True)

    # 선택적 코멘트, 코멘트 없이 별점만 남길 수도 있음
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # 관계
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")  # 피드백 작성자
    article: Mapped["CollectedArticle"] = relationship(
        "CollectedArticle",
        back_populates="feedbacks",
    )  # 피드백 대상 아티클

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, user_id={self.user_id}, rating={self.rating})>"
