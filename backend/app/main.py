import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db
from app.services.ai_service import generate_response_async, get_available_providers
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
from app.api.organization import router as organization_router
from app.api.users import router as users_router
from app.api.data_intelligence import router as data_intel_router
from app.api.pipeline import router as pipeline_router
from app.api.columns import router as columns_router
from app.api.billing import router as billing_router

# Import all models so SQLAlchemy metadata registers them for create_all
from app.models.user import User  # noqa: F401
from app.models.organization import Organization, OrganizationSecurity, OrganizationAIConfig, OrganizationDataGovernance  # noqa: F401
from app.models.billing import BillingAccount, Invoice  # noqa: F401
from app.models.dataset_meta import DatasetMetadata  # noqa: F401
from app.models.quality_report import QualityReport  # noqa: F401
from app.models.column_meta import ColumnMetadata  # noqa: F401
from app.models.workspace import Workspace, WorkspaceMember  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

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
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
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
app.include_router(organization_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(data_intel_router, prefix="/api/v1")
app.include_router(columns_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")


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
        response = await generate_response_async("Return only the word OK if you can read this.", request_type="health_check")
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
        result = await generate_response_async("Return only the word 'ok' if you can read this.", request_type="test")
        return {"status": "ok", "response": result.strip(), "provider": providers["active"]}
    except Exception as e:
        return {"status": "error", "error": str(e), "provider": providers["active"]}
