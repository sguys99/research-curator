"""
아티클 중요도 평가기

LLM과 메타데이터를 결합하여 아티클의 중요도를 0.0~1.0으로 평가합니다.
"""

import asyncio
import json
import logging
from typing import Any

from ..core.prompts import build_messages, get_prompt
from ..llm.client import get_llm_client

logger = logging.getLogger(__name__)


class ImportanceEvaluator:
    """아티클 중요도 평가 클래스"""

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        temperature: float = 0.2,
        llm_weight: float = 0.7,
        metadata_weight: float = 0.3,
    ):
        """
        Args:
            provider: LLM 프로바이더
            model: 사용할 모델
            temperature: 생성 온도 (낮을수록 일관성 높음)
            llm_weight: LLM 평가 가중치 (0.0-1.0)
            metadata_weight: 메타데이터 평가 가중치 (0.0-1.0)
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.llm_weight = llm_weight
        self.metadata_weight = metadata_weight
        self.llm_client = get_llm_client(provider=provider, model=model)

        # 평가 기준 가중치 로드
        self.criteria_weights = get_prompt("evaluate_importance.weights")

    async def evaluate(
        self,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        max_tokens: int = 500,
    ) -> dict[str, float]:
        """
        단일 아티클 중요도 평가

        Args:
            title: 아티클 제목
            content: 아티클 내용
            metadata: 메타데이터 (인용수, 저자, 출처 등)
            max_tokens: 최대 토큰 수

        Returns:
            평가 결과 딕셔너리
            {
                "innovation": 0.0-1.0,
                "relevance": 0.0-1.0,
                "impact": 0.0-1.0,
                "timeliness": 0.0-1.0,
                "reasoning": "평가 근거",
                "llm_score": 0.0-1.0,
                "metadata_score": 0.0-1.0,
                "final_score": 0.0-1.0
            }

        Examples:
            >>> evaluator = ImportanceEvaluator()
            >>> result = await evaluator.evaluate(
            ...     title="GPT-4 Technical Report",
            ...     content="...",
            ...     metadata={"citations": 5000, "year": 2023}
            ... )
            >>> print(result["final_score"])
        """
        try:
            # LLM 평가
            llm_result = await self._evaluate_with_llm(title, content, metadata or {}, max_tokens)

            # 메타데이터 평가
            metadata_score = self._evaluate_with_metadata(metadata or {})

            # 최종 점수 계산
            llm_score = llm_result.get("overall_score", 0.0)
            final_score = self.llm_weight * llm_score + self.metadata_weight * metadata_score

            result = {
                **llm_result,
                "llm_score": llm_score,
                "metadata_score": metadata_score,
                "final_score": min(1.0, max(0.0, final_score)),  # 0-1 범위로 클램핑
            }

            logger.info(
                f"Evaluation completed: final_score={result['final_score']:.2f} "
                f"(llm={llm_score:.2f}, metadata={metadata_score:.2f})",
            )

            return result

        except Exception as e:
            logger.error(f"Error evaluating importance: {e}")
            error_msg = get_prompt("common.error_messages.api_error")
            raise RuntimeError(error_msg) from e

    async def _evaluate_with_llm(
        self,
        title: str,
        content: str,
        metadata: dict[str, Any],
        max_tokens: int,
    ) -> dict[str, float]:
        """LLM을 사용한 평가"""
        try:
            # 프롬프트 빌드
            messages = build_messages(
                "evaluate_importance",
                title=title,
                content=content,
                metadata=json.dumps(metadata, ensure_ascii=False, indent=2),
            )

            # LLM 호출 (JSON 모드)
            response = await self.llm_client.achat_completion(
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                response_format="json",
            )

            # JSON 파싱
            result = json.loads(response)

            # 필수 필드 검증
            required_fields = ["innovation", "relevance", "impact", "timeliness"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing field in LLM response: {field}")
                    result[field] = 0.5  # 기본값

            # overall_score 계산 (가중 평균)
            if "overall_score" not in result:
                result["overall_score"] = sum(
                    result.get(criterion, 0.0) * weight
                    for criterion, weight in self.criteria_weights.items()
                )

            # 값 범위 보정 (0-1)
            for key in ["innovation", "relevance", "impact", "timeliness", "overall_score"]:
                if key in result:
                    result[key] = min(1.0, max(0.0, float(result[key])))

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Response: {response[:200]}...")
            # 기본 점수 반환
            return {
                "innovation": 0.5,
                "relevance": 0.5,
                "impact": 0.5,
                "timeliness": 0.5,
                "reasoning": "JSON 파싱 실패",
                "overall_score": 0.5,
            }

    def _evaluate_with_metadata(self, metadata: dict[str, Any]) -> float:
        """
        메타데이터 기반 평가

        고려 사항:
        - 인용수 (citations)
        - 출처 신뢰도 (source)
        - 최신성 (publication_date, year)
        - 저자 명성 (authors - 추후 확장)
        """
        score = 0.5  # 기본 점수

        # 1. 인용수 평가 (0.0-0.3 점수)
        citations = metadata.get("citations", 0)
        if citations > 10000:
            score += 0.3
        elif citations > 1000:
            score += 0.2
        elif citations > 100:
            score += 0.1

        # 2. 출처 신뢰도 (0.0-0.2 점수)
        source = metadata.get("source_name", "").lower()
        trusted_sources = [
            "arxiv",
            "nature",
            "science",
            "acl",
            "neurips",
            "icml",
            "iclr",
            "cvpr",
            "openai",
            "google",
            "deepmind",
        ]
        if any(trusted in source for trusted in trusted_sources):
            score += 0.2
        elif any(domain in source for domain in ["techcrunch", "venturebeat", "mit technology review"]):
            score += 0.1

        # 3. 최신성 평가 (0.0-0.2 점수)
        year = metadata.get("year")
        if year:
            from datetime import datetime

            current_year = datetime.now().year
            age = current_year - year
            if age == 0:
                score += 0.2  # 올해
            elif age == 1:
                score += 0.15  # 작년
            elif age <= 2:
                score += 0.1  # 2년 이내
            elif age <= 5:
                score += 0.05  # 5년 이내

        return min(1.0, max(0.0, score))

    async def batch_evaluate(
        self,
        articles: list[dict[str, Any]],
        max_tokens: int = 500,
    ) -> list[dict[str, float]]:
        """
        여러 아티클 동시 평가 (병렬 처리)

        Args:
            articles: 아티클 리스트
                [{"title": "...", "content": "...", "metadata": {...}}, ...]
            max_tokens: 최대 토큰 수

        Returns:
            평가 결과 리스트

        Examples:
            >>> articles = [
            ...     {"title": "Paper 1", "content": "...", "metadata": {...}},
            ...     {"title": "Paper 2", "content": "...", "metadata": {...}},
            ... ]
            >>> results = await evaluator.batch_evaluate(articles)
        """
        try:
            # 병렬 처리
            tasks = [
                self.evaluate(
                    title=article["title"],
                    content=article["content"],
                    metadata=article.get("metadata"),
                    max_tokens=max_tokens,
                )
                for article in articles
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 에러 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error evaluating article {i}: {result}")
                    # 기본 점수 반환
                    processed_results.append(
                        {
                            "innovation": 0.5,
                            "relevance": 0.5,
                            "impact": 0.5,
                            "timeliness": 0.5,
                            "reasoning": f"평가 실패: {str(result)}",
                            "llm_score": 0.5,
                            "metadata_score": 0.5,
                            "final_score": 0.5,
                        },
                    )
                else:
                    processed_results.append(result)

            logger.info(
                f"Batch evaluation completed: "
                f"{len(processed_results)} articles, "
                f"{sum(1 for r in results if not isinstance(r, Exception))} succeeded",
            )

            return processed_results

        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            raise


# 사용 예시
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    sample_article = {
        "title": "Attention Is All You Need",
        "content": """
        We propose a new simple network architecture, the Transformer,
        based solely on attention mechanisms, dispensing with recurrence
        and convolutions entirely.
        """,
        "metadata": {"citations": 50000, "year": 2017, "source_name": "arXiv"},
    }

    async def test():
        evaluator = ImportanceEvaluator(provider="openai")

        print("=" * 60)
        print("단일 평가 테스트")
        print("=" * 60)

        result = await evaluator.evaluate(
            title=sample_article["title"],
            content=sample_article["content"],
            metadata=sample_article["metadata"],
        )

        print(f"\n제목: {sample_article['title']}")
        print(f"최종 점수: {result['final_score']:.2f}")
        print(f"  - LLM 점수: {result['llm_score']:.2f}")
        print(f"  - 메타데이터 점수: {result['metadata_score']:.2f}")
        print("\n세부 평가:")
        print(f"  - 혁신성: {result['innovation']:.2f}")
        print(f"  - 관련성: {result['relevance']:.2f}")
        print(f"  - 영향력: {result['impact']:.2f}")
        print(f"  - 시의성: {result['timeliness']:.2f}")
        if "reasoning" in result:
            print(f"\n평가 근거: {result['reasoning']}")

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n에러 발생: {e}")
        sys.exit(1)
