"""Retry logic with exponential backoff for async functions.

This module provides a decorator for implementing retry logic with exponential
backoff and jitter, specifically designed for handling transient errors when
communicating with external services like ComfyUI.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from aiohttp import ClientConnectorError, ClientResponseError, ServerTimeoutError

# Type variable for decorated function return type
T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    max_wait: float = 60.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that retries async functions with exponential backoff.

    Implements exponential backoff with jitter to handle transient errors when
    communicating with external services. Only retries on errors that are likely
    to be transient (connection errors, timeouts, server errors, rate limits).

    The backoff formula uses: wait = min(max_wait, (2 ** attempt) + jitter)
    where jitter is a random value between 0 and 1 second.

    Retryable errors:
        - ClientConnectorError: Connection failed
        - ServerTimeoutError: Request timed out
        - ClientResponseError with status 5xx: Server error
        - ClientResponseError with status 429: Rate limit exceeded

    Non-retryable errors (fail immediately):
        - ClientResponseError with status 4xx (except 429): Client errors
        - All other exceptions

    Args:
        max_attempts: Maximum number of attempts (including initial try).
                     Default: 3
        max_wait: Maximum wait time between retries in seconds.
                 Default: 60.0

    Returns:
        Decorated async function with retry logic

    Example:
        >>> @retry_with_backoff(max_attempts=3, max_wait=30)
        >>> async def fetch_data():
        ...     async with session.get(url) as response:
        ...         response.raise_for_status()
        ...         return await response.json()

        >>> # Will retry on connection errors, timeouts, 5xx, 429
        >>> data = await fetch_data()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0

            while attempt < max_attempts:
                try:
                    # Attempt to execute the function
                    return await func(*args, **kwargs)

                except (
                    ClientConnectorError,
                    ServerTimeoutError,
                ):
                    # Always retry on connection/timeout errors
                    attempt += 1
                    if attempt >= max_attempts:
                        raise  # Re-raise if max attempts exhausted

                    # Calculate exponential backoff with jitter
                    base_wait = 2 ** (attempt - 1)  # 2^0, 2^1, 2^2, ...
                    jitter = random.uniform(0, 1)  # Random jitter 0-1 seconds
                    wait_time = min(max_wait, base_wait + jitter)

                    # Wait before retrying
                    await asyncio.sleep(wait_time)

                except ClientResponseError as e:
                    # Only retry on 5xx server errors and 429 rate limiting
                    if e.status >= 500 or e.status == 429:
                        attempt += 1
                        if attempt >= max_attempts:
                            raise  # Re-raise if max attempts exhausted

                        # Calculate exponential backoff with jitter
                        base_wait = 2 ** (attempt - 1)
                        jitter = random.uniform(0, 1)
                        wait_time = min(max_wait, base_wait + jitter)

                        # Wait before retrying
                        await asyncio.sleep(wait_time)
                    else:
                        # Don't retry on 4xx client errors (except 429)
                        raise

        return wrapper

    return decorator


__all__ = ["retry_with_backoff"]
