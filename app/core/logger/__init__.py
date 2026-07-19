"""
Central logging utilities for the FastAPI starter template.

Split by concern across this package (see individual modules for detail):
- `context.py` — request ID propagation across async calls (ContextVar)
- `formatters.py` — JSON and human-readable log formatters
- `setup.py` — logger construction (console + rotating file handlers)
- `emit.py` — structured log-record emitters + redaction/layer inference
- `decorators.py` — `@log_function`, `LoggedService`, `LoggedRepository`

Everything below is re-exported here so existing `from app.core.logger import X`
call sites across the app are unaffected by the internal split.
"""

from app.core.logger.context import get_request_id, request_id_var, set_request_id
from app.core.logger.decorators import (
    LoggedMethods,
    LoggedRepository,
    LoggedService,
    log_function,
    log_method,
)
from app.core.logger.emit import (
    log_call,
    log_debug,
    log_error,
    log_info,
    log_request_end,
    log_request_start,
    log_result,
    log_warning,
)
from app.core.logger.formatters import BeautifulFormatter, StructuredFormatter
from app.core.logger.setup import logger, setup_logger

__all__ = [
    "request_id_var",
    "set_request_id",
    "get_request_id",
    "StructuredFormatter",
    "BeautifulFormatter",
    "setup_logger",
    "logger",
    "log_request_start",
    "log_request_end",
    "log_call",
    "log_result",
    "log_error",
    "log_info",
    "log_warning",
    "log_debug",
    "log_function",
    "log_method",
    "LoggedMethods",
    "LoggedService",
    "LoggedRepository",
]
