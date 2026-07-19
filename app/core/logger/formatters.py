"""Log record formatters: JSON (for aggregation) and human-readable console output."""

import json
import logging
import traceback
from datetime import datetime
from typing import Any

from app.core.logger.context import request_id_var


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
