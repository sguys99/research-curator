"""아티클 관리 및 검색을 위한 라우터."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas.articles import (
    ArticleListResponse,
    ArticleResponse,
    ArticleSearchRequest,
    ArticleSearchResponse,
    ArticleSearchResult,
    ArticleStatisticsResponse,
    BatchArticleRequest,
)
from app.db.crud.articles import (
    delete_article,
    get_article_by_id,
    get_article_statistics,
    get_articles,
    get_articles_by_ids,
    search_articles,
)
from app.db.models import User
from app.db.session import get_db
from app.vector_db.operations import get_vector_operations

router = APIRouter(tags=["articles"], prefix="/articles")


@router.get("", response_model=ArticleListResponse)
def list_articles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    source_type: list[str] | None = Query(None, description="Filter by source type"),
    category: list[str] | None = Query(None, description="Filter by category"),
    min_importance_score: float | None = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum importance score",
    ),
    date_from: datetime | None = Query(None, description="Filter from this date"),
    date_to: datetime | None = Query(None, description="Filter until this date"),
    order_by: str = Query("collected_at", description="Field to order by"),
    order_desc: bool = Query(True, description="Order descending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleListResponse:
    """
    필터/정렬/페이지네이션을 적용해 아티클 목록을 조회한다.

    Args:
        skip: 건너뛸 레코드 수(페이지네이션)
        limit: 반환할 최대 레코드 수
        source_type: 소스 유형 필터(paper, news, report)
        category: 카테고리 필터
        min_importance_score: 최소 중요도 점수(0.0-1.0)
        date_from: 시작 날짜 필터
        date_to: 종료 날짜 필터
        order_by: 정렬 필드(collected_at, importance_score)
        order_desc: True면 내림차순 정렬
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        페이지네이션 정보가 포함된 아티클 목록
    """
    articles, total = get_articles(
        db,
        skip=skip,
        limit=limit,
        source_type=source_type,
        category=category,
        min_importance_score=min_importance_score,
        date_from=date_from,
        date_to=date_to,
        order_by=order_by,
        order_desc=order_desc,
    )

    article_responses = [
        ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            source_url=article.source_url,
            source_type=article.source_type,
            category=article.category,
            importance_score=article.importance_score,
            metadata=article.metadata,
            collected_at=article.collected_at,
            vector_id=article.vector_id,
        )
        for article in articles
    ]

    return ArticleListResponse(
        articles=article_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleResponse:
    """
    ID로 단일 아티클을 조회한다.

    Args:
        article_id: 아티클 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        아티클 상세 정보

    Raises:
        HTTPException: 아티클을 찾지 못한 경우
    """
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    return ArticleResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        summary=article.summary,
        source_url=article.source_url,
        source_type=article.source_type,
        category=article.category,
        importance_score=article.importance_score,
        metadata=article.metadata,
        collected_at=article.collected_at,
        vector_id=article.vector_id,
    )


@router.post("/search", response_model=ArticleSearchResponse)
async def search_semantic(
    request: ArticleSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleSearchResponse:
    """
    자연어 쿼리로 아티클을 시맨틱 검색한다.

    임베딩 기반 유사도 검색을 위해 Vector DB(Qdrant)를 사용한다.

    Args:
        request: 쿼리/필터가 포함된 검색 요청
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        유사도 점수가 포함된 검색 결과
    """
    try:
        # 벡터 연산 클라이언트 획득
        vector_ops = get_vector_operations()

        # 시맨틱 검색 수행
        results = await vector_ops.search_similar_articles(
            query=request.query,
            limit=request.limit or 10,
            score_threshold=request.score_threshold or 0.7,
            source_type=request.source_type,
            category=request.category,
            min_importance_score=request.min_importance_score,
            date_from=request.date_from.isoformat() if request.date_from else None,
            date_to=request.date_to.isoformat() if request.date_to else None,
        )

        # 응답 형식으로 변환
        article_results = []
        for result in results:
            # DB에서 아티클 상세 조회
            article_id = UUID(result["article_id"])
            article = get_article_by_id(db, article_id)
            if article:
                # ArticleResponse를 확장한 ArticleSearchResult 생성
                article_results.append(
                    ArticleSearchResult(
                        id=article.id,
                        title=article.title,
                        content=article.content,
                        summary=article.summary,
                        source_url=article.source_url,
                        source_type=article.source_type,
                        category=article.category,
                        importance_score=article.importance_score,
                        article_metadata=article.metadata if isinstance(article.metadata, dict) else {},
                        collected_at=article.collected_at,
                        vector_id=article.vector_id,
                        published_at=None,
                        similarity_score=result["score"],
                    ),
                )

        return ArticleSearchResponse(
            query=request.query,
            results=article_results,
            total=len(article_results),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get("/{article_id}/similar", response_model=ArticleSearchResponse)
async def get_similar_articles(
    article_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of similar articles"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleSearchResponse:
    """
    아티클 ID를 기준으로 유사 아티클을 조회한다.

    Args:
        article_id: 아티클 UUID
        limit: 반환할 유사 아티클 수
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        유사도 점수가 포함된 유사 아티클 목록

    Raises:
        HTTPException: 아티클을 찾지 못한 경우
    """
    # 원본 아티클 조회
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    if not article.vector_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has no vector embedding",
        )

    try:
        # 벡터 연산 클라이언트 획득
        vector_ops = get_vector_operations()

        # 유사 아티클 검색
        results = await vector_ops.find_similar_articles(
            vector_id=article.vector_id,
            limit=limit + 1,  # 자기 자신 제외를 위해 +1
            score_threshold=0.7,
        )

        # 원본 아티클을 제외하고 응답 형식으로 변환
        article_results = []
        for result in results:
            # 동일 아티클 제외
            if result["article_id"] == str(article_id):
                continue

            # DB에서 아티클 상세 조회
            similar_article_id = UUID(result["article_id"])
            similar_article = get_article_by_id(db, similar_article_id)
            if similar_article:
                article_results.append(
                    ArticleSearchResult(
                        id=similar_article.id,
                        title=similar_article.title,
                        content=similar_article.content,
                        summary=similar_article.summary,
                        source_url=similar_article.source_url,
                        source_type=similar_article.source_type,
                        category=similar_article.category,
                        importance_score=similar_article.importance_score,
                        article_metadata=similar_article.metadata
                        if isinstance(similar_article.metadata, dict)
                        else {},
                        collected_at=similar_article.collected_at,
                        vector_id=similar_article.vector_id,
                        published_at=None,
                        similarity_score=result["score"],
                    ),
                )

        return ArticleSearchResponse(
            query=f"Similar to: {article.title}",
            results=article_results[:limit],
            total=len(article_results),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar articles: {str(e)}",
        ) from e


@router.post("/batch", response_model=ArticleListResponse)
def get_articles_batch(
    request: BatchArticleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleListResponse:
    """
    여러 ID로 아티클을 일괄 조회한다.

    Args:
        request: 아티클 ID 목록이 포함된 요청
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        아티클 목록
    """
    articles = get_articles_by_ids(db, request.article_ids)

    article_responses = [
        ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            source_url=article.source_url,
            source_type=article.source_type,
            category=article.category,
            importance_score=article.importance_score,
            metadata=article.metadata,
            collected_at=article.collected_at,
            vector_id=article.vector_id,
        )
        for article in articles
    ]

    return ArticleListResponse(
        articles=article_responses,
        total=len(article_responses),
        skip=0,
        limit=len(article_responses),
    )


@router.get("/statistics/summary", response_model=ArticleStatisticsResponse)
def get_statistics(
    date_from: datetime | None = Query(None, description="Filter from this date"),
    date_to: datetime | None = Query(None, description="Filter until this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleStatisticsResponse:
    """
    아티클 통계를 조회한다(카테고리/소스 유형 등).

    Args:
        date_from: 시작 날짜 필터
        date_to: 종료 날짜 필터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        통계 요약
    """
    stats = get_article_statistics(db, date_from=date_from, date_to=date_to)

    return ArticleStatisticsResponse(
        total=stats["total"],
        by_source_type=stats["by_source_type"],
        by_category=stats["by_category"],
        average_importance_score=stats["average_importance_score"],
    )


@router.delete("/{article_id}")
def delete_article_by_id(
    article_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    ID로 아티클을 삭제한다.

    Args:
        article_id: 아티클 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        성공 메시지

    Raises:
        HTTPException: 아티클을 찾지 못한 경우
    """
    success = delete_article(db, article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    return {"message": "Article deleted successfully"}


@router.get("/keyword-search", response_model=ArticleListResponse)
def keyword_search(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleListResponse:
    """
    제목/본문/요약에 대해 키워드 검색을 수행한다.

    참고: 시맨틱 검색은 POST /articles/search를 사용한다.

    Args:
        q: 검색 쿼리
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        매칭된 아티클 목록
    """
    articles, total = search_articles(db, search_query=q, skip=skip, limit=limit)

    article_responses = [
        ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            source_url=article.source_url,
            source_type=article.source_type,
            category=article.category,
            importance_score=article.importance_score,
            metadata=article.metadata,
            collected_at=article.collected_at,
            vector_id=article.vector_id,
        )
        for article in articles
    ]

    return ArticleListResponse(
        articles=article_responses,
        total=total,
        skip=skip,
        limit=limit,
    )
