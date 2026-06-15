from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.billing import PLANS
from app.services.auth_service import decode_token, get_current_user
from app.services.permissions_service import require_permission
from app.services.billing_service import get_billing_info, update_billing, change_plan, get_invoices
from app.services.billing_service import check_limits as check_usage_limits

router = APIRouter(prefix="/billing", tags=["billing"])


async def _get_admin(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(authorization[7:])
    user = await get_current_user(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_permission(user.role, "manage_organization")
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "role": user.role, "organization_id": user.organization_id}


class BillingUpdateRequest(BaseModel):
    billing_email: str | None = None
    billing_company: str | None = None
    tax_vat: str | None = None
    billing_address: str | None = None
    country: str | None = None
    currency: str | None = None
    po_number: str | None = None


class PlanChangeRequest(BaseModel):
    plan: str


@router.get("/")
async def get_billing(user: dict = Depends(_get_admin)):
    return await get_billing_info(user["organization_id"])


@router.put("/")
async def update_billing_settings(payload: BillingUpdateRequest, user: dict = Depends(_get_admin)):
    return await update_billing(user["organization_id"], payload.model_dump(exclude_none=True))


@router.post("/plan")
async def change_plan_endpoint(payload: PlanChangeRequest, user: dict = Depends(_get_admin)):
    return await change_plan(user["organization_id"], payload.plan)


@router.get("/plans")
async def list_plans():
    return [{"id": k, **v} for k, v in PLANS.items()]


@router.get("/usage")
async def get_usage(user: dict = Depends(_get_admin)):
    return await check_usage_limits(user["organization_id"])


@router.get("/invoices")
async def list_invoices(user: dict = Depends(_get_admin)):
    return await get_invoices(user["organization_id"])
