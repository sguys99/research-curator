"""데이터 수집/처리/이메일 발송 스케줄 작업."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.collectors.arxiv import ArxivCollector
from app.collectors.base import CollectedData
from app.collectors.news import NewsCollector
from app.core.retry import async_with_retry
from app.db import crud
from app.db.models import UserPreference
from app.db.session import SessionLocal
from app.email.builder import EmailBuilder
from app.email.selection import select_articles_for_user_async
from app.email.sender import EmailSender
from app.processors.classifier import ContentClassifier
from app.processors.embedder import TextEmbedder
from app.processors.evaluator import ImportanceEvaluator
from app.processors.summarizer import ArticleSummarizer

logger = logging.getLogger(__name__)


# 비동기 호출을 감싸는 헬퍼 함수
async def summarize_article(title: str, content: str) -> str:
    """아티클 요약 비동기 래퍼."""
    summarizer = ArticleSummarizer()
    return await summarizer.summarize(title=title, content=content)


async def evaluate_importance(title: str, content: str) -> float:
    """중요도 평가 비동기 래퍼."""
    evaluator = ImportanceEvaluator()
    result = await evaluator.evaluate(title=title, content=content)
    return result.get("importance_score", 0.5)


async def classify_article_type(title: str, content: str) -> str:
    """아티클 분류 비동기 래퍼."""
    classifier = ContentClassifier()
    result = await classifier.classify(title=title, content=content)
    return result.get("category", "other")


async def generate_embedding(text: str) -> list[float]:
    """임베딩 생성 비동기 래퍼."""
    embedder = TextEmbedder()
    return await embedder.embed(text)


async def collect_data_task_async() -> None:
    """
    다양한 소스에서 데이터를 수집하는 스케줄 작업.

    수집 소스:
    - arXiv(연구 논문)
    - 뉴스 소스(TechCrunch 등)
    - Google Scholar(예정)

    매일 01:00 KST 실행
    """
    logger.info("=" * 60)
    logger.info("Starting data collection task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    collected_count = 0
    error_count = 0

    try:
        # 선호도를 가진 사용자 목록 조회(수집 대상 결정)
        users = crud.list_users(db)
        logger.info(f"Found {len(users)} users")

        if not users:
            logger.warning("No users found, skipping data collection")
            return

        # 사용자들의 연구 분야/키워드 집계
        all_fields = set()
        all_keywords = set()

        for user in users:
            pref = crud.get_user_preference(db, user.id)
            if pref:
                all_fields.update(pref.research_fields)
                all_keywords.update(pref.keywords)

        logger.info(f"Collecting for {len(all_fields)} fields and {len(all_keywords)} keywords")

        # 1) arXiv 수집
        logger.info("\n1. Collecting from arXiv...")
        arxiv_collector = ArxivCollector()

        for field in all_fields:
            try:
                articles = await async_with_retry(
                    lambda f=field: arxiv_collector.collect(query=f, limit=5),
                    max_attempts=3,
                )

                for article_data in articles:
                    try:
                        # 이미 존재하는 아티클인지 확인
                        existing = crud.get_article_by_url(db, article_data.url)
                        if existing:
                            continue

                        # 아티클 생성
                        crud.create_article(
                            db,
                            title=article_data.title,
                            content=article_data.content,
                            summary="",
                            source_url=article_data.url,
                            source_type="paper",
                            category="",
                            importance_score=0.5,
                            metadata=article_data.metadata,
                        )
                        collected_count += 1

                    except Exception as article_error:
                        logger.error(
                            f"Error saving article '{article_data.title[:50]}': {article_error}",
                        )
                        error_count += 1
                        db.rollback()

            except Exception as e:
                logger.error(f"Error collecting from arXiv for field '{field}': {e}")
                error_count += 1
                db.rollback()

        # 2) 뉴스 소스 수집
        logger.info("\n2. Collecting from News sources...")
        news_collector = NewsCollector()

        for keyword in list(all_keywords)[:5]:  # 레이트 리밋 방지를 위해 5개 제한
            try:
                articles = await async_with_retry(
                    lambda k=keyword: news_collector.collect(query=k, limit=3),
                    max_attempts=3,
                )

                for article_data in articles:
                    try:
                        existing = crud.get_article_by_url(db, article_data.url)
                        if existing:
                            continue

                        crud.create_article(
                            db,
                            title=article_data.title,
                            content=article_data.content,
                            summary="",
                            source_url=article_data.url,
                            source_type="news",
                            category="",
                            importance_score=0.5,
                            metadata=article_data.metadata,
                        )
                        collected_count += 1

                    except Exception as article_error:
                        logger.error(
                            f"Error saving article '{article_data.title[:50]}': {article_error}",
                        )
                        error_count += 1
                        db.rollback()

            except Exception as e:
                logger.error(f"Error collecting news for keyword '{keyword}': {e}")
                error_count += 1
                db.rollback()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Data collection completed!")
        logger.info(f"Total collected: {collected_count} articles")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in data collection task: {e}", exc_info=True)
    finally:
        db.close()


def collect_data_task() -> None:
    """스케줄러용 동기 진입점."""
    asyncio.run(collect_data_task_async())


async def process_articles_task_async() -> None:
    """
    수집된 아티클을 처리하는 스케줄 작업.

    처리 단계:
    1. 요약 생성(한국어)
    2. 중요도 점수 평가
    3. 아티클 분류
    4. 임베딩 생성
    5. 벡터 DB 저장

    매일 01:30 KST 실행
    """
    logger.info("=" * 60)
    logger.info("Starting article processing task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    processed_count = 0
    error_count = 0

    try:
        # 최근 24시간 내 수집된 미처리 아티클 조회
        articles = crud.list_articles(db, limit=100)

        # 미처리 아티클 필터(요약/중요도 없음)
        unprocessed = [a for a in articles if not a.summary or a.importance_score is None]

        logger.info(f"Found {len(unprocessed)} unprocessed articles")

        if not unprocessed:
            logger.info("No articles to process")
            return

        for article in unprocessed:
            try:
                # 1) 요약 생성(없는 경우)
                if not article.summary:
                    summary = await async_with_retry(
                        lambda a=article: summarize_article(
                            title=a.title,
                            content=a.content or "",
                        ),
                        max_attempts=3,
                    )
                    article.summary = summary

                # 2) 중요도 평가(없는 경우)
                if article.importance_score is None:
                    score = await async_with_retry(
                        lambda a=article: evaluate_importance(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.importance_score = score

                # 3) 카테고리 분류(없는 경우)
                if not article.category:
                    category = await async_with_retry(
                        lambda a=article: classify_article_type(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.category = category

                # 4) 임베딩 생성 및 벡터 DB 저장
                if not article.vector_id:
                    try:
                        from app.vector_db.operations import VectorOperations

                        # Qdrant 저장(임베딩은 내부에서 생성)
                        vector_ops = VectorOperations()
                        vector_id = await vector_ops.insert_article(
                            article_id=str(article.id),
                            title=article.title,
                            content=article.content or "",
                            summary=article.summary or "",
                            source_type=article.source_type,
                            category=article.category or "general",
                            importance_score=article.importance_score or 0.5,
                            metadata=article.article_metadata or {},
                        )

                        article.vector_id = vector_id
                        logger.info(f"Stored article in Qdrant with vector_id={vector_id}")

                    except Exception as e:
                        logger.warning(f"Embedding generation or Qdrant storage failed: {e}")
                        # 전체 처리는 중단하지 않고 로그만 남김

                # 변경사항 저장
                crud.update_article(
                    db,
                    article.id,
                    summary=article.summary,
                    importance_score=article.importance_score,
                    category=article.category,
                    vector_id=article.vector_id,
                )

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing article '{article.title[:50]}': {e}")
                error_count += 1
                # 오류 복구를 위해 트랜잭션 롤백
                db.rollback()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Article processing completed!")
        logger.info(f"Total processed: {processed_count} articles")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in article processing task: {e}", exc_info=True)
    finally:
        db.close()


def process_articles_task() -> None:
    """스케줄러용 동기 진입점."""
    asyncio.run(process_articles_task_async())


async def send_digest_task_async() -> None:
    """
    사용자에게 이메일 다이제스트를 발송하는 스케줄 작업.

    사용자별 처리:
    1. 중요도/선호도 기반 상위 N개 선택
    2. HTML 다이제스트 생성
    3. 이메일 발송
    4. sent_digests 테이블에 기록

    매일 08:00 KST 실행(사용자별 설정 가능)
    """
    logger.info("=" * 60)
    logger.info("Starting email digest task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    sent_count = 0
    error_count = 0

    try:
        # 이메일 수신 활성 사용자 조회
        users = crud.list_users(db)
        logger.info(f"Found {len(users)} users")

        # 최근 24시간 아티클 조회(효율을 위해 1회 조회)
        since = datetime.now(UTC) - timedelta(days=1)
        all_articles = crud.get_articles_since(db, since=since)

        # 처리 완료 아티클만 필터링
        processed_articles = [
            a
            for a in all_articles
            if (
                # 요약 또는 카테고리가 있어야 함(LLM 생성)
                (a.summary and a.summary.strip()) or (a.category and a.category.strip())
            )
            and (
                # 중요도 점수가 있어야 함(>= 0.1)
                a.importance_score is not None and a.importance_score >= 0.1
            )
        ]

        logger.info(
            f"Found {len(all_articles)} articles from last 24 hours, "
            f"{len(processed_articles)} are fully processed",
        )

        # 처리 완료 아티클만 사용
        all_articles = processed_articles

        if not all_articles:
            logger.warning(
                "No processed articles available for digest. "
                "This may happen if collection ran but processing hasn't completed yet. "
                "Skipping digest sending for now.",
            )
            return

        for user in users:
            try:
                # 사용자 선호도 조회
                pref = crud.get_user_preference(db, user.id)
                if not pref or not pref.email_enabled:
                    continue

                # 오늘 이미 발송했는지 확인(중복 방지)
                if crud.has_digest_sent_today(db, user.id):
                    logger.info(
                        f"⏭️  Digest already sent to {user.email} today, skipping",
                    )
                    continue

                # 최근 7일 내 발송한 아티클 제외
                sent_article_ids = crud.get_user_sent_article_ids(db, user.id, days=7)
                unsent_articles = [a for a in all_articles if str(a.id) not in sent_article_ids]

                logger.info(
                    f"Filtered articles for {user.email}: "
                    f"{len(all_articles)} total → {len(unsent_articles)} unsent "
                    f"(excluded {len(sent_article_ids)} already sent in last 7 days)",
                )

                # 사용자 선호도 기반 개인화 선택
                personalized_articles = await select_articles_for_user_async(
                    articles=unsent_articles,
                    preferences=pref,
                    limit=pref.daily_limit,
                )

                if not personalized_articles:
                    logger.info(
                        f"No new articles for {user.email} "
                        f"(all recent articles already sent or no matches)",
                    )
                    continue

                logger.info(
                    f"Selected {len(personalized_articles)} articles for "
                    f"{user.email} (keywords: {pref.keywords}, "
                    f"fields: {pref.research_fields})",
                )

                # 다이제스트 생성 및 발송
                try:
                    # 이메일 콘텐츠 생성
                    builder = EmailBuilder()
                    html_content = builder.build_daily_digest(
                        user_name=user.name or user.email.split("@")[0],
                        user_email=user.email,
                        articles=personalized_articles,
                        daily_limit=pref.daily_limit,
                    )

                    # 제목 생성
                    date_str = datetime.now().strftime("%Y년 %m월 %d일")
                    subject = f"🔬 Research Curator - {date_str} AI 연구 동향"

                    # 이메일 발송
                    sender = EmailSender()
                    await sender.send_email(
                        to_email=user.email,
                        subject=subject,
                        html_content=html_content,
                    )

                    # DB에 기록
                    crud.create_digest(
                        db=db,
                        user_id=user.id,
                        article_ids=[str(a.id) for a in personalized_articles],
                    )
                    sent_count += 1

                except Exception as email_error:
                    logger.error(f"Failed to send email to {user.email}: {email_error}")
                    error_count += 1
                    db.rollback()

            except Exception as e:
                logger.error(f"Error sending digest to {user.email}: {e}")
                error_count += 1
                db.rollback()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Email digest task completed!")
        logger.info(f"Emails sent: {sent_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in email digest task: {e}", exc_info=True)
    finally:
        db.close()


def send_digest_task() -> None:
    """스케줄러용 동기 진입점."""
    asyncio.run(send_digest_task_async())


async def unified_collect_and_send_task_async(*, send_email: bool = True) -> None:
    """
    통합 작업: 수집/매칭/처리/다이제스트 발송.

    수집-처리-발송을 하나의 효율적인 작업으로 통합:
    1. 모든 소스에서 아티클 수집(메모리만, DB 저장 없음)
    2. 사용자 선호도 기반 매칭
    3. 사용자별 상위 N개 선택
    4. LLM 처리(요약, 점수, 카테고리, 임베딩)
    5. DB + 벡터 DB 저장
    6. 이메일 발송

    매일 06:00 KST 실행
    """
    logger.info("=" * 60)
    logger.info("Starting unified collect-and-send task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    collected_count = 0
    processed_count = 0
    sent_count = 0
    error_count = 0

    try:
        # 1단계: 사용자 목록 조회
        users = crud.list_users(db)
        logger.info(f"Found {len(users)} users")

        if not users:
            logger.warning("No users found, skipping task")
            return

        # 사용자 연구 분야/키워드 집계
        all_fields = set()
        all_keywords = set()

        for user in users:
            pref = crud.get_user_preference(db, user.id)
            if pref:
                all_fields.update(pref.research_fields)
                all_keywords.update(pref.keywords)

        logger.info(
            f"Collecting for {len(all_fields)} fields and {len(all_keywords)} keywords",
        )

        # 2단계: 아티클 수집(메모리만, DB 미저장)
        raw_articles = []

        # 2a) arXiv 수집
        logger.info("\n📚 Collecting from arXiv...")
        arxiv_collector = ArxivCollector()

        for field in all_fields:
            try:
                articles = await async_with_retry(
                    lambda f=field: arxiv_collector.collect(query=f, limit=5),
                    max_attempts=3,
                )
                raw_articles.extend(articles)
                collected_count += len(articles)
            except Exception as e:
                logger.error(f"Error collecting from arXiv for field '{field}': {e}")
                error_count += 1

        # 2b) 뉴스 소스 수집
        logger.info("\n📰 Collecting from News sources...")
        news_collector = NewsCollector()

        for keyword in list(all_keywords)[:5]:  # 키워드 5개 제한
            try:
                articles = await async_with_retry(
                    lambda k=keyword: news_collector.collect(query=k, limit=3),
                    max_attempts=3,
                )
                raw_articles.extend(articles)
                collected_count += len(articles)
            except Exception as e:
                logger.error(f"Error collecting news for keyword '{keyword}': {e}")
                error_count += 1

        logger.info(f"\n✅ Collected {collected_count} articles (in-memory)")

        # URL 기준 중복 제거
        unique_articles = {}
        for article in raw_articles:
            if article.url not in unique_articles:
                unique_articles[article.url] = article

        raw_articles = list(unique_articles.values())
        logger.info(f"After deduplication: {len(raw_articles)} unique articles")

        # 3단계: 사용자 매칭 및 상위 N개 선택
        user_article_map = {}  # {user_id: [selected_articles]}

        for user in users:
            pref = crud.get_user_preference(db, user.id)
            if not pref or not pref.email_enabled:
                continue

            # 단순 키워드 매칭으로 아티클 선택
            selected = _match_articles_to_user(raw_articles, pref)

            if selected:
                user_article_map[user.id] = selected
                logger.info(
                    f"User {user.email}: selected {len(selected)} articles "
                    f"from {len(raw_articles)} collected",
                )

        # 4단계: 처리 대상 아티클 유니크 목록 구성
        seen_urls = set()
        articles_to_process = []

        for selected_articles in user_article_map.values():
            for article in selected_articles:
                if article.url not in seen_urls:
                    seen_urls.add(article.url)
                    articles_to_process.append(article)
        logger.info(
            f"\n🔄 Processing {len(articles_to_process)} unique articles (selected across all users)",
        )

        # 5단계: LLM으로 선택 아티클 처리
        processed_articles = {}  # {url: processed_db_article}

        for article_data in articles_to_process:
            try:
                # DB에 이미 존재하는지 확인
                existing = crud.get_article_by_url(db, article_data.url)
                if existing:
                    logger.info(f"Article already exists: {article_data.title[:50]}...")
                    processed_articles[article_data.url] = existing
                    continue

                # LLM 처리: 요약
                summary = await async_with_retry(
                    lambda data=article_data: summarize_article(
                        title=data.title,
                        content=data.content or "",
                    ),
                    max_attempts=3,
                )

                # LLM 처리: 중요도 점수
                importance_score = await async_with_retry(
                    lambda data=article_data, s=summary: evaluate_importance(
                        title=data.title,
                        content=data.content or s,
                    ),
                    max_attempts=3,
                )

                # LLM 처리: 카테고리
                category = await async_with_retry(
                    lambda data=article_data, s=summary: classify_article_type(
                        title=data.title,
                        content=data.content or s,
                    ),
                    max_attempts=3,
                )

                # DB 저장
                db_article = crud.create_article(
                    db,
                    title=article_data.title,
                    content=article_data.content,
                    summary=summary,
                    source_url=article_data.url,
                    source_type=article_data.metadata.get("source_type", "news"),
                    category=category,
                    importance_score=importance_score,
                    metadata=article_data.metadata,
                )

                # 임베딩 생성 및 벡터 DB 저장
                try:
                    from app.vector_db.operations import VectorOperations

                    vector_ops = VectorOperations()
                    vector_id = await vector_ops.insert_article(
                        article_id=str(db_article.id),
                        title=db_article.title,
                        content=db_article.content or "",
                        summary=db_article.summary or "",
                        source_type=db_article.source_type,
                        category=db_article.category or "general",
                        importance_score=db_article.importance_score or 0.5,
                        metadata=db_article.article_metadata or {},
                    )

                    crud.update_article(db, db_article.id, vector_id=vector_id)
                    logger.info(
                        f"✅ Processed & saved: {article_data.title[:50]}... "
                        f"(score={importance_score:.2f})",
                    )

                except Exception as e:
                    logger.warning(f"Vector DB storage failed: {e}")

                processed_articles[article_data.url] = db_article
                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing article '{article_data.title[:50]}': {e}")
                error_count += 1
                # 오류 복구를 위해 트랜잭션 롤백
                db.rollback()

        # 6단계: 이메일 발송
        if not send_email:
            logger.info("\n⏭️  Skipping email sending (send_email=False)")
        else:
            logger.info(f"\n📧 Sending digests to {len(user_article_map)} users...")

            for user in users:
                if user.id not in user_article_map:
                    continue

                try:
                    pref = crud.get_user_preference(db, user.id)
                    if not pref or not pref.email_enabled:
                        continue

                    # 오늘 이미 발송했는지 확인(중복 방지)
                    if crud.has_digest_sent_today(db, user.id):
                        logger.info(
                            f"⏭️  Digest already sent to {user.email} today, skipping",
                        )
                        continue

                    # 사용자별 처리 완료 아티클 조회
                    user_articles_data = user_article_map[user.id]
                    user_db_articles = [processed_articles.get(a.url) for a in user_articles_data]
                    user_db_articles = [a for a in user_db_articles if a is not None]

                    # 최근 7일 내 발송한 아티클 제외
                    sent_article_ids = crud.get_user_sent_article_ids(db, user.id, days=7)
                    user_db_articles = [
                        a for a in user_db_articles if str(a.id) not in sent_article_ids
                    ]

                    logger.info(
                        f"Filtered articles for {user.email}: "
                        f"excluded {len(sent_article_ids)} already sent in last 7 days, "
                        f"{len(user_db_articles)} remaining",
                    )

                    if not user_db_articles:
                        logger.info(
                            f"No new articles for {user.email} "
                            f"(all articles already sent or processing failed)",
                        )
                        continue

                    # 중요도 기준 정렬 및 제한
                    user_db_articles = sorted(
                        user_db_articles,
                        key=lambda x: x.importance_score or 0.0,
                        reverse=True,
                    )
                    user_db_articles = user_db_articles[: pref.daily_limit]

                    # 이메일 생성 및 발송
                    builder = EmailBuilder()
                    html_content = builder.build_daily_digest(
                        user_name=user.name or user.email.split("@")[0],
                        user_email=user.email,
                        articles=user_db_articles,
                        daily_limit=pref.daily_limit,
                    )

                    date_str = datetime.now().strftime("%Y년 %m월 %d일")
                    subject = f"🔬 Research Curator - {date_str} AI 연구 동향"

                    sender = EmailSender()
                    await sender.send_email(
                        to_email=user.email,
                        subject=subject,
                        html_content=html_content,
                    )

                    # DB에 기록
                    crud.create_digest(
                        db=db,
                        user_id=user.id,
                        article_ids=[str(a.id) for a in user_db_articles],
                    )

                    logger.info(
                        f"✅ Sent {len(user_db_articles)} articles to {user.email}",
                    )
                    sent_count += 1

                except Exception as e:
                    logger.error(f"Error sending digest to {user.email}: {e}")
                    error_count += 1
                    db.rollback()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Unified task completed!")
        logger.info(f"Collected: {collected_count} articles")
        logger.info(f"Processed: {processed_count} articles (LLM + DB)")
        logger.info(f"Emails sent: {sent_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in unified task: {e}", exc_info=True)
    finally:
        db.close()


def unified_collect_and_send_task() -> None:
    """스케줄러용 동기 진입점."""
    asyncio.run(unified_collect_and_send_task_async())


def _match_articles_to_user(
    raw_articles: list[CollectedData],
    preferences: UserPreference,
) -> list[CollectedData]:
    """
    단순 키워드 매칭으로 사용자 선호도에 맞는 아티클을 찾는다.

    Args:
        raw_articles: CollectedArticleData 목록
        preferences: UserPreference 객체

    Returns:
        매칭된 아티클 목록(사용자 daily_limit * 2 제한)
    """
    keywords = preferences.keywords or []
    research_fields = preferences.research_fields or []

    if not keywords and not research_fields:
        # 기본적으로 상위 아티클 반환
        return raw_articles[: preferences.daily_limit * 2]

    matched = []

    for article in raw_articles:
        # 검색 대상 텍스트 결합
        searchable_text = f"{article.title} {article.content or ''}"
        searchable_text_lower = searchable_text.lower()

        # 키워드 매칭 확인
        matches_keyword = any(kw.lower() in searchable_text_lower for kw in keywords)

        # 연구 분야 매칭 확인
        matches_field = any(field.lower() in searchable_text_lower for field in research_fields)

        if matches_keyword or matches_field:
            matched.append(article)

    # 다양성을 위해 2배까지 반환
    limit = preferences.daily_limit * 2
    return matched[:limit]
