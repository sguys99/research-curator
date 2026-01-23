"""LiteLLM 기반 LLM 클라이언트 래퍼."""

import json
import warnings
from functools import lru_cache
from typing import Any, Literal

import litellm
from litellm import completion, embedding
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings

# LiteLLM 상세 로그 비활성화
litellm.suppress_debug_info = True

_RETRYABLE_LLM_ERROR_NAMES = {
    "APIConnectionError",
    "APIError",
    "BadGatewayError",
    "InternalServerError",
    "RateLimitError",
    "ServiceUnavailableError",
    "Timeout",
    "TimeoutError",
}


def _is_retryable_llm_error(exc: BaseException) -> bool:
    for candidate in (exc, getattr(exc, "__cause__", None), getattr(exc, "__context__", None)):
        if candidate and candidate.__class__.__name__ in _RETRYABLE_LLM_ERROR_NAMES:
            return True
    return False


class LLMClient:
    """
    여러 제공자(OpenAI, Claude 등)를 지원하는 통합 LLM 클라이언트.

    LiteLLM을 사용해 제공자와 무관하게 OpenAI 호환 인터페이스를 제공한다.
    """

    def __init__(
        self,
        provider: Literal["openai", "claude"] = "openai",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        LLM 클라이언트를 초기화한다.

        Args:
            provider: 사용할 제공자(openai 또는 claude)
            model: 모델 이름(None이면 설정 기본값 사용)
            temperature: 샘플링 온도(0.0~1.0)
            max_tokens: 응답 최대 토큰 수
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 제공자별 API 키 설정
        if provider == "openai":
            litellm.openai_key = settings.OPENAI_API_KEY
            self._validate_api_key(settings.OPENAI_API_KEY, "OPENAI_API_KEY")
            self.model = model or settings.OPENAI_MODEL
        elif provider == "claude":
            litellm.anthropic_key = settings.ANTHROPIC_API_KEY
            self._validate_api_key(settings.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY")
            self.model = model or settings.ANTHROPIC_MODEL
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _validate_api_key(self, api_key: str | None, env_var: str) -> None:
        if api_key:
            return

        if settings.ENVIRONMENT == "production":
            raise ValueError(f"{env_var} must be set in production.")

        warnings.warn(
            f"{env_var} is not set; LLM requests will fail in development.",
            RuntimeWarning,
            stacklevel=2,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_llm_error),
        reraise=True,
    )
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",  # 응답 형식
        stream: bool = False,  # 스트리밍 모드
        **kwargs: Any,
    ) -> str | Any:
        """
        설정된 LLM으로 채팅 완료 응답을 생성한다.

        Args:
            messages: role/content를 포함한 메시지 목록
            temperature: 기본 temperature 재정의
            max_tokens: 기본 max_tokens 재정의
            response_format: 응답 형식(text 또는 json)
            stream: 스트리밍 모드 사용(전체 대신 청크 반환)
            **kwargs: LiteLLM에 전달할 추가 파라미터

        Returns:
            생성된 텍스트 응답(str) 또는 stream=True인 경우 제너레이터

        예시:
            >>> client = LLMClient(provider="openai")
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "Summarize this article."}
            ... ]
            >>> response = client.chat_completion(messages)
            >>> # 스트리밍 모드
            >>> for chunk in client.chat_completion(messages, stream=True):
            ...     print(chunk, end="", flush=True)
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        # 요청 파라미터 구성
        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok,
            "stream": stream,
            **kwargs,
        }

        # JSON 모드 응답 형식 추가
        # openai만 json 모드를 지원한다. claude는 프롬프트로 JSON을 유도해야 함
        if response_format == "json":
            if self.provider == "openai":
                completion_params["response_format"] = {"type": "json_object"}
            # Claude는 네이티브 JSON 모드가 없어 프롬프트로 유도해야 함

        try:
            response = completion(**completion_params)  # litellm 함수임

            # stream=True면 generator를 그대로 반환 (사용자가 직접 처리)
            if stream:
                return response

            # stream=False면 일반 텍스트 응답 반환
            content = response.choices[0].message.content

            # JSON 응답 검증 및 복구
            if response_format == "json":
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    # JSON이 아니면 응답에서 JSON 추출 시도
                    import re

                    # 정규식으로 JSON 추출 시도
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)

            return content

        except Exception as e:
            if _is_retryable_llm_error(e):
                raise
            raise RuntimeError(f"LLM completion failed: {e}") from e

    # json형식 사용 예시
    # # OpenAI로 일반 텍스트 요약
    # client = LLMClient(provider="openai")
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Summarize this article about AI..."}
    # ]
    # summary = client.chat_completion(messages)

    # # JSON 형식으로 분류 결과 받기
    # messages = [
    #     {"role": "system", "content": "Classify articles and return JSON"},
    #     {"role": "user", "content": "Classify: 'GPT-4 paper released'"}
    # ]
    # result = client.chat_completion(
    #     messages,
    #     response_format="json",
    #     temperature=0.0  # 결정적인 응답
    # )
    # # result: '{"category": "paper", "confidence": 0.95}'

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_llm_error),
        reraise=True,
    )
    def generate_embedding(self, text: str, model: str | None = None) -> list[float]:
        """
        주어진 텍스트의 임베딩 벡터를 생성한다.

        Args:
            text: 임베딩할 입력 텍스트
            model: 임베딩 모델 이름(None이면 기본값 사용)

        Returns:
            float 리스트 형태의 임베딩 벡터

        예시:
            >>> client = LLMClient()
            >>> vec = client.generate_embedding("AI research trends")
            >>> len(vec)
            1536
        """
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = embedding(model=embedding_model, input=text)
            return response.data[0]["embedding"]
        # response 답변 구조가 다음과 같기 때문이다.
        # response = {
        #     "data": [
        #         {
        #             "embedding": [0.123, -0.456, 0.789, ...],  # 1536개의 float
        #             "index": 0
        #         }
        #     ],
        #     "model": "text-embedding-3-small",
        #     "usage": {"prompt_tokens": 10, "total_tokens": 10}
        # }

        except Exception as e:
            if _is_retryable_llm_error(e):
                raise
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_llm_error),
        reraise=True,
    )
    async def achat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",
        stream: bool = False,  # 스트리밍 모드
        **kwargs: Any,
    ) -> str | Any:
        """
        chat_completion의 비동기 버전.

        Args:
            messages: role/content를 포함한 메시지 목록
            temperature: 기본 temperature 재정의
            max_tokens: 기본 max_tokens 재정의
            response_format: 응답 형식(text 또는 json)
            stream: 스트리밍 모드 사용(전체 대신 청크 반환)
            **kwargs: LiteLLM에 전달할 추가 파라미터

        Returns:
            생성된 텍스트 응답(str) 또는 stream=True인 경우 비동기 제너레이터

        예시:
            >>> # 스트리밍 모드
            >>> async for chunk in client.achat_completion(messages, stream=True):
            ...     print(chunk, end="", flush=True)
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok,
            "stream": stream,
            **kwargs,
        }

        if response_format == "json" and self.provider == "openai":
            completion_params["response_format"] = {"type": "json_object"}

        try:
            response = await litellm.acompletion(**completion_params)

            # stream=True면 async generator를 그대로 반환 (사용자가 직접 처리)
            if stream:
                return response

            # stream=False면 일반 텍스트 응답 반환
            content = response.choices[0].message.content

            if response_format == "json":
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)

            return content

        except Exception as e:
            if _is_retryable_llm_error(e):
                raise
            raise RuntimeError(f"Async LLM completion failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_llm_error),
        reraise=True,
    )
    async def agenerate_embedding(self, text: str, model: str | None = None) -> list[float]:
        """
        generate_embedding의 비동기 버전.

        Args:
            text: 임베딩할 입력 텍스트
            model: 임베딩 모델 이름(None이면 기본값 사용)

        Returns:
            float 리스트 형태의 임베딩 벡터
        """
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = await litellm.aembedding(model=embedding_model, input=text)
            return response.data[0]["embedding"]

        except Exception as e:
            if _is_retryable_llm_error(e):
                raise
            raise RuntimeError(f"Async embedding generation failed: {e}") from e


# @lru_cache 데코레이터를 사용하기 위해 함수로 만듬, 인스턴스 재사용
@lru_cache
def get_llm_client(
    provider: Literal["openai", "claude"] = "openai",
    model: str | None = None,
) -> LLMClient:
    """
    캐시된 LLM 클라이언트 인스턴스를 반환한다.

    Args:
        provider: 사용할 LLM 제공자
        model: 모델 이름(선택)

    Returns:
        캐시된 LLMClient 인스턴스
    """
    return LLMClient(provider=provider, model=model)


# @lru_cache 데코레이터 활용
# 핵심 목적: 인스턴스 재사용
# # 첫 번째 호출: 새 인스턴스 생성
# client1 = get_llm_client(provider="openai")  # LLMClient 객체 생성

# # 두 번째 호출: 캐시된 인스턴스 반환 (같은 객체!)
# client2 = get_llm_client(provider="openai")  # 새로 생성 안함, 캐시 반환

# # 동일한 객체인지 확인
# print(client1 is client2)  # True ✅
# 만약 함수 없이 직접 생성한다면:
# # 매번 새 인스턴스 생성 (비효율적)
# client1 = LLMClient(provider="openai")
# client2 = LLMClient(provider="openai")
# print(client1 is client2)  # False ❌
