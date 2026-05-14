import time
import uuid
from contextvars import ContextVar

import structlog

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def setup_logging(debug: bool = False):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name or __name__)


def set_trace_id(trace_id: str = "") -> str:
    tid = trace_id or uuid.uuid4().hex[:12]
    trace_id_var.set(tid)
    return tid


def get_trace_id() -> str:
    return trace_id_var.get()


class TraceMiddleware:
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        incoming_trace_id = ""
        for key, value in headers.items():
            if key == b"x-trace-id":
                incoming_trace_id = value.decode()
                break

        trace_id = set_trace_id(incoming_trace_id)
        logger = get_logger("http")
        start = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request",
                method=scope.get("method", ""),
                path=scope.get("path", ""),
                duration_ms=elapsed_ms,
            )

    def __init__(self, app):
        self.app = app
