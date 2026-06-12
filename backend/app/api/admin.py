from fastapi import APIRouter

from app.services.monitoring_service import get_ai_usage_stats, estimate_cost
from app.services.cache_service import get_cache_stats
from app.services.ai_service import get_available_providers
from app.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ai-monitoring")
async def ai_monitoring():
    settings = get_settings()
    providers = get_available_providers()
    active = providers.get("active", "unknown")
    usage = await get_ai_usage_stats()
    cache = await get_cache_stats()

    tokens_used = usage.get("tokens_estimated", 0)
    tokens_saved = cache.get("total_hits", 0) * 500
    total_hits = cache.get("total_hits", 0)
    total_entries = cache.get("total_entries", 0)

    return {
        "ai_usage": {
            "requests_today": usage.get("requests_today", 0),
            "requests_month": usage.get("requests_month", 0),
            "total_requests": usage.get("total_requests", 0),
            "tokens_consumed": tokens_used,
            "estimated_cost": estimate_cost(tokens_used),
            "average_response_time_ms": usage.get("avg_latency_ms", 0),
            "total_retries": usage.get("total_retries", 0),
            "failed_requests": usage.get("failed_requests", 0),
        },
        "ai_health": {
            "provider": active,
            "active_model": settings.gemini_model if active == "gemini" else settings.openai_model,
            "key_configured": providers.get(active, False),
        },
        "cache_metrics": {
            "cache_hit_rate": round(total_hits / (total_hits + usage.get("total_requests", 1)) * 100, 1) if (total_hits + usage.get("total_requests", 0)) > 0 else 0,
            "cache_miss_rate": round(usage.get("total_requests", 0) / (total_hits + usage.get("total_requests", 1)) * 100, 1) if (total_hits + usage.get("total_requests", 0)) > 0 else 0,
            "tokens_saved": tokens_saved,
            "estimated_cost_savings": estimate_cost(tokens_saved),
            "cache_entries": total_entries,
        },
        "error_monitoring": {
            "failed_requests": usage.get("failed_requests", 0),
            "timeout_count": sum(1 for r in usage.get("recent_usage", []) if not r.get("success")),
            "retry_count": usage.get("total_retries", 0),
            "recent_errors": [
                {"type": r["request_type"], "error": r["error_message"], "time": r.get("created_at")}
                for r in usage.get("recent_usage", []) if not r.get("success")
            ][:10],
        },
    }
