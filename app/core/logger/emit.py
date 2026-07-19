"""Structured log-record emitters used by the request middleware and the
`@log_function`/`LoggedService`/`LoggedRepository` decorators in
`app.core.logger.decorators`.
"""

import logging
import sys
from typing import Any, Optional

from app.core.logger.setup import logger


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


def log_info(message: str, **extra) -> None:
    logger.info(message, extra={"extra_data": extra} if extra else {})


def log_warning(message: str, **extra) -> None:
    logger.warning(message, extra={"extra_data": extra} if extra else {})


def log_debug(message: str, **extra) -> None:
    logger.debug(message, extra={"extra_data": extra} if extra else {})
