"""Retry logic and error handling utilities."""

import asyncio
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        async def fetch_data():
            # Your code here
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


def with_retry(
    func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Execute a function with retry logic.

    Args:
        func: Function to execute
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result from the function

    Raises:
        Last exception if all attempts fail
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
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. " f"Retrying in {delay:.2f}s...",
            )

            time.sleep(delay)
            delay = min(delay * backoff_factor, 60.0)

    if last_exception:
        raise last_exception

    # This should never be reached, but for type safety
    raise RuntimeError("with_retry completed without returning or raising")


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: float):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []

    async def acquire(self):
        """Wait until a call slot is available."""
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
