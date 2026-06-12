import logging

from app.database.database import get_session_factory
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(user_id: int | None, action: str, resource: str | None = None,
                     ip_address: str | None = None, status: str = "success", details: str | None = None):
    try:
        async with get_session_factory()() as db:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                status=status,
                details=details,
            )
            db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning("Audit log failed: %s", e)


async def get_recent_logs(limit: int = 50) -> list[dict]:
    from sqlalchemy import select, desc
    try:
        async with get_session_factory()() as db:
            result = await db.execute(
                select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
            )
            return [
                {"id": e.id, "user_id": e.user_id, "action": e.action, "resource": e.resource,
                 "status": e.status, "ip_address": e.ip_address, "created_at": str(e.created_at) if e.created_at else None}
                for e in result.scalars().all()
            ]
    except Exception as e:
        logger.warning("Audit log read failed: %s", e)
        return []
