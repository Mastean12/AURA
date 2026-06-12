import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_

from app.database.database import get_session_factory
from app.models.ai_usage import AIUsage
from app.models.ai_cache import AICache

logger = logging.getLogger(__name__)


async def log_ai_usage(
    request_type: str,
    provider: str | None = None,
    model: str | None = None,
    tokens_estimated: int | None = None,
    latency_ms: int | None = None,
    success: bool = True,
    error_message: str | None = None,
    retry_count: int = 0,
):
    try:
        async with get_session_factory()() as db:
            entry = AIUsage(
                request_type=request_type,
                provider=provider,
                model=model,
                tokens_estimated=tokens_estimated,
                latency_ms=latency_ms,
                success=1 if success else 0,
                error_message=error_message[:500] if error_message else None,
                retry_count=retry_count,
            )
            db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning("Failed to log AI usage: %s", e)


async def get_ai_usage_stats() -> dict:
    try:
        async with get_session_factory()() as db:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

            today_count = await db.execute(
                select(func.count(AIUsage.id)).where(AIUsage.created_at >= today)
            )
            month_start = today.replace(day=1)
            month_count = await db.execute(
                select(func.count(AIUsage.id)).where(AIUsage.created_at >= month_start)
            )
            total = await db.execute(func.count(AIUsage.id))
            failed = await db.execute(
                select(func.count(AIUsage.id)).where(AIUsage.success == 0)
            )
            avg_latency = await db.execute(
                select(func.avg(AIUsage.latency_ms)).where(AIUsage.success == 1)
            )
            retry_total = await db.execute(
                select(func.sum(AIUsage.retry_count))
            )
            tokens = await db.execute(
                select(func.sum(AIUsage.tokens_estimated))
            )

            recent = await db.execute(
                select(AIUsage).order_by(AIUsage.created_at.desc()).limit(20)
            )

            return {
                "requests_today": today_count.scalar() or 0,
                "requests_month": month_count.scalar() or 0,
                "total_requests": total.scalar() or 0,
                "failed_requests": failed.scalar() or 0,
                "avg_latency_ms": round(float(avg_latency.scalar() or 0), 1),
                "total_retries": retry_total.scalar() or 0,
                "tokens_estimated": tokens.scalar() or 0,
                "recent_usage": [
                    {
                        "id": r.id,
                        "request_type": r.request_type,
                        "provider": r.provider,
                        "latency_ms": r.latency_ms,
                        "success": r.success,
                        "error_message": r.error_message,
                        "retry_count": r.retry_count,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in recent.scalars().all()
                ],
            }
    except Exception as e:
        logger.warning("Failed to get AI usage stats: %s", e)
        return {
            "requests_today": 0, "requests_month": 0, "total_requests": 0,
            "failed_requests": 0, "avg_latency_ms": 0, "total_retries": 0,
            "tokens_estimated": 0, "recent_usage": [],
        }


def estimate_tokens(text: str) -> int:
    return len(text) // 4


COST_PER_TOKEN = 0.000000075


def estimate_cost(tokens: int) -> float:
    return round(tokens * COST_PER_TOKEN, 4)
