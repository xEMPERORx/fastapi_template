# Rate Limiting & Resilience

## Rate limiting — Redis sliding-window log

`app/core/ratelimit/sliding_window.py`'s `RedisSlidingWindowLimiter` backs two
shared instances in `app/core/ratelimit/limiters.py`:

- **`limiter`** — 10 requests / 60s per client IP, applied to every request via
  `app/middleware/ratelimiting_middleware.py`.
- **`login_limiter`** — 5 requests / 60s per *username* (not IP), applied only
  inside `LoginUser.login` — brute-force resistance that doesn't care which IP the
  attempts come from.

### Why sliding-window-log, not a fixed counter

A fixed window (`INCR` a counter, reset every 60s) lets up to ~2x the limit through
if requests cluster around the boundary (e.g. 10 requests at 0:59, 10 more at 1:01).
A sliding-window log records every request's *timestamp* as a member of a Redis
sorted set and, on each check, trims anything older than the window before counting
what's left — so the limit always applies to a true trailing window.

```mermaid
sequenceDiagram
    participant Req as Incoming request
    participant Limiter as RedisSlidingWindowLimiter
    participant Redis as Redis sorted set (ZSET)

    Req->>Limiter: is_allowed(client_ip)
    Limiter->>Redis: ZREMRANGEBYSCORE (trim entries older than `window`)
    Limiter->>Redis: ZADD (record this request's timestamp)
    Limiter->>Redis: ZCARD (count what's left)
    Limiter->>Redis: EXPIRE (key self-cleans if traffic stops)
    Note over Limiter,Redis: all four run in one MULTI/EXEC pipeline —<br/>concurrent requests for the same key can't race
    Redis-->>Limiter: count
    alt count > requests
        Limiter->>Redis: ZREM (undo this request's own entry)
        Limiter-->>Req: false → 429, Retry-After header
    else
        Limiter-->>Req: true → request proceeds
    end
```

A fresh `redis.asyncio.Redis` client is constructed **per call**, not cached —
clients bind their connection pool to whatever event loop was active when first
used, and a cached client breaks under pytest-asyncio's per-test loops (or any
multi-loop scenario). Construction itself does no I/O, so this is essentially free.

### Fail open

If Redis is unreachable, `is_allowed`/`get_remaining` catch the exception, log a
warning, and return `True`/the full limit — the API stays up; only the rate-limit
guarantee itself is temporarily lost. This is the same convention the authz cache
(`app.core.authz_cache`) follows — see
[06-authz-cache.md](./06-authz-cache.md).

## Resilience toolkit (`app/core/resilience/recovery.py`)

Two independent tools for calling flaky external services — nothing in this
template currently needs them (there's no external service integration yet beyond
Postgres/Redis/mail/Google, which have their own handling), but they're the pattern
to reach for when one is added.

### Retry with exponential backoff + jitter

```python
async def async_retry(func, *args, config: RetryConfig | None = None, **kwargs) -> T
```

Retries on `ConnectionError`, `TimeoutError`, `asyncio.TimeoutError`, `OSError` (not
arbitrary exceptions — a genuine business-logic error shouldn't be retried). Delay
grows as `base_delay * backoff_factor ** attempt`, capped at `max_delay`, randomized
within `[0, delay]` when `jitter=True` (spreads out retries from many callers instead
of them all retrying in lockstep). A `@retry(config=...)` decorator wraps the same
logic around a whole function.

### Circuit breaker

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> CLOSED: success, or failure < threshold
    CLOSED --> OPEN: failure_count >= failure_threshold
    OPEN --> HALF_OPEN: recovery_timeout elapses
    OPEN --> OPEN: call attempted before timeout → CircuitOpenError (no call made)
    HALF_OPEN --> CLOSED: the trial call succeeds
    HALF_OPEN --> OPEN: the trial call fails
```

`CircuitBreaker(name, config)` must be a **module-level singleton** per external
service — instantiating a fresh one per call defeats the entire point, since it
would never accumulate failures across calls and never trip. Usage:

```python
payment_breaker = CircuitBreaker("payment-gateway")  # module-level, once
result = await payment_breaker.call(payment_service.charge, amount=100)
```

`CircuitOpenError` (raised when the circuit is `OPEN`) is registered in
`app/error/register.py` and mapped to `429 Too Many Requests` — the same status code
as an ordinary rate limit, since both mean "back off and retry later" to a client.
