import structlog
import uuid
from contextvars import ContextVar

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


def set_trace_id() -> str:
    trace_id = uuid.uuid4().hex[:12]
    trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> str:
    return trace_id_var.get()
