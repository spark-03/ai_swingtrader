from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry_call(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    initial_delay: float = 0.5,
    backoff: float = 2.0,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Run an operation with bounded exponential backoff."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    delay = initial_delay
    last_error: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_exceptions as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(delay)
            delay *= backoff

    if last_error is None:
        raise RuntimeError("retry_call failed without capturing an exception")
    raise last_error
