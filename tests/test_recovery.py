"""Tests for the Advanced Error Recovery skill."""

import asyncio
import pytest
from app.core.resilience.recovery import (
    async_retry,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
)

pytestmark = pytest.mark.asyncio


class TestRetry:
    async def test_retry_succeeds_first_attempt(self):
        calls = 0

        async def ok():
            nonlocal calls
            calls += 1
            return "ok"

        result = await async_retry(ok, config=RetryConfig(max_retries=3, base_delay=0.01))
        assert result == "ok"
        assert calls == 1

    async def test_retry_after_transient_failure(self):
        calls = 0

        async def flaky():
            nonlocal calls
            calls += 1
            if calls < 2:
                raise ConnectionError("transient")
            return "recovered"

        result = await async_retry(flaky, config=RetryConfig(max_retries=3, base_delay=0.01))
        assert result == "recovered"
        assert calls == 2

    async def test_retry_exhausted(self):
        async def always_fail():
            raise ConnectionError("persistent")

        with pytest.raises(ConnectionError):
            await async_retry(always_fail, config=RetryConfig(max_retries=2, base_delay=0.01))

    async def test_non_retryable_exception_raised_immediately(self):
        async def type_error_func():
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            await async_retry(type_error_func, config=RetryConfig(max_retries=3, base_delay=0.01))


class TestCircuitBreaker:
    async def test_closed_allows_calls(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30))

        async def ok():
            return "success"

        result = await cb.call(ok)
        assert result == "success"
        assert cb.state == "closed"

    async def test_trips_open_after_failures(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=30))

        async def fail():
            raise ConnectionError("boom")

        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(fail)

        assert cb.state == "open"

        with pytest.raises(CircuitOpenError):
            await cb.call(lambda: "should not reach")

    async def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01),
        )

        async def fail():
            raise ConnectionError("boom")

        with pytest.raises(ConnectionError):
            await cb.call(fail)
        assert cb.state == "open"

        # Wait for recovery timeout to pass
        await asyncio.sleep(0.05)

        async def ok():
            return "recovered"

        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == "closed"