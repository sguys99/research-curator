"""아티클 CRUD 작업."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import CollectedArticle


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source_type: list[str] | None = None,
    category: list[str] | None = None,
    min_importance_score: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    order_by: str = "collected_at",
    order_desc: bool = True,
) -> tuple[list[CollectedArticle], int]:
    """
    필터/정렬/페이지네이션을 적용해 아티클 목록을 조회한다.

    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        source_type: 소스 유형 필터(paper/news/report)
        category: 카테고리 필터
        min_importance_score: 최소 중요도 점수
        date_from: 시작 날짜 필터
        date_to: 종료 날짜 필터
        order_by: 정렬 필드(collected_at, importance_score)
        order_desc: True면 내림차순 정렬

    Returns:
        (아티클 목록, 총 개수)
    """
    # 필터 적용
    filters = []
    if source_type:
        filters.append(CollectedArticle.source_type.in_(source_type))
    if category:
        filters.append(CollectedArticle.category.in_(category))
    if min_importance_score is not None:
        filters.append(CollectedArticle.importance_score >= min_importance_score)
    if date_from:
        filters.append(CollectedArticle.collected_at >= date_from)
    if date_to:
        filters.append(CollectedArticle.collected_at <= date_to)

    count_stmt = select(func.count()).select_from(CollectedArticle)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = db.scalar(count_stmt) or 0

    stmt = select(CollectedArticle)
    if filters:
        stmt = stmt.where(and_(*filters))

    # 정렬 적용
    if order_by == "importance_score":
        order_field = CollectedArticle.importance_score
    else:
        order_field = CollectedArticle.collected_at

    if order_desc:
        stmt = stmt.order_by(desc(order_field))
    else:
        stmt = stmt.order_by(order_field)

    # 페이지네이션 적용
    stmt = stmt.offset(skip).limit(limit)
    articles = list(db.scalars(stmt).all())

    return articles, total


def get_article_by_id(db: Session, article_id: UUID) -> CollectedArticle | None:
    """
    ID로 아티클을 조회한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID

    Returns:
        CollectedArticle 객체 또는 None
    """
    stmt = select(CollectedArticle).where(CollectedArticle.id == article_id)
    return db.scalar(stmt)


def get_article_by_url(db: Session, source_url: str) -> CollectedArticle | None:
    """
    소스 URL로 아티클을 조회한다(중복 감지).

    Args:
        db: 데이터베이스 세션
        source_url: 소스 URL

    Returns:
        CollectedArticle 객체 또는 None
    """
    stmt = select(CollectedArticle).where(CollectedArticle.source_url == source_url)
    return db.scalar(stmt)


def get_articles_by_ids(
    db: Session,
    article_ids: list[UUID],
) -> list[CollectedArticle]:
    """
    여러 ID로 아티클을 일괄 조회한다.

    Args:
        db: 데이터베이스 세션
        article_ids: 아티클 UUID 목록

    Returns:
        CollectedArticle 객체 목록
    """
    stmt = select(CollectedArticle).where(CollectedArticle.id.in_(article_ids))
    return list(db.scalars(stmt).all())


def create_article(
    db: Session,
    title: str,
    content: str,
    summary: str,
    source_url: str,
    source_type: str,
    category: str,
    importance_score: float,
    metadata: dict[str, Any] | None = None,
    vector_id: str | None = None,
) -> CollectedArticle:
    """
    새 아티클을 생성한다.

    Args:
        db: 데이터베이스 세션
        title: 아티클 제목
        content: 아티클 내용
        summary: 아티클 요약
        source_url: 소스 URL(유일해야 함)
        source_type: 소스 유형(paper/news/report)
        category: 카테고리
        importance_score: 중요도 점수(0.0-1.0)
        metadata: 추가 메타데이터
        vector_id: Qdrant 벡터 ID(선택)

    Returns:
        생성된 CollectedArticle 객체
    """
    article = CollectedArticle(
        title=title,
        content=content,
        summary=summary,
        source_url=source_url,
        source_type=source_type,
        category=category,
        importance_score=importance_score,
        metadata=metadata or {},
        vector_id=vector_id,
        collected_at=datetime.now(UTC),
    )
    db.add(article)
    _commit_or_rollback(db)
    db.refresh(article)
    return article


def update_article(
    db: Session,
    article_id: UUID,
    title: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    category: str | None = None,
    importance_score: float | None = None,
    metadata: dict[str, Any] | None = None,
    vector_id: str | None = None,
) -> CollectedArticle | None:
    """
    아티클 필드를 업데이트한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID
        title: 새 제목(선택)
        content: 새 내용(선택)
        summary: 새 요약(선택)
        category: 새 카테고리(선택)
        importance_score: 새 중요도 점수(선택)
        metadata: 새 메타데이터(선택)
        vector_id: 새 벡터 ID(선택)

    Returns:
        업데이트된 CollectedArticle 객체 또는 None
    """
    article = get_article_by_id(db, article_id)
    if not article:
        return None

    if title is not None:
        article.title = title
    if content is not None:
        article.content = content
    if summary is not None:
        article.summary = summary
    if category is not None:
        article.category = category
    if importance_score is not None:
        article.importance_score = importance_score
    if metadata is not None:
        article.metadata = metadata
    if vector_id is not None:
        article.vector_id = vector_id

    _commit_or_rollback(db)
    db.refresh(article)
    return article


def delete_article(db: Session, article_id: UUID) -> bool:
    """
    아티클을 삭제한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID

    Returns:
        삭제 성공 시 True, 미존재 시 False
    """
    article = get_article_by_id(db, article_id)
    if not article:
        return False

    db.delete(article)
    _commit_or_rollback(db)
    return True


def get_article_statistics(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict[str, Any]:
    """
    아티클 통계를 조회한다(카테고리/소스 유형 등).

    Args:
        db: 데이터베이스 세션
        date_from: 시작 날짜 필터(선택)
        date_to: 종료 날짜 필터(선택)

    Returns:
        통계 딕셔너리
    """
    filters = []
    if date_from:
        filters.append(CollectedArticle.collected_at >= date_from)
    if date_to:
        filters.append(CollectedArticle.collected_at <= date_to)

    total_stmt = select(func.count()).select_from(CollectedArticle)
    if filters:
        total_stmt = total_stmt.where(and_(*filters))
    total = db.scalar(total_stmt) or 0

    source_type_stmt = select(
        CollectedArticle.source_type,
        func.count(CollectedArticle.id).label("count"),
    ).select_from(CollectedArticle)
    category_stmt = select(
        CollectedArticle.category,
        func.count(CollectedArticle.id).label("count"),
    ).select_from(CollectedArticle)
    avg_score_stmt = select(func.avg(CollectedArticle.importance_score)).select_from(CollectedArticle)

    if filters:
        source_type_stmt = source_type_stmt.where(and_(*filters))
        category_stmt = category_stmt.where(and_(*filters))
        avg_score_stmt = avg_score_stmt.where(and_(*filters))

    source_type_counts = db.execute(
        source_type_stmt.group_by(CollectedArticle.source_type),
    ).all()
    category_counts = db.execute(
        category_stmt.group_by(CollectedArticle.category),
    ).all()
    avg_score = db.scalar(avg_score_stmt)

    return {
        "total": total,
        "by_source_type": dict(source_type_counts),
        "by_category": dict(category_counts),
        "average_importance_score": float(avg_score) if avg_score else 0.0,
    }


def search_articles(
    db: Session,
    search_query: str,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[CollectedArticle], int]:
    """
    제목/본문/요약에서 키워드로 아티클을 검색한다.

    참고: 시맨틱 검색은 Vector DB 작업을 사용한다.
    이 함수는 단순 키워드 검색이다.

    Args:
        db: 데이터베이스 세션
        search_query: 검색 쿼리 문자열
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        (아티클 목록, 총 개수)
    """
    search_pattern = f"%{search_query}%"
    search_condition = or_(
        CollectedArticle.title.ilike(search_pattern),
        CollectedArticle.summary.ilike(search_pattern),
        CollectedArticle.content.ilike(search_pattern),
    )
    total_stmt = select(func.count()).select_from(CollectedArticle).where(search_condition)
    total = db.scalar(total_stmt) or 0
    stmt = (
        select(CollectedArticle)
        .where(search_condition)
        .order_by(desc(CollectedArticle.importance_score))
        .offset(skip)
        .limit(limit)
    )
    articles = list(db.scalars(stmt).all())

    return articles, total


def list_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source_type: str | None = None,
    category: str | None = None,
    min_importance: float | None = None,
) -> list[CollectedArticle]:
    """
    필터를 적용해 아티클 목록을 조회한다(get_articles의 간단 버전).

    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        source_type: 소스 유형 필터(선택)
        category: 카테고리 필터(선택)
        min_importance: 최소 중요도 점수(선택)

    Returns:
        CollectedArticle 객체 목록
    """
    stmt = select(CollectedArticle)

    # 필터 적용
    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    if category:
        stmt = stmt.where(CollectedArticle.category == category)
    if min_importance is not None:
        stmt = stmt.where(CollectedArticle.importance_score >= min_importance)

    # 수집 시각 기준 정렬(최신 우선)
    stmt = stmt.order_by(desc(CollectedArticle.collected_at))

    # 페이지네이션 적용
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_articles(
    db: Session,
    source_type: str | None = None,
) -> int:
    """
    아티클 총 개수를 조회한다(필터 옵션 포함).

    Args:
        db: 데이터베이스 세션
        source_type: 소스 유형 필터(선택)

    Returns:
        아티클 총 개수
    """
    stmt = select(func.count()).select_from(CollectedArticle)
    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    return db.scalar(stmt) or 0


def get_articles_since(
    db: Session,
    since: datetime,
) -> list[CollectedArticle]:
    """
    특정 시각 이후 수집된 아티클을 조회한다.

    Args:
        db: 데이터베이스 세션
        since: 시작 시각

    Returns:
        중요도 점수 기준으로 정렬된 아티클 목록
    """
    stmt = (
        select(CollectedArticle)
        .where(CollectedArticle.collected_at >= since)
        .order_by(desc(CollectedArticle.importance_score))
    )
    return list(db.scalars(stmt).all())


def get_top_articles_by_importance(
    db: Session,
    limit: int = 10,
    since: datetime | None = None,
) -> list[CollectedArticle]:
    """
    중요도 점수 기준 상위 N개 아티클을 조회한다.

    Args:
        db: 데이터베이스 세션
        limit: 반환할 최대 아티클 수
        since: 특정 시각 이후로 필터(선택)

    Returns:
        상위 아티클 목록
    """
    stmt = select(CollectedArticle)
    if since:
        stmt = stmt.where(CollectedArticle.collected_at >= since)
    stmt = stmt.order_by(desc(CollectedArticle.importance_score)).limit(limit)
    return list(db.scalars(stmt).all())
