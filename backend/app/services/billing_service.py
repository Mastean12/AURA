import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func

from app.database.database import get_session_factory
from app.models.billing import BillingAccount, Invoice, PLANS
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.ai_usage import AIUsage
from app.models.ai_cache import AICache

logger = logging.getLogger(__name__)


def _plan_limits(plan: str) -> dict:
    return PLANS.get(plan, PLANS["free"])


async def get_or_create_billing(org_id: int) -> dict:
    async with get_session_factory()() as db:
        ba = (await db.execute(select(BillingAccount).where(BillingAccount.org_id == org_id))).scalar_one_or_none()
        if not ba:
            ba = BillingAccount(org_id=org_id, plan="free", subscription_status="active")
            db.add(ba)
            await db.commit()
            await db.refresh(ba)
        return ba


async def get_usage(org_id: int) -> dict:
    async with get_session_factory()() as db:
        users = (await db.execute(select(func.count(User.id)).where(User.organization_id == org_id))).scalar() or 0
        workspaces = (await db.execute(select(func.count(Workspace.id)).where(Workspace.organization_id == org_id, Workspace.status == "active"))).scalar() or 0
        docs = (await db.execute(select(func.count(Document.id)).where(Document.organization_id == org_id))).scalar() or 0
        ai = (await db.execute(select(func.count(AIUsage.id)))).scalar() or 0
        total_bytes = (await db.execute(select(func.sum(Document.file_size)).where(Document.organization_id == org_id))).scalar() or 0
        storage_mb = round(total_bytes / (1024 * 1024), 1) if total_bytes else 0
        ba = await get_or_create_billing(org_id)
        limits = _plan_limits(ba.plan)
        return {
            "users": users, "users_limit": limits["users"],
            "workspaces": workspaces, "workspaces_limit": limits["workspaces"],
            "documents": docs, "documents_limit": limits["documents"],
            "ai_requests": ai, "ai_requests_limit": limits["ai_requests"],
            "storage_mb": storage_mb, "storage_limit_mb": limits["storage_mb"],
        }


async def check_limits(org_id: int) -> dict:
    usage = await get_usage(org_id)
    warnings = []
    blocked = []
    for key in ["users", "workspaces", "documents", "ai_requests"]:
        used = usage[key]
        limit = usage[f"{key}_limit"]
        pct = (used / limit * 100) if limit > 0 else 0
        if pct >= 100:
            blocked.append(key)
        elif pct >= 80:
            warnings.append(key)
    return {"warnings": warnings, "blocked": blocked, "usage": usage}


async def get_invoices(org_id: int, limit: int = 12) -> list[dict]:
    async with get_session_factory()() as db:
        rows = (await db.execute(
            select(Invoice).where(Invoice.org_id == org_id)
            .order_by(Invoice.created_at.desc()).limit(limit)
        )).scalars().all()
        return [
            {
                "id": inv.id, "invoice_number": inv.invoice_number,
                "amount_cents": inv.amount_cents, "currency": inv.currency,
                "status": inv.status, "plan_name": inv.plan_name,
                "period_start": str(inv.period_start) if inv.period_start else None,
                "period_end": str(inv.period_end) if inv.period_end else None,
                "paid_at": str(inv.paid_at) if inv.paid_at else None,
                "created_at": str(inv.created_at) if inv.created_at else None,
            }
            for inv in rows
        ]


async def get_billing_info(org_id: int) -> dict:
    ba = await get_or_create_billing(org_id)
    plan = _plan_limits(ba.plan)
    usage = await get_usage(org_id)
    invoices = await get_invoices(org_id)
    now = datetime.now(timezone.utc)
    period_end = ba.current_period_end or (now + timedelta(days=30))
    return {
        "plan": ba.plan,
        "plan_name": plan["name"],
        "price_cents": plan["price_cents"],
        "subscription_status": ba.subscription_status,
        "billing_email": ba.billing_email,
        "billing_company": ba.billing_company,
        "tax_vat": ba.tax_vat,
        "billing_address": ba.billing_address,
        "country": ba.country,
        "currency": ba.currency,
        "po_number": ba.po_number,
        "period_end": str(period_end) if period_end else None,
        "stripe_configured": bool(ba.stripe_customer_id),
        "usage": usage,
        "invoices": invoices,
    }


async def update_billing(org_id: int, data: dict) -> dict:
    async with get_session_factory()() as db:
        ba = (await db.execute(select(BillingAccount).where(BillingAccount.org_id == org_id))).scalar_one_or_none()
        if not ba:
            ba = BillingAccount(org_id=org_id)
            db.add(ba)
        for field in ["billing_email", "billing_company", "tax_vat", "billing_address", "country", "currency", "po_number"]:
            if field in data:
                setattr(ba, field, data[field])
        await db.commit()
    return {"detail": "Billing settings updated"}


async def change_plan(org_id: int, new_plan: str) -> dict:
    if new_plan not in PLANS:
        return {"error": f"Invalid plan. Choose: {', '.join(PLANS.keys())}"}
    async with get_session_factory()() as db:
        ba = (await db.execute(select(BillingAccount).where(BillingAccount.org_id == org_id))).scalar_one_or_none()
        if not ba:
            ba = BillingAccount(org_id=org_id)
            db.add(ba)
        old_plan = ba.plan
        ba.plan = new_plan
        ba.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
        await db.commit()
        logger.info("Plan changed: org=%d %s -> %s", org_id, old_plan, new_plan)
    return {"detail": f"Plan changed to {PLANS[new_plan]['name']}"}
