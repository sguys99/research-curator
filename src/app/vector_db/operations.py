"""아티클 임베딩을 위한 벡터 DB CRUD 작업."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from qdrant_client.http import models

from app.processors.embedder import TextEmbedder, get_embedder
from app.vector_db.client import QdrantClientWrapper, get_qdrant_client
from app.vector_db.exceptions import VectorDBOperationError
from app.vector_db.schema import CollectionSchema

logger = logging.getLogger(__name__)


# 벡터 DB CRUD 작업:
# - 임베딩 삽입/수정/삭제, 시맨틱 검색, 유사 아티클, 필터링 및 메타데이터 관리
class VectorOperations:
    """아티클 임베딩용 벡터 DB 작업."""

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper | None = None,
        embedder: TextEmbedder | None = None,
        collection_name: str | None = None,
    ) -> None:
        """벡터 작업 클래스를 초기화한다.

        Args:
            qdrant_client: Qdrant 클라이언트(기본값: 전역 클라이언트)
            embedder: 텍스트 임베더(기본값: 전역 임베더)
            collection_name: 컬렉션 이름(기본값: CollectionSchema.COLLECTION_NAME)
        """
        # 싱글톤 의존성 주입
        self.qdrant_client = qdrant_client or get_qdrant_client()
        self.embedder = embedder or get_embedder()
        self.collection_name = collection_name or CollectionSchema.COLLECTION_NAME

        logger.info(f"VectorOperations initialized for collection: {self.collection_name}")

    # 단일 아티클 삽입: 생성
    async def insert_article(
        self,
        article_id: str,
        title: str,
        content: str,
        summary: str | None = None,
        source_type: str = "paper",
        category: str = "AI",
        importance_score: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """단일 아티클 임베딩을 Qdrant에 삽입한다.

        Args:
            article_id: 아티클 UUID(PostgreSQL)
            title: 아티클 제목
            content: 아티클 본문
            summary: 아티클 요약(선택)
            source_type: paper/news/report
            category: AI, ML, NLP 등
            importance_score: 0.0 - 1.0
            metadata: 추가 메타데이터

        Returns:
            벡터 ID(Qdrant point ID)

        Raises:
            VectorDBOperationError: 삽입 실패 시

        예시:
            >>> ops = VectorOperations()
            >>> vector_id = await ops.insert_article(
            ...     article_id="123e4567-e89b-12d3-a456-426614174000",
            ...     title="Attention Is All You Need",
            ...     content="We propose a new architecture...",
            ...     summary="Transformer 논문입니다.",
            ...     source_type="paper",
            ...     category="NLP",
            ...     importance_score=0.95
            ... )
        """
        try:
            # 임베딩 생성
            embedding = await self.embedder.embed_article(
                title=title,
                content=content,
                summary=summary,
            )

            # 벡터 ID 생성
            vector_id = str(uuid.uuid4())

            # 페이로드 구성
            payload = {
                "article_id": article_id,
                "title": title,
                "summary": summary or "",
                "source_type": source_type,
                "category": category,
                "importance_score": importance_score,
                "collected_at": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }

            # Qdrant에 삽입
            self.qdrant_client.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload,
                    ),
                ],
            )

            logger.info(
                f"Inserted article '{title[:50]}...' (article_id={article_id}, vector_id={vector_id})",
            )

            return vector_id

        except Exception as e:
            logger.error(f"Failed to insert article: {e}")
            raise VectorDBOperationError(f"Article insertion failed: {e}") from e

    async def insert_articles_batch(
        self,
        articles: list[dict[str, Any]],
        batch_size: int = 10,
    ) -> list[str]:
        """다수 아티클을 배치로 삽입한다.

        Args:
            articles: 아래 키를 가진 아티클 dict 목록
                - article_id: UUID 문자열
                - title: str
                - content: str
                - summary: str (선택)
                - source_type: str (선택, 기본값: "paper")
                - category: str (선택, 기본값: "AI")
                - importance_score: float (선택, 기본값: 0.5)
                - metadata: dict (선택)
            batch_size: 한 번에 처리할 개수

        Returns:
            벡터 ID 목록

        예시:
            >>> articles = [
            ...     {
            ...         "article_id": "uuid-1",
            ...         "title": "Paper 1",
            ...         "content": "Content 1",
            ...         "summary": "Summary 1",
            ...         "source_type": "paper",
            ...         "category": "AI",
            ...         "importance_score": 0.9,
            ...     },
            ...     # ... more articles
            ... ]
            >>> vector_ids = await ops.insert_articles_batch(articles)
        """
        if not articles:
            logger.warning("Empty articles list provided")
            return []

        try:
            # 배치 임베딩 생성
            embeddings = await self.embedder.embed_articles_batch(
                articles=[
                    {
                        "title": a.get("title", ""),
                        "content": a.get("content", ""),
                        "summary": a.get("summary"),
                    }
                    for a in articles
                ],
                batch_size=batch_size,
            )

            # Qdrant 포인트 구성
            points = []
            vector_ids = []

            for article, embedding in zip(articles, embeddings, strict=True):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)

                payload = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "source_type": article.get("source_type", "paper"),
                    "category": article.get("category", "AI"),
                    "importance_score": article.get("importance_score", 0.5),
                    "collected_at": datetime.now(UTC).isoformat(),
                    "metadata": article.get("metadata", {}),
                }

                points.append(
                    models.PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload,
                    ),
                )

            # 전체 포인트 삽입
            self.qdrant_client.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Batch inserted {len(articles)} articles into Qdrant")

            return vector_ids

        except Exception as e:
            logger.error(f"Failed to batch insert articles: {e}")
            raise VectorDBOperationError(f"Batch insertion failed: {e}") from e

    # 아티클 업데이트: 수정
    async def update_article(
        self,
        vector_id: str,
        title: str | None = None,
        content: str | None = None,
        summary: str | None = None,
        source_type: str | None = None,
        category: str | None = None,
        importance_score: float | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_embedding: bool = False,  # False이면 메타 데이터만 업데이트
    ) -> bool:
        """Qdrant의 아티클을 업데이트한다.

        Args:
            vector_id: 벡터 ID(Qdrant point ID)
            title: 새 제목(선택)
            content: 새 본문(선택)
            summary: 새 요약(선택)
            source_type: 새 소스 타입(선택)
            category: 새 카테고리(선택)
            importance_score: 새 중요도 점수(선택)
            metadata: 새 메타데이터(선택)
            regenerate_embedding: True면 새 내용으로 임베딩 재생성

        Returns:
            업데이트 성공 여부

        예시:
            >>> success = await ops.update_article(
            ...     vector_id="vector-id-123",
            ...     importance_score=0.95,
            ...     category="NLP"
            ... )
        """
        try:
            # 현재 포인트 조회
            current = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
            )

            if not current:
                logger.error(f"Vector ID {vector_id} not found")
                return False

            current_payload = current[0].payload

            # 페이로드 필드 업데이트
            updated_payload = dict(current_payload)

            if title is not None:
                updated_payload["title"] = title
            if summary is not None:
                updated_payload["summary"] = summary
            if source_type is not None:
                updated_payload["source_type"] = source_type
            if category is not None:
                updated_payload["category"] = category
            if importance_score is not None:
                updated_payload["importance_score"] = importance_score
            if metadata is not None:
                updated_payload["metadata"] = metadata

            # 필요 시 임베딩 재생성
            if regenerate_embedding and (
                title is not None or content is not None or summary is not None
            ):
                new_title = title or current_payload.get("title", "")
                new_content = content or ""
                new_summary = summary or current_payload.get("summary")

                new_embedding = await self.embedder.embed_article(
                    title=new_title,
                    content=new_content,
                    summary=new_summary,
                )

                # 새 임베딩으로 업데이트
                self.qdrant_client.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        models.PointStruct(
                            id=vector_id,
                            vector=new_embedding,
                            payload=updated_payload,
                        ),
                    ],
                )
            else:
                # 페이로드만 업데이트
                self.qdrant_client.client.set_payload(
                    collection_name=self.collection_name,
                    payload=updated_payload,
                    points=[vector_id],
                )

            logger.info(f"Updated article with vector_id={vector_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update article: {e}")
            return False

    # 단일 삭제: 삭제
    def delete_article(self, vector_id: str) -> bool:
        """Qdrant에서 아티클을 삭제한다.

        Args:
            vector_id: 벡터 ID(Qdrant point ID)

        Returns:
            삭제 성공 여부

        예시:
            >>> success = ops.delete_article("vector-id-123")
        """
        try:
            self.qdrant_client.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[vector_id]),
            )

            logger.info(f"Deleted article with vector_id={vector_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete article: {e}")
            return False

    def delete_articles_batch(self, vector_ids: list[str]) -> bool:
        """다수 아티클을 배치로 삭제한다.

        Args:
            vector_ids: 벡터 ID 목록

        Returns:
            삭제 성공 여부

        예시:
            >>> success = ops.delete_articles_batch(["id1", "id2", "id3"])
        """
        try:
            self.qdrant_client.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=vector_ids),
            )

            logger.info(f"Batch deleted {len(vector_ids)} articles")
            return True

        except Exception as e:
            logger.error(f"Failed to batch delete articles: {e}")
            return False

    def get_article(self, vector_id: str) -> dict[str, Any] | None:
        """벡터 ID로 아티클을 조회한다.

        Args:
            vector_id: 벡터 ID(Qdrant point ID)

        Returns:
            아티클 데이터 dict(없으면 None)

        예시:
            >>> article = ops.get_article("vector-id-123")
            >>> print(article["title"])
        """
        try:
            results = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_payload=True,
                with_vectors=False,
            )

            if not results:
                logger.warning(f"Article with vector_id={vector_id} not found")
                return None

            point = results[0]
            return {
                "vector_id": point.id,
                **point.payload,
            }

        except Exception as e:
            logger.error(f"Failed to get article: {e}")
            return None

    def get_articles_batch(self, vector_ids: list[str]) -> list[dict[str, Any]]:
        """여러 벡터 ID로 아티클을 조회한다.

        Args:
            vector_ids: 벡터 ID 목록

        Returns:
            아티클 데이터 dict 목록

        예시:
            >>> articles = ops.get_articles_batch(["id1", "id2", "id3"])
        """
        try:
            results = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=vector_ids,
                with_payload=True,
                with_vectors=False,
            )

            articles = []
            for point in results:
                articles.append(
                    {
                        "vector_id": point.id,
                        **point.payload,
                    },
                )

            logger.info(f"Retrieved {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            return []

    def count_articles(self) -> int:
        """컬렉션 내 아티클 총 개수를 반환한다.

        Returns:
            아티클 개수

        예시:
            >>> count = ops.count_articles()
            >>> print(f"Total articles: {count}")
        """
        try:
            info = self.qdrant_client.get_collection_info(self.collection_name)
            return info["points_count"] if info else 0

        except Exception as e:
            logger.error(f"Failed to count articles: {e}")
            return 0

    # 자연어 기반 유사 아티클 검색: 예) 트랜스포머 검색(임베딩 필요)
    async def search_similar_articles(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
        min_importance_score: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """자연어 질의로 유사 아티클을 검색한다.

        Args:
            query: 자연어 검색 질의
            limit: 최대 결과 수(기본값: 10)
            score_threshold: 최소 유사도 점수(기본값: 0.7)
            source_type: 소스 타입 필터(예: ["paper", "news"])
            category: 카테고리 필터(예: ["AI", "NLP"])
            min_importance_score: 최소 중요도 점수(0.0 - 1.0)
            date_from: 시작 일자(ISO 형식)
            date_to: 종료 일자(ISO 형식)

        Returns:
            점수를 포함한 유사 아티클 목록

        예시:
            >>> results = await ops.search_similar_articles(
            ...     query="transformer architecture optimization",
            ...     limit=5,
            ...     score_threshold=0.8,
            ...     source_type=["paper"],
            ...     category=["NLP", "AI"],
            ...     min_importance_score=0.9
            ... )
        """
        try:
            # 질의 임베딩 생성
            query_embedding = await self.embedder.embed(query)

            # 필터 구성
            query_filter = self._build_search_filter(
                source_type=source_type,
                category=category,
                min_importance_score=min_importance_score,
                date_from=date_from,
                date_to=date_to,
            )

            # query_points로 Qdrant 검색
            search_results = self.qdrant_client.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter if query_filter else None,
                with_payload=True,
                with_vectors=False,
            ).points

            # 결과 포맷팅
            results = []
            for hit in search_results:
                result = {
                    "vector_id": hit.id,
                    "score": hit.score,
                    **hit.payload,
                }
                results.append(result)

            logger.info(
                f"Search query '{query[:50]}...' returned {len(results)} results "
                f"(threshold: {score_threshold})",
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search articles: {e}")
            return []

    # ID 기반 유사 아티클 찾기: 예) 이 논문과 유사한 논문(임베딩 필요, 빠름)
    # 검색 방법: vector_id 또는 article_id
    async def find_similar_articles(
        self,
        article_id: str | None = None,
        vector_id: str | None = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """특정 아티클과 유사한 아티클을 찾는다.

        Args:
            article_id: PostgreSQL 아티클 ID(유사 검색 기준)
            vector_id: Qdrant 벡터 ID(유사 검색 기준)
            limit: 최대 결과 수(기본값: 10)
            score_threshold: 최소 유사도 점수(기본값: 0.7)
            source_type: 소스 타입 필터
            category: 카테고리 필터

        Returns:
            점수를 포함한 유사 아티클 목록

        예시:
            >>> similar = await ops.find_similar_articles(
            ...     vector_id="vector-id-123",
            ...     limit=5,
            ...     score_threshold=0.8
            ... )
        """
        try:
            # 기준 아티클 확보
            if vector_id:
                ref_article = self.get_article(vector_id)
                if not ref_article:
                    logger.error(f"Reference article with vector_id={vector_id} not found")
                    return []
            elif article_id:
                # payload에서 article_id로 검색
                # 먼저 article_id로 vector_id를 찾는다
                search_by_id = self.qdrant_client.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="article_id",
                                match=models.MatchValue(value=article_id),
                            ),
                        ],
                    ),
                    limit=1,
                    with_payload=True,
                    with_vectors=True,
                )

                if not search_by_id[0]:
                    logger.error(f"Reference article with article_id={article_id} not found")
                    return []

                ref_point = search_by_id[0][0]
                vector_id = ref_point.id
                query_vector = ref_point.vector
            else:
                logger.error("Either article_id or vector_id must be provided")
                return []

            # 기준 아티클 벡터 조회
            ref_points = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_vectors=True,
            )

            if not ref_points:
                logger.error(f"Vector not found for vector_id={vector_id}")
                return []

            query_vector = ref_points[0].vector

            # 필터 구성
            query_filter = self._build_search_filter(
                source_type=source_type,
                category=category,
            )

            # query_points로 유사 아티클 검색
            search_results = self.qdrant_client.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit + 1,  # +1 to exclude self
                score_threshold=score_threshold,
                query_filter=query_filter if query_filter else None,
                with_payload=True,
                with_vectors=False,
            ).points

            # 결과 포맷팅 및 자기 자신 제외
            results = []
            for hit in search_results:
                if hit.id != vector_id:  # 자기 자신 제외
                    result = {
                        "vector_id": hit.id,
                        "score": hit.score,
                        **hit.payload,
                    }
                    results.append(result)

            # 요청 수로 제한
            results = results[:limit]

            logger.info(f"Found {len(results)} similar articles for vector_id={vector_id}")

            return results

        except Exception as e:
            logger.error(f"Failed to find similar articles: {e}")
            return []

    # SQL처럼 검색 필터 조건 생성
    def _build_search_filter(
        self,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
        min_importance_score: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> models.Filter | None:
        """검색용 Qdrant 필터를 생성한다.

        Args:
            source_type: 소스 타입 필터
            category: 카테고리 필터
            min_importance_score: 최소 중요도 점수
            date_from: 시작 일자
            date_to: 종료 일자

        Returns:
            Qdrant 필터 객체(조건이 없으면 None)
        """
        must_conditions = []

        # 소스 타입 필터
        if source_type:
            must_conditions.append(
                models.FieldCondition(
                    key="source_type",
                    match=models.MatchAny(any=source_type),
                ),
            )

        # 카테고리 필터
        if category:
            must_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchAny(any=category),
                ),
            )

        # 중요도 점수 필터
        if min_importance_score is not None:
            must_conditions.append(
                models.FieldCondition(
                    key="importance_score",
                    range=models.Range(gte=min_importance_score),
                ),
            )

        # 날짜 범위 필터
        if date_from or date_to:
            range_params = {}
            if date_from:
                range_params["gte"] = date_from
            if date_to:
                range_params["lte"] = date_to

            must_conditions.append(
                models.FieldCondition(
                    key="collected_at",
                    range=models.Range(**range_params),
                ),
            )

        # 조건이 있으면 필터 반환
        if must_conditions:
            return models.Filter(must=must_conditions)

        return None


# 전역 operations 인스턴스
_vector_ops: VectorOperations | None = None


def get_vector_operations() -> VectorOperations:
    """전역 VectorOperations 인스턴스를 반환한다.

    Returns:
        싱글턴 VectorOperations 인스턴스
    """
    global _vector_ops
    if _vector_ops is None:
        _vector_ops = VectorOperations()
    return _vector_ops


# # 전체 워크플로우 예시
# # 1. VectorOperations 인스턴스 가져오기
# ops = get_vector_operations()

# # 2. 새 논문 수집 (PostgreSQL에 먼저 저장했다고 가정)
# article_id = "123e4567-e89b-12d3-a456-426614174000"  # PostgreSQL UUID

# # 3. 벡터 DB에 삽입
# vector_id = await ops.insert_article(
#     article_id=article_id,
#     title="Attention Is All You Need",
#     content="We propose a new simple network architecture...",
#     summary="Transformer 아키텍처를 제안하는 논문입니다.",
#     source_type="paper",
#     category="NLP",
#     importance_score=0.95,
#     metadata={"authors": ["Vaswani et al."], "year": 2017}
# )
# # 반환 예시: "550e8400-e29b-41d4-a716-446655440000"

# # 4. 사용자 검색
# search_results = await ops.search_similar_articles(
#     query="자연어 처리를 위한 attention 메커니즘",
#     limit=10,
#     score_threshold=0.8,
#     source_type=["paper"],
#     category=["NLP", "AI"],
#     min_importance_score=0.9
# )

# # 5. 유사 논문 추천
# similar_papers = await ops.find_similar_articles(
#     vector_id=vector_id,
#     limit=5,
#     score_threshold=0.85,
#     category=["NLP"]
# )

# # 6. 중요도 점수 업데이트 (사용자 피드백 반영)
# await ops.update_article(
#     vector_id=vector_id,
#     importance_score=0.98,  # 피드백 후 점수 상승
#     regenerate_embedding=False
# )

# # 7. 아티클 개수 확인
# total = ops.count_articles()
# print(f"DB 내 논문 총 개수: {total}")
