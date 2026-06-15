from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database.database import get_session_factory
from app.models.organization import Organization, OrganizationSecurity, OrganizationAIConfig, OrganizationDataGovernance
from app.models.workspace import Workspace
from app.models.user import User
from app.models.document import Document
from app.models.ai_cache import AICache
from app.models.ai_usage import AIUsage
from app.services.auth_service import decode_token, get_current_user
from app.services.permissions_service import require_permission

router = APIRouter(prefix="/organization", tags=["organization"])


async def _get_org_admin(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(authorization[7:])
    user = await get_current_user(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_permission(user.role, "manage_organization")
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "role": user.role, "organization_id": user.organization_id}


async def _get_org(org_id: int, db):
    from sqlalchemy import select as sel
    r = await db.execute(sel(Organization).where(Organization.id == org_id))
    org = r.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


class OrgProfileUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    address: str | None = None
    description: str | None = None
    timezone: str | None = None
    theme_color: str | None = None


class SecurityUpdate(BaseModel):
    password_min_length: int | None = None
    password_require_special: bool | None = None
    password_expiry_days: int | None = None
    session_timeout_minutes: int | None = None
    require_mfa: bool | None = None
    require_email_verification: bool | None = None
    allow_public_invitations: bool | None = None
    lock_inactive_days: int | None = None
    force_password_reset: bool | None = None


class AIConfigUpdate(BaseModel):
    ai_provider: str | None = None
    executive_intelligence: bool | None = None
    risk_analysis: bool | None = None
    forecasting: bool | None = None
    recommendations: bool | None = None
    board_reports: bool | None = None
    document_chat: bool | None = None
    knowledge_search: bool | None = None
    monthly_budget_cents: int | None = None
    max_daily_requests: int | None = None
    max_monthly_requests: int | None = None
    auto_shutdown_threshold: int | None = None


class GovernanceUpdate(BaseModel):
    data_retention_days: int | None = None
    max_upload_size_mb: int | None = None
    allowed_file_types: str | None = None
    document_retention_days: int | None = None
    gdpr_compliant: bool | None = None
    soc2_compliant: bool | None = None
    iso27001_compliant: bool | None = None


@router.get("/profile")
async def get_profile(user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        org = await _get_org(user["organization_id"], db)
        return {
            "id": org.id, "name": org.name, "industry": org.industry,
            "website": org.website, "email": org.email, "phone": org.phone,
            "country": org.country, "address": org.address,
            "logo_url": org.logo_url, "theme_color": org.theme_color,
            "description": org.description, "timezone": org.timezone,
            "subscription_plan": org.subscription_plan, "status": org.status,
            "created_at": str(org.created_at) if org.created_at else None,
        }


@router.put("/profile")
async def update_profile(payload: OrgProfileUpdate, user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        org = await _get_org(user["organization_id"], db)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(org, field, value)
        await db.commit()
    return {"detail": "Organization updated"}


@router.get("/security")
async def get_security(user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        s = (await db.execute(select(OrganizationSecurity).where(OrganizationSecurity.org_id == user["organization_id"]))).scalar_one_or_none()
        if not s:
            return {}
        return {
            "password_min_length": s.password_min_length,
            "password_require_special": s.password_require_special,
            "password_expiry_days": s.password_expiry_days,
            "session_timeout_minutes": s.session_timeout_minutes,
            "require_mfa": s.require_mfa,
            "require_email_verification": s.require_email_verification,
            "allow_public_invitations": s.allow_public_invitations,
            "lock_inactive_days": s.lock_inactive_days,
            "force_password_reset": s.force_password_reset,
        }


@router.put("/security")
async def update_security(payload: SecurityUpdate, user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        s = (await db.execute(select(OrganizationSecurity).where(OrganizationSecurity.org_id == user["organization_id"]))).scalar_one_or_none()
        if not s:
            s = OrganizationSecurity(org_id=user["organization_id"])
            db.add(s)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(s, field, value)
        await db.commit()
    return {"detail": "Security settings updated"}


@router.get("/ai-config")
async def get_ai_config(user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        c = (await db.execute(select(OrganizationAIConfig).where(OrganizationAIConfig.org_id == user["organization_id"]))).scalar_one_or_none()
        if not c:
            return {}
        return {
            "ai_provider": c.ai_provider,
            "executive_intelligence": c.executive_intelligence,
            "risk_analysis": c.risk_analysis,
            "forecasting": c.forecasting,
            "recommendations": c.recommendations,
            "board_reports": c.board_reports,
            "document_chat": c.document_chat,
            "knowledge_search": c.knowledge_search,
            "monthly_budget_cents": c.monthly_budget_cents,
            "max_daily_requests": c.max_daily_requests,
            "max_monthly_requests": c.max_monthly_requests,
            "auto_shutdown_threshold": c.auto_shutdown_threshold,
        }


@router.put("/ai-config")
async def update_ai_config(payload: AIConfigUpdate, user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        c = (await db.execute(select(OrganizationAIConfig).where(OrganizationAIConfig.org_id == user["organization_id"]))).scalar_one_or_none()
        if not c:
            c = OrganizationAIConfig(org_id=user["organization_id"])
            db.add(c)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(c, field, value)
        await db.commit()
    return {"detail": "AI configuration updated"}


@router.get("/governance")
async def get_governance(user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        g = (await db.execute(select(OrganizationDataGovernance).where(OrganizationDataGovernance.org_id == user["organization_id"]))).scalar_one_or_none()
        if not g:
            return {}
        return {
            "data_retention_days": g.data_retention_days,
            "max_upload_size_mb": g.max_upload_size_mb,
            "allowed_file_types": g.allowed_file_types,
            "document_retention_days": g.document_retention_days,
            "gdpr_compliant": g.gdpr_compliant,
            "soc2_compliant": g.soc2_compliant,
            "iso27001_compliant": g.iso27001_compliant,
        }


@router.put("/governance")
async def update_governance(payload: GovernanceUpdate, user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        g = (await db.execute(select(OrganizationDataGovernance).where(OrganizationDataGovernance.org_id == user["organization_id"]))).scalar_one_or_none()
        if not g:
            g = OrganizationDataGovernance(org_id=user["organization_id"])
            db.add(g)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(g, field, value)
        await db.commit()
    return {"detail": "Governance settings updated"}


@router.get("/analytics")
async def get_analytics(user: dict = Depends(_get_org_admin)):
    org_id = user["organization_id"]
    async with get_session_factory()() as db:
        total_users = (await db.execute(select(func.count(User.id)).where(User.organization_id == org_id))).scalar() or 0
        active_users = (await db.execute(select(func.count(User.id)).where(User.organization_id == org_id, User.is_active == True))).scalar() or 0
        total_workspaces = (await db.execute(select(func.count(Workspace.id)).where(Workspace.organization_id == org_id))).scalar() or 0
        active_workspaces = (await db.execute(select(func.count(Workspace.id)).where(Workspace.organization_id == org_id, Workspace.status == "active"))).scalar() or 0
        total_docs = (await db.execute(select(func.count(Document.id)).where(Document.organization_id == org_id))).scalar() or 0
        processed_docs = (await db.execute(select(func.count(Document.id)).where(Document.organization_id == org_id, Document.processing_status == "completed"))).scalar() or 0
        ai_requests = (await db.execute(select(func.count(AIUsage.id)))).scalar() or 0
        tokens = (await db.execute(select(func.sum(AIUsage.tokens_estimated)))).scalar() or 0
        cache_hits = (await db.execute(select(func.sum(AICache.hit_count)))).scalar() or 0
        return {
            "total_users": total_users, "active_users": active_users, "inactive_users": total_users - active_users,
            "total_workspaces": total_workspaces, "active_workspaces": active_workspaces,
            "total_documents": total_docs, "documents_processed": processed_docs,
            "ai_requests": ai_requests, "tokens_consumed": tokens, "cache_hits": cache_hits or 0,
        }


@router.get("/subscription")
async def get_subscription(user: dict = Depends(_get_org_admin)):
    async with get_session_factory()() as db:
        org = await _get_org(user["organization_id"], db)
        total_users = (await db.execute(select(func.count(User.id)).where(User.organization_id == org.id))).scalar() or 0
        total_docs = (await db.execute(select(func.count(Document.id)).where(Document.organization_id == org.id))).scalar() or 0
        storage_used_mb = total_docs * 2
        return {
            "plan": org.subscription_plan,
            "users_allowed": 10 if org.subscription_plan == "free" else 50 if org.subscription_plan == "professional" else 9999,
            "storage_used_mb": storage_used_mb,
            "storage_limit_mb": 500 if org.subscription_plan == "free" else 5000 if org.subscription_plan == "professional" else 99999,
            "users_count": total_users,
            "renewal_date": str(org.created_at) if org.created_at else None,
        }
