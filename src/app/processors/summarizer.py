"""
아티클 요약 생성기

LLM을 사용하여 논문/뉴스/리포트를 한국어 또는 영어로 요약합니다.
"""

import asyncio
import logging
from typing import Literal

from ..core.prompts import build_messages, get_prompt
from ..llm.client import get_llm_client

logger = logging.getLogger(__name__)

SummaryLength = Literal["short", "medium", "long"]
Language = Literal["ko", "en"]


class ArticleSummarizer:
    """아티클 요약 생성 클래스"""

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        temperature: float = 0.3,
    ):
        """
        Args:
            provider: LLM 프로바이더 ("openai" 또는 "claude")
            model: 사용할 모델 (None이면 기본 모델)
            temperature: 생성 온도 (0.0-1.0, 낮을수록 일관성↑)
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.llm_client = get_llm_client(provider=provider, model=model)

    async def summarize(
        self,
        title: str,
        content: str,
        language: Language = "ko",
        length: SummaryLength = "medium",
        max_tokens: int = 500,
    ) -> str:
        """
        단일 아티클 요약 생성

        Args:
            title: 아티클 제목
            content: 아티클 내용
            language: 요약 언어 ("ko" 또는 "en")
            length: 요약 길이 ("short", "medium", "long")
            max_tokens: 최대 토큰 수

        Returns:
            요약 문자열

        Examples:
            >>> summarizer = ArticleSummarizer()
            >>> summary = await summarizer.summarize(
            ...     title="Attention Is All You Need",
            ...     content="We propose...",
            ...     language="ko",
            ...     length="medium"
            ... )
        """
        try:
            # 프롬프트 빌드
            lang_key = "korean" if language == "ko" else "english"
            subcategory = f"{lang_key}.{length}"

            messages = build_messages("summarize", subcategory, title=title, content=content)

            # LLM 호출
            response = await self.llm_client.achat_completion(
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
            )

            summary = response.strip()
            logger.info(
                f"Summary generated: {len(summary)} chars " f"(lang={language}, length={length})",
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            error_msg = get_prompt("common.error_messages.api_error")
            raise RuntimeError(error_msg) from e

    async def batch_summarize(
        self,
        articles: list[dict],
        language: Language = "ko",
        length: SummaryLength = "medium",
        max_tokens: int = 500,
    ) -> list[str]:
        """
        여러 아티클 동시 요약 (병렬 처리)

        Args:
            articles: 아티클 리스트 [{"title": "...", "content": "..."}, ...]
            language: 요약 언어
            length: 요약 길이
            max_tokens: 최대 토큰 수

        Returns:
            요약 문자열 리스트

        Examples:
            >>> articles = [
            ...     {"title": "Paper 1", "content": "..."},
            ...     {"title": "Paper 2", "content": "..."},
            ... ]
            >>> summaries = await summarizer.batch_summarize(articles)
        """
        try:
            # 병렬 처리
            tasks = [
                self.summarize(
                    title=article["title"],
                    content=article["content"],
                    language=language,
                    length=length,
                    max_tokens=max_tokens,
                )
                for article in articles
            ]

            summaries = await asyncio.gather(*tasks, return_exceptions=True)

            # 에러 처리
            results = []
            for i, summary in enumerate(summaries):
                if isinstance(summary, Exception):
                    logger.error(f"Error summarizing article {i}: {summary}")
                    results.append(f"요약 생성 실패: {str(summary)}")
                else:
                    results.append(summary)

            logger.info(
                f"Batch summarization completed: "
                f"{len(results)} articles, "
                f"{sum(1 for r in results if not r.startswith('요약 생성 실패'))} succeeded",
            )

            return results

        except Exception as e:
            logger.error(f"Error in batch summarization: {e}")
            raise

    def summarize_sync(
        self,
        title: str,
        content: str,
        language: Language = "ko",
        length: SummaryLength = "medium",
        max_tokens: int = 500,
    ) -> str:
        """
        동기 방식 요약 생성 (편의 함수)

        Returns:
            요약 문자열
        """
        return asyncio.run(
            self.summarize(
                title=title,
                content=content,
                language=language,
                length=length,
                max_tokens=max_tokens,
            ),
        )


# 사용 예시
if __name__ == "__main__":
    import sys

    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 샘플 데이터
    sample_article = {
        "title": "Attention Is All You Need",
        "content": """
        We propose a new simple network architecture, the Transformer,
        based solely on attention mechanisms, dispensing with recurrence
        and convolutions entirely. Experiments on two machine translation
        tasks show these models to be superior in quality while being
        more parallelizable and requiring significantly less time to train.
        """,
    }

    async def test():
        # Summarizer 생성
        summarizer = ArticleSummarizer(provider="openai")

        # 단일 요약
        print("=" * 60)
        print("단일 요약 테스트")
        print("=" * 60)

        summary = await summarizer.summarize(
            title=sample_article["title"],
            content=sample_article["content"],
            language="ko",
            length="medium",
        )

        print(f"\n제목: {sample_article['title']}")
        print(f"요약: {summary}")

        # 배치 요약
        print("\n" + "=" * 60)
        print("배치 요약 테스트")
        print("=" * 60)

        articles = [
            {
                "title": "GPT-4 Technical Report",
                "content": "GPT-4 is a large multimodal model...",
            },
            {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "content": "We introduce BERT, which stands for...",
            },
        ]

        summaries = await summarizer.batch_summarize(articles, length="short")

        for i, (article, summary) in enumerate(zip(articles, summaries, strict=False), 1):
            print(f"\n[{i}] {article['title']}")
            print(f"요약: {summary}")

    # 테스트 실행
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n에러 발생: {e}")
        sys.exit(1)
