"""Auto-logging decorators and base classes for routes/services/repositories."""

from __future__ import annotations

import inspect
import time
from functools import wraps
from typing import Callable, Optional, ParamSpec, TypeVar

from app.core.logger.emit import _infer_layer, _redact_value, log_call, log_error, log_result

P = ParamSpec("P")
R = TypeVar("R")


def _wrap_callable(func: Callable[P, R], layer: str) -> Callable[P, R]:
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs):
            owner = args[0].__class__.__name__ if args else func.__module__.rsplit(".", 1)[-1]
            bound_arguments = inspect.signature(func).bind_partial(*args, **kwargs)
            bound_arguments.apply_defaults()
            arguments = {
                key: _redact_value(key, value)
                for key, value in bound_arguments.arguments.items()
                if key not in {"self", "cls"}
            }
            log_call(owner=owner, method_name=func.__name__, arguments=arguments, layer=layer)
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = round((time.perf_counter() - start_time) * 1000, 2)
                result_preview = str(result)[:120]
                log_result(
                    result_type=f"Success ({type(result).__name__})",
                    result_preview=f"{result_preview} | {duration:.2f}ms",
                    layer=layer,
                )
                return result
            except Exception as exc:
                duration = round((time.perf_counter() - start_time) * 1000, 2)
                log_error(
                    error_type=type(exc).__name__,
                    message=str(exc),
                    error_location=f"{owner}.{func.__name__}",
                    exc_info=True,
                    layer=layer,
                )
                log_result(result_type="Error", result_preview=f"{duration:.2f}ms", layer=layer)
                raise

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs):
        owner = args[0].__class__.__name__ if args else func.__module__.rsplit(".", 1)[-1]
        bound_arguments = inspect.signature(func).bind_partial(*args, **kwargs)
        bound_arguments.apply_defaults()
        arguments = {
            key: _redact_value(key, value)
            for key, value in bound_arguments.arguments.items()
            if key not in {"self", "cls"}
        }
        log_call(owner=owner, method_name=func.__name__, arguments=arguments, layer=layer)
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            result_preview = str(result)[:120]
            log_result(
                result_type=f"Success ({type(result).__name__})",
                result_preview=f"{result_preview} | {duration:.2f}ms",
                layer=layer,
            )
            return result
        except Exception as exc:
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            log_error(
                error_type=type(exc).__name__,
                message=str(exc),
                error_location=f"{owner}.{func.__name__}",
                exc_info=True,
                layer=layer,
            )
            log_result(result_type="Error", result_preview=f"{duration:.2f}ms", layer=layer)
            raise

    return sync_wrapper


def log_function(func: Callable[P, R]) -> Callable[P, R]:
    """Backward-compatible decorator for standalone functions."""
    return _wrap_callable(func, _infer_layer(func.__module__))


def log_method(func: Optional[Callable[P, R]] = None, *, layer: str = "function"):
    """Decorator factory for functions when layer should be explicit."""

    def decorator(inner: Callable[P, R]) -> Callable[P, R]:
        return _wrap_callable(inner, layer)

    if func is not None:
        return decorator(func)
    return decorator


class LoggedMethods:
    """Base class that automatically logs public methods on subclasses."""

    _log_layer = "function"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, value in list(cls.__dict__.items()):
            if name.startswith("_") or name == "__init__":
                continue
            if inspect.isfunction(value):
                setattr(cls, name, log_method(value, layer=cls._log_layer))


class LoggedService(LoggedMethods):
    _log_layer = "service"


class LoggedRepository(LoggedMethods):
    _log_layer = "repository"
