import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies strict modern security headers to all responses (Member 6).
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory IP-based rate limiting middleware.
    Protects login/signup and heavy analysis endpoints from DDoS and brute force.
    Default: 120 requests per minute per IP.
    """
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Ignore static assets or health checks
        if request.url.path in ("/", "/api/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean expired timestamps
        timestamps = self.clients[client_ip]
        self.clients[client_ip] = [ts for ts in timestamps if now - ts < self.window_seconds]
        
        if len(self.clients[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "detail": "Too many requests. Rate limit exceeded. Please wait a moment."
                },
                headers={"Retry-After": str(self.window_seconds)}
            )

        self.clients[client_ip].append(now)
        return await call_next(request)

def sanitize_text(text: str) -> str:
    """Sanitizes text by stripping harmful control characters."""
    if not text:
        return ""
    # Strip dangerous HTML/script characters if necessary
    return "".join(ch for ch in text if ch.isprintable() or ch in ("\n", "\r", "\t")).strip()
