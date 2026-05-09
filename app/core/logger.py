"""
Central logging utilities for the FastAPI starter template.

Features:
- Request ID tracking across async calls
- Structured request/response cycle logs
- Decorators for route, service, and repository methods
- Human-readable and JSON log output
"""

from __future__ import annotations

import inspect
import json
import logging
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, ParamSpec

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

P = ParamSpec("P")
R = TypeVar("R")


class StructuredFormatter(logging.Formatter):
    """Formatter for JSON logs that are easy to parse."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "request_id": request_id_var.get() or "NO_REQUEST_ID",
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        extra_data = getattr(record, "extra_data", None)
        if extra_data is not None:
            log_data["extra"] = extra_data

        log_type = getattr(record, "log_type", None)
        if log_type is not None:
            log_data["log_type"] = log_type

        duration = getattr(record, "duration_ms", None)
        if duration is not None:
            log_data["duration_ms"] = duration

        exc_info = getattr(record, "exc_info_value", None)
        if isinstance(exc_info, tuple) and len(exc_info) == 3 and exc_info[0] is not None:
            log_data["exception"] = {
                "type": exc_info[0].__name__,
                "message": str(exc_info[1]),
                "traceback": traceback.format_exception(*exc_info),
            }

        return json.dumps(log_data, default=str)


class BeautifulFormatter(logging.Formatter):
    """Readable formatter with request and layer-specific sections."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = request_id_var.get() or "NO_REQUEST_ID"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_type = getattr(record, "log_type", None)
        layer = getattr(record, "layer", None)

        if log_type == "REQUEST_START":
            separator = "=" * 100
            formatted = f"\n{separator}\n"
            formatted += f"[REQUEST START] Request ID: {request_id} | {timestamp}\n"
            formatted += (
                f"   Method: {getattr(record, 'method', '-') }"
                f" | Path: {getattr(record, 'path', '-') }"
                f" | Client: {getattr(record, 'client_ip', '-') }\n"
            )
            query_params = getattr(record, "query_params", None)
            if query_params:
                formatted += f"   Query Params: {query_params}\n"
            formatted += f"{separator}"
            return formatted

        if log_type == "REQUEST_END":
            separator = "=" * 100
            formatted = f"\n{separator}\n"
            formatted += f"[REQUEST END] Request ID: {request_id} | {timestamp}\n"
            formatted += (
                f"   Status Code: {getattr(record, 'status_code', '-') }"
                f" | Duration: {float(getattr(record, 'duration_ms', 0.0)):.2f}ms\n"
            )
            formatted += f"{separator}\n"
            return formatted

        if log_type == "CALL":
            separator = "-" * 90
            formatted = f"\n{separator}\n"
            formatted += f"[{layer.upper() if layer else 'CALL'}] Request ID: {request_id} | {timestamp}\n"
            formatted += (
                f"   Owner: {getattr(record, 'owner', '-') }"
                f" | Method: {getattr(record, 'method_name', '-') }\n"
            )
            arguments = getattr(record, "arguments", None)
            if arguments is not None:
                formatted += f"   Arguments: {json.dumps(arguments, indent=6, default=str)}\n"
            formatted += f"{separator}"
            return formatted

        if log_type == "RESULT":
            separator = "-" * 90
            formatted = f"\n{separator}\n"
            formatted += f"[{layer.upper() if layer else 'RESULT'}] Request ID: {request_id} | {timestamp}\n"
            formatted += f"   Result Type: {getattr(record, 'result_type', '-') }\n"
            result_preview = getattr(record, "result_preview", None)
            if result_preview:
                formatted += f"   Preview: {result_preview}\n"
            formatted += f"{separator}"
            return formatted

        if log_type == "ERROR":
            separator = "!" * 100
            formatted = f"\n{separator}\n"
            formatted += f"[ERROR] Request ID: {request_id} | {timestamp}\n"
            formatted += f"   Layer: {layer or '-'}\n"
            formatted += f"   Error Type: {getattr(record, 'error_type', '-') }\n"
            formatted += f"   Message: {record.getMessage()}\n"
            error_location = getattr(record, "error_location", None)
            if error_location:
                formatted += f"   Location: {error_location}\n"
            formatted += f"{separator}"
            return formatted

        return f"[{timestamp}] [{record.levelname}] [ReqID: {request_id}] {record.getMessage()}"


def setup_logger(name: str = "app") -> logging.Logger:
    """Setup and configure the application logger."""
    Path("logs").mkdir(parents=True, exist_ok=True)

    app_logger = logging.getLogger(name)
    app_logger.setLevel(logging.DEBUG)
    app_logger.propagate = False
    app_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(console_handler)

    beautiful_file_handler = RotatingFileHandler(
        "logs/app_beautiful.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    beautiful_file_handler.setLevel(logging.DEBUG)
    beautiful_file_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(beautiful_file_handler)

    json_file_handler = RotatingFileHandler(
        "logs/app_structured.json",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    json_file_handler.setLevel(logging.DEBUG)
    json_file_handler.setFormatter(StructuredFormatter())
    app_logger.addHandler(json_file_handler)

    error_file_handler = RotatingFileHandler(
        "logs/errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(error_file_handler)

    return app_logger


logger = setup_logger()


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    return request_id_var.get()


def _redact_value(key: str, value: Any) -> Any:
    if any(token in key.lower() for token in ("pass", "token", "secret", "key")):
        return "********"
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return {k: _redact_value(k, v) for k, v in value.items()}
    return str(value)


def _infer_layer(module_name: str) -> str:
    if ".api." in module_name:
        return "route"
    if ".services." in module_name:
        return "service"
    if ".repositories." in module_name:
        return "repository"
    if ".middleware." in module_name:
        return "middleware"
    return "function"


def log_request_start(method: str, path: str, client_ip: str, query_params: Optional[dict] = None) -> None:
    record = logger.makeRecord(logger.name, logging.INFO, "", 0, "REQUEST_START", (), None)
    record.log_type = "REQUEST_START"
    record.method = method
    record.path = path
    record.client_ip = client_ip
    record.query_params = query_params
    logger.handle(record)


def log_request_end(status_code: int, duration_ms: float) -> None:
    record = logger.makeRecord(logger.name, logging.INFO, "", 0, "REQUEST_END", (), None)
    record.log_type = "REQUEST_END"
    record.status_code = status_code
    record.duration_ms = duration_ms
    logger.handle(record)


def log_call(owner: str, method_name: str, arguments: dict[str, Any], layer: str = "function") -> None:
    record = logger.makeRecord(logger.name, logging.INFO, "", 0, "CALL", (), None)
    record.log_type = "CALL"
    record.layer = layer
    record.owner = owner
    record.method_name = method_name
    record.arguments = arguments
    logger.handle(record)


def log_result(result_type: str, result_preview: str = "", layer: str = "function") -> None:
    record = logger.makeRecord(logger.name, logging.INFO, "", 0, "RESULT", (), None)
    record.log_type = "RESULT"
    record.layer = layer
    record.result_type = result_type
    record.result_preview = result_preview
    logger.handle(record)


def log_error(error_type: str, message: str, error_location: str = "", exc_info=None, layer: str = "function") -> None:
    normalized_exc_info = sys.exc_info() if exc_info is True else exc_info
    record = logger.makeRecord(logger.name, logging.ERROR, "", 0, message, (), normalized_exc_info)
    record.log_type = "ERROR"
    record.layer = layer
    record.error_type = error_type
    record.error_location = error_location
    record.exc_info_value = normalized_exc_info
    logger.handle(record)


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


def log_info(message: str, **extra) -> None:
    logger.info(message, extra={"extra_data": extra} if extra else {})


def log_warning(message: str, **extra) -> None:
    logger.warning(message, extra={"extra_data": extra} if extra else {})


def log_debug(message: str, **extra) -> None:
    logger.debug(message, extra={"extra_data": extra} if extra else {})
