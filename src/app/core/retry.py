"""재시도 로직과 에러 처리 유틸리티."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


async def async_with_retry[T](
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    비동기 함수를 재시도 로직과 함께 실행한다.

    Args:
        func: 실행할 비동기 함수
        max_attempts: 최대 시도 횟수
        initial_delay: 초기 대기 시간(초)
        backoff_factor: 재시도마다 증가하는 대기 시간 배수
        exceptions: 재시도 대상으로 처리할 예외 튜플

    Returns:
        함수 실행 결과

    Raises:
        모든 시도가 실패하면 마지막 예외 발생
    """
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:
                logger.error(f"Async function failed after {max_attempts} attempts: {e}")
                raise

            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. Retrying in {delay:.2f}s...",
            )

            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, 60.0)

    if last_exception:
        raise last_exception

    raise RuntimeError("async_with_retry가 반환 또는 예외 없이 종료되었습니다.")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """지수 백오프로 함수를 재시도하는 데코레이터.

    Args:
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 대기 시간(초)
        max_delay: 최대 대기 시간(초)
        backoff_factor: 재시도마다 증가하는 대기 시간 배수
        exceptions: 재시도 대상으로 처리할 예외 튜플

    예시:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        async def fetch_data():
            # 로직 작성
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s...",
                    )

                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s...",
                    )

                    import time

                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            if last_exception:
                raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_retry[T](
    func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    함수를 재시도 로직과 함께 실행한다.

    Args:
        func: 실행할 함수
        max_attempts: 최대 시도 횟수
        initial_delay: 초기 대기 시간(초)
        backoff_factor: 재시도마다 증가하는 대기 시간 배수
        exceptions: 재시도 대상으로 처리할 예외 튜플

    Returns:
        함수 실행 결과

    Raises:
        모든 시도가 실패하면 마지막 예외 발생
    """
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:
                logger.error(f"Function failed after {max_attempts} attempts: {e}")
                raise

            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. Retrying in {delay:.2f}s...",
            )

            time.sleep(delay)
            delay = min(delay * backoff_factor, 60.0)

    if last_exception:
        raise last_exception

    # 타입 안정성을 위한 방어 코드(정상 경로에서는 도달하지 않음)
    raise RuntimeError("with_retry가 반환 또는 예외 없이 종료되었습니다.")


class RateLimiter:
    """API 호출을 위한 간단한 레이트 리미터."""

    def __init__(self, max_calls: int, time_window: float) -> None:
        """레이트 리미터를 초기화한다.

        Args:
            max_calls: 허용되는 최대 호출 수
            time_window: 시간 창(초)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []

    async def acquire(self) -> None:
        """호출 슬롯이 열릴 때까지 대기한다."""
        import time

        now = time.time()

        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            sleep_time = self.time_window - (now - oldest_call)

            if sleep_time > 0:
                logger.debug(f"Rate limit reached. Waiting {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)

        self.calls.append(time.time())
