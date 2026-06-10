import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db
from app.services.ai_service import generate_response, get_available_providers
from app.api.upload import router as documents_router
from app.api.chat import router as chat_router
from app.api.summary import router as summary_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AURA application")
    logger.info("DATABASE_URL=%s (used by %s)", settings.database_url, "app.config via pydantic-settings")
    logger.info("  Source: %s", ".env file" if getattr(settings, "_env_file_loaded", True) else "hardcoded default")
    try:
        await init_db()
    except Exception as e:
        logger.warning("Database init skipped: %s", e)
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down AURA application")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    route = request.url.path
    logger.info("[REQUEST] %s %s", request.method, route)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed = int((time.perf_counter() - start) * 1000)
        logger.info("[RESPONSE] %s %d - %dms", route, response.status_code, elapsed)
        response.headers["X-Response-Time-Ms"] = str(elapsed)
        return response
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        logger.error("[RESPONSE] %s ERROR - %dms: %s", route, elapsed, e)
        raise


app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(summary_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "application": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/test-ai")
async def test_ai():
    providers = get_available_providers()
    if not providers.get(providers["active"]):
        return {"error": f"No API key configured for active provider '{providers['active']}'", "providers": providers}
    try:
        result = generate_response("Return only the word 'ok' if you can read this.")
        return {"status": "ok", "response": result.strip(), "provider": providers["active"]}
    except Exception as e:
        return {"status": "error", "error": str(e), "provider": providers["active"]}
