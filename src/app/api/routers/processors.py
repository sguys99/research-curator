"""
Processors API 엔드포인트

데이터 처리 관련 API:
- 요약 생성 (Summarization)
- 중요도 평가 (Evaluation)
- 카테고리 분류 (Classification)
- 단일/배치 아티클 처리 (Processing Pipeline)
"""

import time

from fastapi import APIRouter, HTTPException

from src.app.api.schemas.processors import (
    BatchProcessRequest,
    BatchProcessResponse,
    ClassifyRequest,
    ClassifyResponse,
    EvaluateRequest,
    EvaluateResponse,
    ProcessArticleRequest,
    ProcessedArticleResponse,
    StatisticsResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from src.app.processors import (
    ArticleSummarizer,
    ContentClassifier,
    ImportanceEvaluator,
    ProcessingPipeline,
)

router = APIRouter(prefix="/processors", tags=["Processors"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_article(request: SummarizeRequest) -> SummarizeResponse:
    """
    아티클 요약 생성

    제목과 내용을 받아 지정된 언어와 길이로 요약을 생성합니다.
    """
    try:
        # Create summarizer
        summarizer = ArticleSummarizer()

        # Generate summary
        summary = await summarizer.summarize(
            title=request.title,
            content=request.content,
            language=request.language,  # type: ignore
            length=request.length,  # type: ignore
        )

        return SummarizeResponse(
            summary=summary,
            language=request.language,
            length=request.length,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"요약 생성 실패: {str(e)}",
        ) from e


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_article(request: EvaluateRequest) -> EvaluateResponse:
    """
    아티클 중요도 평가

    제목, 내용, 메타데이터를 분석하여 중요도 점수를 계산합니다.
    """
    try:
        # Create evaluator
        evaluator = ImportanceEvaluator()

        # Evaluate article
        result = await evaluator.evaluate(
            title=request.title,
            content=request.content,
            metadata=request.metadata or {},
        )

        return EvaluateResponse(
            innovation_score=result["innovation"],
            relevance_score=result["relevance"],
            impact_score=result["impact"],
            timeliness_score=result["timeliness"],
            final_score=result["final_score"],
            llm_score=result["llm_score"],
            metadata_score=result["metadata_score"],
            reasoning=result.get("reasoning"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"중요도 평가 실패: {str(e)}",
        ) from e


@router.post("/classify", response_model=ClassifyResponse)
async def classify_article(request: ClassifyRequest) -> ClassifyResponse:
    """
    아티클 카테고리 분류

    제목과 내용을 분석하여 카테고리, 키워드, 연구 분야를 추출합니다.
    """
    try:
        # Create classifier
        classifier = ContentClassifier()

        # Classify article
        result = await classifier.classify(
            title=request.title,
            content=request.content,
            source_name=request.source_name,
            url=request.url,
        )

        return ClassifyResponse(
            category=result["category"],
            confidence=result.get("confidence", 0.8),
            keywords=result.get("keywords", []),
            research_field=result.get("research_field", "Other"),
            sub_fields=result.get("sub_fields", []),
            reasoning=result.get("reasoning"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 분류 실패: {str(e)}",
        ) from e


@router.post("/process", response_model=ProcessedArticleResponse)
async def process_article(request: ProcessArticleRequest) -> ProcessedArticleResponse:
    """
    단일 아티클 전체 처리

    요약, 평가, 분류, 임베딩을 모두 수행하여 처리된 아티클을 반환합니다.
    """
    try:
        # Create pipeline
        pipeline = ProcessingPipeline(
            summary_language=request.summary_language,
            summary_length=request.summary_length,
        )

        # Process article
        result = await pipeline.process_article(
            title=request.title,
            content=request.content,
            url=request.url,
            source_name=request.source_name,
            source_type=request.source_type,
            metadata=request.metadata,
        )

        return ProcessedArticleResponse(
            # 원본 데이터
            title=result.title,
            content=result.content,
            url=result.url,
            source_name=result.source_name,
            source_type=result.source_type,
            # 처리 결과
            summary=result.summary,
            importance_score=result.importance_score,
            category=result.category,
            keywords=result.keywords,
            research_field=result.research_field,
            embedding=result.embedding,
            # 상세 평가
            innovation_score=result.innovation_score,
            relevance_score=result.relevance_score,
            impact_score=result.impact_score,
            timeliness_score=result.timeliness_score,
            # 메타데이터
            metadata=result.metadata,
            processed_at=result.processed_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"아티클 처리 실패: {str(e)}",
        ) from e


@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process_articles(request: BatchProcessRequest) -> BatchProcessResponse:
    """
    배치 아티클 처리

    여러 아티클을 동시에 처리합니다. max_concurrent로 동시 처리 개수 제한.
    """
    try:
        start_time = time.time()

        # Create pipeline
        pipeline = ProcessingPipeline()

        # Convert requests to dict format
        articles_data = [article.model_dump() for article in request.articles]

        # Process batch
        results = await pipeline.process_batch(
            articles=articles_data,
            max_concurrent=request.max_concurrent,
        )

        # Convert to response format
        processed_responses = [
            ProcessedArticleResponse(
                # 원본 데이터
                title=r.title,
                content=r.content,
                url=r.url,
                source_name=r.source_name,
                source_type=r.source_type,
                # 처리 결과
                summary=r.summary,
                importance_score=r.importance_score,
                category=r.category,
                keywords=r.keywords,
                research_field=r.research_field,
                embedding=r.embedding,
                # 상세 평가
                innovation_score=r.innovation_score,
                relevance_score=r.relevance_score,
                impact_score=r.impact_score,
                timeliness_score=r.timeliness_score,
                # 메타데이터
                metadata=r.metadata,
                processed_at=r.processed_at,
            )
            for r in results
        ]

        processing_time = time.time() - start_time
        total = len(request.articles)
        success = len(results)
        failed = total - success

        return BatchProcessResponse(
            total=total,
            success=success,
            failed=failed,
            results=processed_responses,
            processing_time=processing_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"배치 처리 실패: {str(e)}",
        ) from e


@router.post("/statistics", response_model=StatisticsResponse)
async def get_processing_statistics(
    articles: list[ProcessedArticleResponse],
) -> StatisticsResponse:
    """
    처리된 아티클 통계

    카테고리 분포, 평균 점수 등의 통계를 계산합니다.
    """
    try:
        if not articles:
            return StatisticsResponse(
                total=0,
                category_distribution={},
                average_score=0.0,
                max_score=0.0,
                min_score=0.0,
                high_quality_count=0,
            )

        # Calculate statistics
        category_dist: dict[str, int] = {}
        scores = []

        for article in articles:
            # Category distribution
            cat = article.category
            category_dist[cat] = category_dist.get(cat, 0) + 1

            # Scores
            scores.append(article.importance_score)

        return StatisticsResponse(
            total=len(articles),
            category_distribution=category_dist,
            average_score=sum(scores) / len(scores) if scores else 0.0,
            max_score=max(scores) if scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            high_quality_count=len([s for s in scores if s >= 0.7]),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통계 계산 실패: {str(e)}",
        ) from e
