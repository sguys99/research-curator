"""일일 다이제스트용 아티클 선택/필터링 로직."""

import asyncio
import logging
from typing import Any

from app.db.models import CollectedArticle, UserPreference

logger = logging.getLogger(__name__)


# 사용자 선호도에 맞는 최적의 아티클을 선택하는 로직
def select_articles_for_user(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int | None = None,
) -> list[CollectedArticle]:
    """비동기 선택 로직을 동기로 감싼 래퍼."""
    return asyncio.run(select_articles_for_user_async(articles, preferences, limit))


async def select_articles_for_user_async(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int | None = None,
) -> list[CollectedArticle]:
    """
    사용자 선호도에 따라 아티클을 선택/필터링한다.

    전략(시맨틱 검색과 폴백 포함):
    1. Qdrant 시맨틱 검색(벡터화된 경우)
    2. 실패 시 키워드/분야 필터링
    3. 실패 시 제목만 매칭
    4. 실패 시 중요도 랭킹
    5. 카테고리 분포 적용
    6. 중요도 점수 정렬
    7. 상위 N개 선택

    Args:
        articles: 후보 아티클 목록
        preferences: 사용자 선호도
        limit: 최대 선택 수(기본값은 preferences.daily_limit)

    Returns:
        list[CollectedArticle]: 선택된 아티클
    """
    if not articles:
        return []

    limit = limit or preferences.daily_limit or 5

    # 1단계: 시맨틱 검색 우선 시도
    filtered = await _semantic_filter(
        articles,
        preferences,
        limit=limit * 3,  # 분포 적용을 위해 후보를 더 확보
        score_threshold=0.65,
    )

    if filtered:
        logger.info(f"Using semantic search: {len(filtered)} articles")
    else:
        logger.info("Semantic search yielded no results, trying keyword matching")

        # 2단계: 키워드/분야 필터링
        filtered = _filter_by_preferences(articles, preferences)

        if not filtered:
            logger.warning(
                f"No articles match user preferences for "
                f"keywords={preferences.keywords}, fields={preferences.research_fields}. "
                f"Trying fallback strategies.",
            )

            # 3단계: 제목만 키워드 매칭(폴백)
            filtered = _fallback_title_search(articles, preferences)

            if not filtered:
                logger.warning("Title fallback found nothing. Trying importance ranking.")

                # 4단계: 중요도 랭킹으로 최종 폴백
                filtered = _fallback_importance_ranking(articles, limit=limit)

            if not filtered:
                logger.warning(
                    "All filtering strategies failed. Returning empty to avoid "
                    "sending identical digests to all users.",
                )
                return []

            logger.info(f"Fallback strategy succeeded with {len(filtered)} articles")

    # 5단계: 카테고리 분포 적용
    distributed = _apply_category_distribution(filtered, preferences)

    # 6단계: 중요도 점수 정렬
    sorted_articles = sorted(
        distributed,
        key=lambda x: x.importance_score or 0.0,
        reverse=True,
    )

    # 7단계: 상위 N개 선택
    selected = sorted_articles[:limit]

    logger.info(
        f"Selected {len(selected)} articles from {len(articles)} available "
        f"(filtered: {len(filtered)}, distributed: {len(distributed)})",
    )

    return selected


def _filter_by_preferences(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    사용자 연구 분야/키워드로 아티클을 필터링한다.

    Args:
        articles: 후보 아티클 목록
        preferences: 사용자 선호도

    Returns:
        list[CollectedArticle]: 필터링된 아티클
    """
    keywords = preferences.keywords or []
    research_fields = preferences.research_fields or []

    if not keywords and not research_fields:
        return articles

    # 먼저 메타데이터가 충분한 아티클만 선별
    validated_articles = [a for a in articles if _has_sufficient_metadata(a)]

    if not validated_articles:
        logger.warning(
            f"No articles with sufficient metadata found. "
            f"Total articles: {len(articles)}, Validated: {len(validated_articles)}",
        )
        return []

    filtered = []

    for article in validated_articles:
        # 키워드 매칭 여부 확인
        matches_keyword = False
        if keywords:
            # 요약이 비어 있는 경우를 위해 본문 일부(최대 500자) 포함
            article_text = (
                f"{article.title} {article.summary or ''} "
                f"{article.category or ''} {(article.content or '')[:500]}"
            )
            article_text_lower = article_text.lower()
            matches_keyword = any(kw.lower() in article_text_lower for kw in keywords)

        # 연구 분야 매칭 여부 확인
        matches_field = False
        if research_fields:
            article_category = (article.category or "").lower()
            matches_field = any(field.lower() in article_category for field in research_fields)

        # 키워드 또는 연구 분야에 매칭되면 포함
        if matches_keyword or matches_field:
            filtered.append(article)

    return filtered


def _has_sufficient_metadata(article: CollectedArticle) -> bool:
    """
    필터링에 충분한 메타데이터가 있는지 확인한다.

    Args:
        article: 확인할 아티클

    Returns:
        LLM 처리 완료 여부
    """
    # 요약 또는 카테고리가 있어야 하며, 중요도 점수도 설정되어야 함
    has_summary = bool(article.summary and article.summary.strip())
    has_category = bool(article.category and article.category.strip())
    has_score = article.importance_score is not None

    return (has_summary or has_category) and has_score


def _fallback_title_search(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    폴백: 전체 필터링이 실패했을 때 제목만 키워드 매칭한다.

    전체 텍스트 검색보다 제한적이지만, 전부 반환하는 것보다는 낫다.

    Args:
        articles: 후보 아티클 목록
        preferences: 사용자 선호도

    Returns:
        제목에 키워드가 매칭된 아티클
    """
    keywords = preferences.keywords or []

    if not keywords:
        logger.info("No keywords for fallback search")
        return []

    matched = []
    for article in articles:
        if not _has_sufficient_metadata(article):
            continue

        title_lower = article.title.lower()
        if any(kw.lower() in title_lower for kw in keywords):
            matched.append(article)

    logger.info(f"Fallback title search found {len(matched)} articles matching keywords: {keywords}")

    return matched


def _fallback_importance_ranking(
    articles: list[CollectedArticle],
    limit: int = 5,
) -> list[CollectedArticle]:
    """
    최후의 폴백: 중요도 점수로 상위 아티클을 선택한다.

    다른 전략이 모두 실패한 경우, 처리 완료된 아티클 중
    점수가 높은 순으로 반환한다.

    Args:
        articles: 후보 아티클 목록
        limit: 반환 최대 수

    Returns:
        중요도 상위 아티클
    """
    # 검증된 아티클만 사용
    validated = [a for a in articles if _has_sufficient_metadata(a)]

    if not validated:
        logger.warning("No validated articles for importance fallback")
        return []

    # 중요도 점수 내림차순 정렬
    sorted_articles = sorted(
        validated,
        key=lambda x: x.importance_score or 0.0,
        reverse=True,
    )

    selected = sorted_articles[:limit]

    logger.info(
        f"Importance fallback selected {len(selected)} top articles "
        f"from {len(validated)} validated articles",
    )

    return selected


async def _generate_preference_embedding(preferences: UserPreference) -> list[float] | None:
    """
    시맨틱 검색용 사용자 선호도 임베딩을 생성한다.

    research_fields와 keywords를 하나의 텍스트로 합쳐 임베딩한다.

    Args:
        preferences: 사용자 선호도

    Returns:
        임베딩 벡터(실패 시 None)
    """
    # 연구 분야와 키워드로 텍스트 구성
    fields = preferences.research_fields or []
    keywords = preferences.keywords or []

    if not fields and not keywords:
        logger.warning("No fields or keywords to generate embedding from")
        return None

    # 검색 가능한 텍스트로 결합
    preference_text = "Research interests: " + ", ".join(fields)
    if keywords:
        preference_text += ". Keywords: " + ", ".join(keywords)

    logger.info(f"Generating embedding for preference text: {preference_text[:100]}...")

    try:
        from app.processors.embedder import TextEmbedder

        embedder = TextEmbedder()
        embedding = await embedder.embed(preference_text)
        logger.info(f"Generated preference embedding: {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate preference embedding: {e}")
        return None


async def _semantic_filter(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int = 20,
    score_threshold: float = 0.65,
) -> list[CollectedArticle]:
    """
    Qdrant 시맨틱 유사도 검색으로 아티클을 필터링한다.

    전략:
    1. research_fields + keywords로 임베딩 생성
    2. Qdrant에서 유사 아티클 검색
    3. 제공된 목록 내 아티클만 필터링
    4. 임계값 이상 상위 매치 반환

    Args:
        articles: 후보 아티클 목록(vector_id 필요)
        preferences: 사용자 선호도
        limit: 최대 반환 수
        score_threshold: 최소 유사도 점수(0.0~1.0)

    Returns:
        관련도 순으로 정렬된 아티클
    """
    try:
        # 선호도 임베딩 생성
        preference_embedding = await _generate_preference_embedding(preferences)

        if not preference_embedding:
            logger.warning("Could not generate preference embedding, skipping semantic search")
            return []

        # 벡터 연산 클라이언트 확보
        from app.vector_db.operations import VectorOperations

        vector_ops = VectorOperations()

        # vector_id가 있는 아티클만 사용(Qdrant에 임베딩됨)
        vectorized_articles = [a for a in articles if a.vector_id]

        if not vectorized_articles:
            logger.warning(
                f"No articles have vector_id set. Total articles: {len(articles)}, Vectorized: 0",
            )
            return []

        logger.info(f"Performing semantic search on {len(vectorized_articles)} articles")

        # 선호도 임베딩으로 Qdrant 검색
        search_results = vector_ops.qdrant_client.client.query_points(
            collection_name=vector_ops.collection_name,
            query=preference_embedding,
            limit=limit * 2,  # 필터링을 위해 더 많은 결과 확보
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        ).points

        # vector_id -> 아티클 매핑 생성
        article_map = {a.vector_id: a for a in vectorized_articles}

        # 현재 목록에 있는 아티클만 필터링
        scored_articles: list[tuple[CollectedArticle, float]] = []
        for hit in search_results:
            vector_id = str(hit.id)
            if vector_id in article_map:
                scored_articles.append((article_map[vector_id], hit.score))

        # 시맨틱 점수 기준 정렬 후 제한
        scored_articles.sort(key=lambda item: item[1], reverse=True)
        matched_articles = [article for article, _score in scored_articles[:limit]]

        logger.info(
            f"Semantic search found {len(matched_articles)} matches above threshold {score_threshold}",
        )

        return matched_articles

    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        return []


def _semantic_filter_sync(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int = 20,
    score_threshold: float = 0.65,
) -> list[CollectedArticle]:
    """
    시맨틱 필터링의 동기 래퍼.

    select_articles_for_user 같은 동기 코드에서 호출하기 위함.
    """
    try:
        return asyncio.run(_semantic_filter(articles, preferences, limit, score_threshold))
    except Exception as e:
        logger.error(f"Semantic filter sync wrapper failed: {e}")
        return []


def _apply_category_distribution(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    사용자 선호도에 따라 카테고리 분포를 적용한다.

    미사용 쿼터(해당 카테고리에 아티클이 부족한 경우)는
    남은 아티클이 있는 카테고리에 재분배한다.

    Args:
        articles: 필터링된 아티클 목록
        preferences: info_types를 포함한 사용자 선호도

    Returns:
        list[CollectedArticle]: 분포가 적용된 아티클
    """
    info_types = preferences.info_types or {}

    # 기본 분포(미지정 시)
    default_distribution = {"paper": 50, "news": 30, "report": 20}
    distribution = {**default_distribution, **info_types}

    # 분포를 비율로 정규화
    total = sum(distribution.values())
    if total == 0:
        return articles

    normalized = {k: v / total for k, v in distribution.items()}

    # 유형별 그룹화
    by_type = {
        "paper": [a for a in articles if a.source_type == "paper"],
        "news": [a for a in articles if a.source_type == "news"],
        "report": [a for a in articles if a.source_type == "report"],
    }

    total_articles = len(articles)
    targets = {k: int(total_articles * normalized.get(k, 0)) for k in by_type}

    # 1차 선택 + 미사용 쿼터 계산
    selected: list[CollectedArticle] = []
    remaining_quota = 0
    types_with_surplus: list[str] = []

    for typ in by_type:
        available = len(by_type[typ])
        take = min(targets[typ], available)
        selected.extend(_select_top_by_importance(by_type[typ], take))
        remaining_quota += targets[typ] - take
        if available > take:
            types_with_surplus.append(typ)

    # 2차: 미사용 쿼터를 남은 아티클이 있는 카테고리에 재분배
    if remaining_quota > 0 and types_with_surplus:
        already_selected_ids = {id(a) for a in selected}
        for typ in types_with_surplus:
            if remaining_quota <= 0:
                break
            leftover = [a for a in by_type[typ] if id(a) not in already_selected_ids]
            take = min(remaining_quota, len(leftover))
            selected.extend(_select_top_by_importance(leftover, take))
            remaining_quota -= take

    return selected


def _select_top_by_importance(articles: list[CollectedArticle], count: int) -> list[CollectedArticle]:
    """
    중요도 점수 기준으로 상위 N개를 선택한다.

    Args:
        articles: 후보 아티클 목록
        count: 선택 개수

    Returns:
        list[CollectedArticle]: 상위 N개 아티클
    """
    sorted_articles = sorted(articles, key=lambda x: x.importance_score or 0.0, reverse=True)
    return sorted_articles[:count]


def filter_by_date_range(
    articles: list[CollectedArticle],
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> list[CollectedArticle]:
    """
    수집 일자 범위로 아티클을 필터링한다.

    Args:
        articles: 후보 아티클 목록
        start_date: 시작 일자(포함)
        end_date: 종료 일자(포함)

    Returns:
        list[CollectedArticle]: 필터링된 아티클
    """
    filtered = articles

    if start_date:
        filtered = [a for a in filtered if a.collected_at and a.collected_at >= start_date]

    if end_date:
        filtered = [a for a in filtered if a.collected_at and a.collected_at <= end_date]

    return filtered


def get_category_distribution(articles: list[CollectedArticle]) -> dict[str, int]:
    """
    카테고리별 아티클 분포를 계산한다.

    Args:
        articles: 분석할 아티클 목록

    Returns:
        dict: 카테고리별 개수
    """
    distribution = {"paper": 0, "news": 0, "report": 0, "other": 0}

    for article in articles:
        category = article.source_type or "other"
        if category in distribution:
            distribution[category] += 1
        else:
            distribution["other"] += 1

    return distribution
