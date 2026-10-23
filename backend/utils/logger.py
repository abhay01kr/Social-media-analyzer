import time
import uuid
import logging
import sys
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Configure root logger
logger = logging.getLogger("social_media_analyzer")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s] [ReqID: %(request_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Stream Handler (stdout)
stream_handler = logging.StreamHandler(sys.stdout)
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

stream_handler.addFilter(RequestIdFilter())
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# File Handler
try:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.addFilter(RequestIdFilter())
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Failed to initialize file logger: {e}")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique Request ID to each incoming HTTP request,
    times request execution, and logs structured access logs.
    """
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = req_id
        start_time = time.time()

        try:
            response: Response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id

            # Log request details
            extra = {"request_id": req_id}
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
                extra=extra
            )
            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            extra = {"request_id": req_id}
            logger.error(
                f"{request.method} {request.url.path} ERROR: {str(exc)} ({duration_ms:.2f}ms)",
                extra=extra,
                exc_info=True
            )
            raise exc
