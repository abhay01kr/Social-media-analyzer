from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, PROJECT_NAME, VERSION, UPLOAD_DIR, RATE_LIMIT_PER_MINUTE
from utils.logger import RequestLoggingMiddleware, logger
from utils.security import SecurityHeadersMiddleware, RateLimitMiddleware
from database.db import init_db
from database.auth_db import init_auth_db
from database.db_unified import get_active_db_type

# Import routers for all members
from routers.auth import router as auth_router          # Member 1
from routers.profiles import router as profiles_router  # Member 2
from routers.media import router as media_router        # Member 3
from routers.content import router as content_router    # Member 4
from routers.reports import router as reports_router    # Member 5

app = FastAPI(
    title="Social Media Analyzer - Full Architecture",
    description=(
        "Production API Server for Social Media Analyzer.\n"
        "• Member 1: Authentication & User Management (/signup, /login, /profile)\n"
        "• Member 2: Profile Analyzer (/analyze/profile)\n"
        "• Member 3: Image & Video Analyzer (/analyze/image, /analyze/video)\n"
        "• Member 4: Content Analyzer (/analyze/content)\n"
        "• Member 5: Report & Dashboard (/report, /history, /dashboard)\n"
        "• Member 6: Database (MongoDB) & DevOps (Cloudinary, Security, Logging)"
    ),
    version=VERSION
)

# 1. Member 6 Security & Logging Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=RATE_LIMIT_PER_MINUTE, window_seconds=60)
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize Databases
init_db()
init_auth_db()

# 4. Static Files for Uploads
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 5. Mount API Routers for All Team Members
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(media_router)
app.include_router(content_router)
app.include_router(reports_router)

# 6. Core Status Endpoints
@app.get("/")
def home():
    return {
        "project": PROJECT_NAME,
        "version": VERSION,
        "database_backend": get_active_db_type(),
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "auth": ["/signup", "/login", "/profile", "/forgot-password"],
            "profile_analyzer": ["/analyze/profile"],
            "image_video_analyzer": ["/analyze/image", "/analyze/video"],
            "content_analyzer": ["/analyze/content"],
            "report_dashboard": ["/report", "/report/{id}/pdf", "/history", "/dashboard"]
        }
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": get_active_db_type(),
        "version": VERSION
    }
