"""
콘텐츠 카테고리 분류기

LLM을 사용하여 아티클을 카테고리별로 분류하고 메타데이터를 추출합니다.
"""

import asyncio
import json
import logging
from typing import Any

from ..core.prompts import build_messages, get_prompt
from ..llm.client import get_llm_client

logger = logging.getLogger(__name__)


class ContentClassifier:
    """콘텐츠 카테고리 분류 클래스"""

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        temperature: float = 0.1,
    ):
        """
        Args:
            provider: LLM 프로바이더
            model: 사용할 모델
            temperature: 생성 온도 (매우 낮게 설정하여 일관성 극대화)
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.llm_client = get_llm_client(provider=provider, model=model)

        # 허용된 카테고리 목록
        self.valid_categories = get_prompt("classify_category.categories")
        self.research_fields = get_prompt("classify_category.research_fields")

    async def classify(
        self,
        title: str,
        content: str,
        source_name: str = "",
        url: str = "",
        max_tokens: int = 500,
    ) -> dict[str, Any]:
        """
        단일 아티클 분류 및 메타데이터 추출

        Args:
            title: 아티클 제목
            content: 아티클 내용
            source_name: 소스 이름 (예: "arXiv", "TechCrunch")
            url: 원문 URL
            max_tokens: 최대 토큰 수

        Returns:
            분류 결과 딕셔너리
            {
                "category": "paper|news|report|blog|other",
                "confidence": 0.0-1.0,
                "keywords": ["keyword1", "keyword2", ...],
                "research_field": "주요 연구 분야",
                "sub_fields": ["세부 분야1", "세부 분야2"],
                "reasoning": "분류 근거"
            }

        Examples:
            >>> classifier = ContentClassifier()
            >>> result = await classifier.classify(
            ...     title="Attention Is All You Need",
            ...     content="We propose the Transformer...",
            ...     source_name="arXiv",
            ...     url="https://arxiv.org/abs/1706.03762"
            ... )
            >>> print(result["category"])  # "paper"
        """
        try:
            # 프롬프트 빌드
            messages = build_messages(
                "classify_category",
                title=title,
                content=content,
                source_name=source_name,
                url=url,
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

            # 카테고리 검증 및 보정
            category = result.get("category", "other").lower()
            if category not in self.valid_categories:
                logger.warning(f"Invalid category '{category}', using 'other'")
                result["category"] = "other"
            else:
                result["category"] = category

            # 기본값 설정
            result.setdefault("confidence", 0.8)
            result.setdefault("keywords", [])
            result.setdefault("research_field", "Other")
            result.setdefault("sub_fields", [])
            result.setdefault("reasoning", "")

            # confidence 범위 보정
            result["confidence"] = min(1.0, max(0.0, float(result["confidence"])))

            logger.info(
                f"Classification completed: category={result['category']} "
                f"(confidence={result['confidence']:.2f})",
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Response: {response[:200]}...")
            # 기본 분류 반환
            return self._get_fallback_classification(source_name, url)

        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            error_msg = get_prompt("common.error_messages.api_error")
            raise RuntimeError(error_msg) from e

    def _get_fallback_classification(self, source_name: str, url: str) -> dict[str, Any]:
        """
        LLM 실패 시 휴리스틱 기반 분류

        소스 이름과 URL을 기반으로 간단히 분류
        """
        source_lower = source_name.lower()
        url_lower = url.lower()

        # 논문 판별
        if any(
            keyword in source_lower or keyword in url_lower
            for keyword in ["arxiv", "acl", "neurips", "icml", "cvpr", "ieee", "acm"]
        ):
            return {
                "category": "paper",
                "confidence": 0.7,
                "keywords": [],
                "research_field": "Other",
                "sub_fields": [],
                "reasoning": "Fallback: source-based classification",
            }

        # 뉴스 판별
        if any(
            keyword in source_lower
            for keyword in [
                "techcrunch",
                "venturebeat",
                "verge",
                "wired",
                "zdnet",
                "news",
            ]
        ):
            return {
                "category": "news",
                "confidence": 0.7,
                "keywords": [],
                "research_field": "Other",
                "sub_fields": [],
                "reasoning": "Fallback: source-based classification",
            }

        # 기본값
        return {
            "category": "other",
            "confidence": 0.5,
            "keywords": [],
            "research_field": "Other",
            "sub_fields": [],
            "reasoning": "Fallback: default classification",
        }

    async def batch_classify(
        self,
        articles: list[dict[str, str]],
        max_tokens: int = 500,
    ) -> list[dict[str, Any]]:
        """
        여러 아티클 동시 분류 (병렬 처리)

        Args:
            articles: 아티클 리스트
                [{"title": "...", "content": "...", "source_name": "...", "url": "..."}, ...]
            max_tokens: 최대 토큰 수

        Returns:
            분류 결과 리스트

        Examples:
            >>> articles = [
            ...     {"title": "Paper 1", "content": "...", "source_name": "arXiv", "url": "..."},
            ...     {"title": "News 1", "content": "...", "source_name": "TechCrunch", "url": "..."},
            ... ]
            >>> results = await classifier.batch_classify(articles)
        """
        try:
            # 병렬 처리
            tasks = [
                self.classify(
                    title=article["title"],
                    content=article["content"],
                    source_name=article.get("source_name", ""),
                    url=article.get("url", ""),
                    max_tokens=max_tokens,
                )
                for article in articles
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 에러 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error classifying article {i}: {result}")
                    # Fallback 분류
                    article = articles[i]
                    processed_results.append(
                        self._get_fallback_classification(
                            article.get("source_name", ""),
                            article.get("url", ""),
                        ),
                    )
                else:
                    processed_results.append(result)

            logger.info(
                f"Batch classification completed: "
                f"{len(processed_results)} articles, "
                f"{sum(1 for r in results if not isinstance(r, Exception))} succeeded",
            )

            return processed_results

        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            raise

    def get_category_distribution(self, classifications: list[dict[str, Any]]) -> dict[str, int]:
        """
        분류 결과의 카테고리 분포 계산

        Args:
            classifications: classify() 또는 batch_classify() 결과 리스트

        Returns:
            카테고리별 개수 {"paper": 5, "news": 3, ...}
        """
        distribution = {cat: 0 for cat in self.valid_categories}

        for result in classifications:
            category = result.get("category", "other")
            if category in distribution:
                distribution[category] += 1

        return distribution


# 사용 예시
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    sample_articles = [
        {
            "title": "Attention Is All You Need",
            "content": """
            We propose a new simple network architecture, the Transformer,
            based solely on attention mechanisms.
            """,
            "source_name": "arXiv",
            "url": "https://arxiv.org/abs/1706.03762",
        },
        {
            "title": "OpenAI Announces GPT-4",
            "content": """
            OpenAI today announced GPT-4, the latest milestone in its effort
            to scale up deep learning.
            """,
            "source_name": "TechCrunch",
            "url": "https://techcrunch.com/...",
        },
    ]

    async def test():
        classifier = ContentClassifier(provider="openai")

        print("=" * 60)
        print("단일 분류 테스트")
        print("=" * 60)

        result = await classifier.classify(
            title=sample_articles[0]["title"],
            content=sample_articles[0]["content"],
            source_name=sample_articles[0]["source_name"],
            url=sample_articles[0]["url"],
        )

        print(f"\n제목: {sample_articles[0]['title']}")
        print(f"카테고리: {result['category']} (신뢰도: {result['confidence']:.2f})")
        print(f"연구 분야: {result['research_field']}")
        print(f"키워드: {', '.join(result['keywords'][:5])}")
        if result.get("reasoning"):
            print(f"분류 근거: {result['reasoning']}")

        print("\n" + "=" * 60)
        print("배치 분류 테스트")
        print("=" * 60)

        results = await classifier.batch_classify(sample_articles)

        for i, (article, result) in enumerate(zip(sample_articles, results, strict=False), 1):
            print(f"\n[{i}] {article['title'][:50]}")
            print(f"    카테고리: {result['category']}")
            print(f"    연구 분야: {result['research_field']}")

        # 분포 계산
        distribution = classifier.get_category_distribution(results)
        print("\n" + "=" * 60)
        print("카테고리 분포")
        print("=" * 60)
        for category, count in distribution.items():
            if count > 0:
                print(f"{category}: {count}")

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n에러 발생: {e}")
        sys.exit(1)
