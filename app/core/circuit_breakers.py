"""
Process-wide circuit breaker instances for external services.

Must be module-level singletons — a CircuitBreaker instantiated fresh per
call would never accumulate failures and would never actually trip.
"""

from app.core.recovery import CircuitBreaker

es_breaker = CircuitBreaker("elasticsearch")
redis_breaker = CircuitBreaker("redis")
