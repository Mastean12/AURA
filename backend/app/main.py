import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db
from app.services.ai_service import generate_response, get_available_providers, _gemini_generate
from app.api.upload import router as documents_router
from app.api.chat import router as chat_router
from app.api.summary import router as summary_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router
from app.api.predictive import router as predictive_router
from app.api.enterprise import router as enterprise_router
from app.api.admin import router as admin_router
from app.api.executive import router as executive_router
from app.api.auth import router as auth_router
from app.api.workspaces import router as workspaces_router

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
    # Verify AI provider on startup
    providers = get_available_providers()
    active = providers.get("active", "unknown")
    logger.info("AI provider: %s (key configured: %s)", active, providers.get(active, False))
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
async def observability_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    route = request.url.path
    start = time.perf_counter()
    logger.info("[%s] %s %s", request_id, request.method, route)
    try:
        response = await call_next(request)
        elapsed = int((time.perf_counter() - start) * 1000)
        logger.info("[%s] %s %d - %dms", request_id, route, response.status_code, elapsed)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed)
        return response
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        logger.error("[%s] %s ERROR - %dms: %s", request_id, route, elapsed, e)
        raise


app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(summary_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(predictive_router, prefix="/api/v1")
app.include_router(enterprise_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(executive_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")


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


@app.get("/health/ai")
async def ai_health():
    providers = get_available_providers()
    active = providers.get("active", "unknown")
    key_ok = providers.get(active, False)

    result = {
        "status": "unhealthy",
        "provider": active,
        "model": "",
        "key_configured": key_ok,
        "latency_ms": None,
        "last_success": None,
        "error": None,
    }

    if not key_ok:
        result["error"] = f"No API key configured for provider '{active}'"
        return result

    start = time.perf_counter()
    try:
        response = generate_response("Return only the word OK if you can read this.")
        elapsed = int((time.perf_counter() - start) * 1000)
        result["status"] = "healthy" if response.strip() == "OK" else "degraded"
        result["latency_ms"] = elapsed
        result["last_success"] = time.time()
        if active == "gemini":
            result["model"] = settings.gemini_model
        elif active == "openai":
            result["model"] = settings.openai_model
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        result["status"] = "unhealthy"
        result["latency_ms"] = elapsed
        result["error"] = str(e)

    return result


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
