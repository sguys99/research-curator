"""Articles router for article management and search."""

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
    Get list of articles with filtering, sorting, and pagination.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        source_type: Filter by source type (paper, news, report)
        category: Filter by category
        min_importance_score: Minimum importance score (0.0-1.0)
        date_from: Filter articles from this date
        date_to: Filter articles until this date
        order_by: Field to order by (collected_at, importance_score)
        order_desc: Order descending if True
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of articles with pagination info
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
    Get single article by ID.

    Args:
        article_id: Article UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Article details

    Raises:
        HTTPException: If article not found
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
    Semantic search for articles using natural language query.

    Uses Vector DB (Qdrant) for similarity search based on embeddings.

    Args:
        request: Search request with query and filters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Search results with similarity scores
    """
    try:
        # Get vector operations client
        vector_ops = get_vector_operations()

        # Perform semantic search
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

        # Convert results to response format
        from app.api.schemas.articles import ArticleSearchResult

        article_results = []
        for result in results:
            # Get article details from DB
            article_id = UUID(result["article_id"])
            article = get_article_by_id(db, article_id)
            if article:
                # Create ArticleSearchResult which extends ArticleResponse
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
                        article_metadata=article.metadata,
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
    Get similar articles based on article ID.

    Args:
        article_id: Article UUID
        limit: Number of similar articles to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of similar articles with similarity scores

    Raises:
        HTTPException: If article not found
    """
    # Get original article
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
        # Get vector operations client
        vector_ops = get_vector_operations()

        # Find similar articles
        results = await vector_ops.find_similar_articles(
            vector_id=article.vector_id,
            limit=limit + 1,  # +1 to exclude self
            score_threshold=0.7,
        )

        # Filter out the original article and convert to response
        from app.api.schemas.articles import ArticleSearchResult

        article_results = []
        for result in results:
            # Skip if it's the same article
            if result["article_id"] == str(article_id):
                continue

            # Get article details from DB
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
                        article_metadata=similar_article.metadata,
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
    Get multiple articles by IDs (batch retrieval).

    Args:
        request: Batch request with article IDs
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of articles
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
    Get article statistics (counts by category, source type, etc.).

    Args:
        date_from: Filter from this date
        date_to: Filter until this date
        db: Database session
        current_user: Current authenticated user

    Returns:
        Statistics summary
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
    Delete article by ID.

    Args:
        article_id: Article UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If article not found
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
    Keyword-based search in article title, content, and summary.

    Note: For semantic search, use POST /articles/search instead.

    Args:
        q: Search query
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of matching articles
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
