"""
Advanced error recovery utilities.

Provides:
- Retry with exponential backoff and jitter
- Circuit breaker pattern for external service calls
"""

import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, TypeVar

from app.core.logger import logger

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Retry with exponential backoff + jitter
# ---------------------------------------------------------------------------

RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
    OSError,
)


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 0.5  # seconds
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable: tuple = RETRYABLE_EXCEPTIONS


async def async_retry(
    func: Callable[..., T],
    *args,
    config: RetryConfig | None = None,
    **kwargs,
) -> T:
    """Call *func* with exponential backoff + optional jitter on retryable errors."""
    cfg = config or RetryConfig()
    last_exc: Exception | None = None

    for attempt in range(cfg.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except cfg.retryable as exc:
            last_exc = exc
            if attempt == cfg.max_retries:
                logger.error(
                    "async_retry exhausted %d retries for %s: %s",
                    cfg.max_retries,
                    func.__name__,
                    exc,
                )
                raise
            delay = min(cfg.base_delay * (cfg.backoff_factor ** attempt), cfg.max_delay)
            if cfg.jitter:
                delay = random.uniform(0, delay)
            logger.warning(
                "async_retry attempt %d/%d for %s, retrying in %.2fs: %s",
                attempt + 1,
                cfg.max_retries,
                func.__name__,
                delay,
                exc,
            )
            await asyncio.sleep(delay)
        except Exception:
            raise

    raise last_exc  # type: ignore[misc]


def retry(config: RetryConfig | None = None):
    """Decorator version of async_retry."""
    cfg = config or RetryConfig()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await async_retry(func, *args, config=cfg, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds before half-open
    half_open_max: int = 1  # requests allowed in half-open state


class CircuitBreaker:
    """Thread-safe-ish circuit breaker for async external calls."""

    State = type("State", (), {"CLOSED": "closed", "OPEN": "open", "HALF_OPEN": "half_open"})

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.cfg = config or CircuitBreakerConfig()
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._open_until: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        return self._state

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        async with self._lock:
            if self._state == self.State.OPEN:
                if time.monotonic() >= self._open_until:
                    self._state = self.State.HALF_OPEN
                    logger.info("Circuit %s transitioning OPEN -> HALF_OPEN", self.name)
                else:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN. "
                        f"Retry in {self._open_until - time.monotonic():.1f}s"
                    )

        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            await self._record_failure()
            raise
        else:
            await self._record_success()
            return result

    async def _record_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == self.State.HALF_OPEN or (
                self._state == self.State.CLOSED
                and self._failure_count >= self.cfg.failure_threshold
            ):
                self._state = self.State.OPEN
                self._open_until = time.monotonic() + self.cfg.recovery_timeout
                logger.error(
                    "Circuit '%s' tripped OPEN (failures=%d, retry in %.1fs)",
                    self.name,
                    self._failure_count,
                    self.cfg.recovery_timeout,
                )

    async def _record_success(self):
        async with self._lock:
            if self._state == self.State.HALF_OPEN:
                logger.info("Circuit '%s' HALF_OPEN -> CLOSED (success)", self.name)
            self._state = self.State.CLOSED
            self._failure_count = 0


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and the call is rejected."""