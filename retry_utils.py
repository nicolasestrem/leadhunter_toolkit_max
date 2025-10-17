"""
Retry utilities with exponential backoff for API calls
"""
import time
import asyncio
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """A decorator for synchronous functions that adds exponential backoff retry logic.

    Args:
        max_retries (int): The maximum number of retry attempts.
        initial_delay (float): The initial delay in seconds.
        backoff_factor (float): The multiplier for the delay after each retry.
        max_delay (float): The maximum delay between retries.
        exceptions (tuple): A tuple of exceptions to catch and retry on.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # Should never reach here
            raise RuntimeError("Retry logic error")

        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """A decorator for asynchronous functions that adds exponential backoff retry logic.

    Args:
        max_retries (int): The maximum number of retry attempts.
        initial_delay (float): The initial delay in seconds.
        backoff_factor (float): The multiplier for the delay after each retry.
        max_delay (float): The maximum delay between retries.
        exceptions (tuple): A tuple of exceptions to catch and retry on.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # Should never reach here
            raise RuntimeError("Retry logic error")

        return wrapper
    return decorator


class RetryableHTTPError(Exception):
    """An exception for HTTP errors that should be retried."""
    pass


def should_retry_http_error(status_code: Optional[int], error: Exception) -> bool:
    """Determine if an HTTP error is eligible for a retry.

    This function checks if an error is a server-side error (5xx) or a common
    transient network issue, such as a timeout or connection error.

    Args:
        status_code (Optional[int]): The HTTP status code, if available.
        error (Exception): The exception that was raised.

    Returns:
        bool: True if the error should be retried, False otherwise.
    """
    # Retry on server errors (5xx)
    if status_code and status_code >= 500:
        return True

    # Retry on common timeout/connection errors
    error_str = str(error).lower()
    retryable_errors = [
        'timeout',
        'connection',
        'temporary failure',
        'try again',
        'rate limit'
    ]

    return any(err in error_str for err in retryable_errors)
