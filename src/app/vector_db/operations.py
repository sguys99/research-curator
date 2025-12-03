"""Vector database CRUD operations for article embeddings.

This module provides functions to insert, update, delete, and search
article embeddings in Qdrant vector database.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from qdrant_client.http import models

from app.processors.embedder import TextEmbedder, get_embedder
from app.vector_db.client import QdrantClientWrapper, get_qdrant_client
from app.vector_db.schema import CollectionSchema

logger = logging.getLogger(__name__)


class VectorOperations:
    """Vector database operations for article embeddings."""

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper | None = None,
        embedder: TextEmbedder | None = None,
        collection_name: str | None = None,
    ):
        """Initialize vector operations.

        Args:
            qdrant_client: Qdrant client instance (defaults to global client)
            embedder: Text embedder instance (defaults to global embedder)
            collection_name: Collection name (defaults to CollectionSchema.COLLECTION_NAME)
        """
        self.qdrant_client = qdrant_client or get_qdrant_client()
        self.embedder = embedder or get_embedder()
        self.collection_name = collection_name or CollectionSchema.COLLECTION_NAME

        logger.info(f"VectorOperations initialized for collection: {self.collection_name}")

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
        """Insert single article embedding into Qdrant.

        Args:
            article_id: UUID of the article (from PostgreSQL)
            title: Article title
            content: Article content
            summary: Article summary (optional)
            source_type: paper/news/report
            category: AI, ML, NLP, etc.
            importance_score: 0.0 - 1.0
            metadata: Additional metadata

        Returns:
            Vector ID (point ID in Qdrant)

        Raises:
            RuntimeError: If insertion fails

        Examples:
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
            # Generate embedding
            embedding = await self.embedder.embed_article(
                title=title,
                content=content,
                summary=summary,
            )

            # Generate vector ID
            vector_id = str(uuid.uuid4())

            # Prepare payload
            payload = {
                "article_id": article_id,
                "title": title,
                "summary": summary or "",
                "source_type": source_type,
                "category": category,
                "importance_score": importance_score,
                "collected_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            # Insert into Qdrant
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
                f"Inserted article '{title[:50]}...' "
                f"(article_id={article_id}, vector_id={vector_id})",
            )

            return vector_id

        except Exception as e:
            logger.error(f"Failed to insert article: {e}")
            raise RuntimeError(f"Article insertion failed: {e}") from e

    async def insert_articles_batch(
        self,
        articles: list[dict[str, Any]],
        batch_size: int = 10,
    ) -> list[str]:
        """Insert multiple articles in batch.

        Args:
            articles: List of article dicts with keys:
                - article_id: UUID string
                - title: str
                - content: str
                - summary: str (optional)
                - source_type: str (optional, default: "paper")
                - category: str (optional, default: "AI")
                - importance_score: float (optional, default: 0.5)
                - metadata: dict (optional)
            batch_size: Number of articles to process at once

        Returns:
            List of vector IDs

        Examples:
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
            # Generate embeddings for all articles in batch
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

            # Prepare points for Qdrant
            points = []
            vector_ids = []

            for article, embedding in zip(articles, embeddings, strict=False):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)

                payload = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "source_type": article.get("source_type", "paper"),
                    "category": article.get("category", "AI"),
                    "importance_score": article.get("importance_score", 0.5),
                    "collected_at": datetime.utcnow().isoformat(),
                    "metadata": article.get("metadata", {}),
                }

                points.append(
                    models.PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload,
                    ),
                )

            # Insert all points
            self.qdrant_client.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Batch inserted {len(articles)} articles into Qdrant")

            return vector_ids

        except Exception as e:
            logger.error(f"Failed to batch insert articles: {e}")
            raise RuntimeError(f"Batch insertion failed: {e}") from e

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
        regenerate_embedding: bool = False,
    ) -> bool:
        """Update article in Qdrant.

        Args:
            vector_id: Vector ID (point ID in Qdrant)
            title: New title (optional)
            content: New content (optional)
            summary: New summary (optional)
            source_type: New source type (optional)
            category: New category (optional)
            importance_score: New importance score (optional)
            metadata: New metadata (optional)
            regenerate_embedding: If True, regenerate embedding from new content

        Returns:
            True if update successful, False otherwise

        Examples:
            >>> success = await ops.update_article(
            ...     vector_id="vector-id-123",
            ...     importance_score=0.95,
            ...     category="NLP"
            ... )
        """
        try:
            # Get current point
            current = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
            )

            if not current:
                logger.error(f"Vector ID {vector_id} not found")
                return False

            current_payload = current[0].payload

            # Update payload fields
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

            # Regenerate embedding if needed
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

                # Update with new embedding
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
                # Update payload only
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

    def delete_article(self, vector_id: str) -> bool:
        """Delete article from Qdrant.

        Args:
            vector_id: Vector ID (point ID in Qdrant)

        Returns:
            True if deletion successful, False otherwise

        Examples:
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
        """Delete multiple articles in batch.

        Args:
            vector_ids: List of vector IDs

        Returns:
            True if deletion successful, False otherwise

        Examples:
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
        """Retrieve article by vector ID.

        Args:
            vector_id: Vector ID (point ID in Qdrant)

        Returns:
            Article data dict or None if not found

        Examples:
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
        """Retrieve multiple articles by vector IDs.

        Args:
            vector_ids: List of vector IDs

        Returns:
            List of article data dicts

        Examples:
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
        """Count total number of articles in collection.

        Returns:
            Number of articles

        Examples:
            >>> count = ops.count_articles()
            >>> print(f"Total articles: {count}")
        """
        try:
            info = self.qdrant_client.get_collection_info(self.collection_name)
            return info["points_count"] if info else 0

        except Exception as e:
            logger.error(f"Failed to count articles: {e}")
            return 0

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
        """Search for similar articles using natural language query.

        Args:
            query: Natural language search query
            limit: Maximum number of results (default: 10)
            score_threshold: Minimum similarity score (default: 0.7)
            source_type: Filter by source types (e.g., ["paper", "news"])
            category: Filter by categories (e.g., ["AI", "NLP"])
            min_importance_score: Minimum importance score (0.0 - 1.0)
            date_from: Filter articles from this date (ISO format)
            date_to: Filter articles until this date (ISO format)

        Returns:
            List of similar articles with scores

        Examples:
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
            # Generate query embedding
            query_embedding = await self.embedder.embed(query)

            # Build filters
            query_filter = self._build_search_filter(
                source_type=source_type,
                category=category,
                min_importance_score=min_importance_score,
                date_from=date_from,
                date_to=date_to,
            )

            # Search in Qdrant using query_points
            search_results = self.qdrant_client.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter if query_filter else None,
                with_payload=True,
                with_vectors=False,
            ).points

            # Format results
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

    async def find_similar_articles(
        self,
        article_id: str | None = None,
        vector_id: str | None = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Find articles similar to a given article.

        Args:
            article_id: Article ID (from PostgreSQL) to find similar to
            vector_id: Vector ID (from Qdrant) to find similar to
            limit: Maximum number of results (default: 10)
            score_threshold: Minimum similarity score (default: 0.7)
            source_type: Filter by source types
            category: Filter by categories

        Returns:
            List of similar articles with scores

        Examples:
            >>> similar = await ops.find_similar_articles(
            ...     vector_id="vector-id-123",
            ...     limit=5,
            ...     score_threshold=0.8
            ... )
        """
        try:
            # Get the reference article
            if vector_id:
                ref_article = self.get_article(vector_id)
                if not ref_article:
                    logger.error(f"Reference article with vector_id={vector_id} not found")
                    return []
            elif article_id:
                # Search by article_id in payload
                # First, we need to find the vector_id by article_id
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

            # Get vector for the reference article
            ref_points = self.qdrant_client.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_vectors=True,
            )

            if not ref_points:
                logger.error(f"Vector not found for vector_id={vector_id}")
                return []

            query_vector = ref_points[0].vector

            # Build filters
            query_filter = self._build_search_filter(
                source_type=source_type,
                category=category,
            )

            # Search similar articles using query_points
            search_results = self.qdrant_client.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit + 1,  # +1 to exclude self
                score_threshold=score_threshold,
                query_filter=query_filter if query_filter else None,
                with_payload=True,
                with_vectors=False,
            ).points

            # Format results and exclude the reference article itself
            results = []
            for hit in search_results:
                if hit.id != vector_id:  # Exclude self
                    result = {
                        "vector_id": hit.id,
                        "score": hit.score,
                        **hit.payload,
                    }
                    results.append(result)

            # Limit to requested number
            results = results[:limit]

            logger.info(f"Found {len(results)} similar articles for vector_id={vector_id}")

            return results

        except Exception as e:
            logger.error(f"Failed to find similar articles: {e}")
            return []

    def _build_search_filter(
        self,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
        min_importance_score: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> models.Filter | None:
        """Build Qdrant filter for search queries.

        Args:
            source_type: Filter by source types
            category: Filter by categories
            min_importance_score: Minimum importance score
            date_from: Filter from this date
            date_to: Filter until this date

        Returns:
            Qdrant Filter object or None if no filters
        """
        must_conditions = []

        # Source type filter
        if source_type:
            must_conditions.append(
                models.FieldCondition(
                    key="source_type",
                    match=models.MatchAny(any=source_type),
                ),
            )

        # Category filter
        if category:
            must_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchAny(any=category),
                ),
            )

        # Importance score filter
        if min_importance_score is not None:
            must_conditions.append(
                models.FieldCondition(
                    key="importance_score",
                    range=models.Range(gte=min_importance_score),
                ),
            )

        # Date range filter
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

        # Return filter if any conditions exist
        if must_conditions:
            return models.Filter(must=must_conditions)

        return None


# Global operations instance
_vector_ops: VectorOperations | None = None


def get_vector_operations() -> VectorOperations:
    """Get or create global vector operations instance.

    Returns:
        Singleton VectorOperations instance
    """
    global _vector_ops
    if _vector_ops is None:
        _vector_ops = VectorOperations()
    return _vector_ops
