from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, delete, func

from app.database.database import get_session_factory
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceSettings
from app.models.document import Document
from app.services.auth_service import decode_token, get_current_user
from app.services.permissions_service import require_permission

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

WORKSPACE_TYPES = ["department", "project", "team", "custom"]
WORKSPACE_ROLES = ["workspace_admin", "manager", "analyst", "viewer"]


async def _get_user_from_token(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(authorization[7:])
    user = await get_current_user(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "role": user.role, "organization_id": user.organization_id}


async def _verify_workspace_access(workspace_id: int, user: dict, min_role: str = "viewer") -> dict:
    async with get_session_factory()() as db:
        ws = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        ws = ws.scalar_one_or_none()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if ws.organization_id != user.get("organization_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user["id"],
            )
        )
        member = member.scalar_one_or_none()
        user_role = member.role if member else user["role"]
        role_rank = {"workspace_admin": 100, "manager": 60, "analyst": 30, "viewer": 10,
                     "admin": 100, "analyst": 30, "viewer": 10}
        if role_rank.get(user_role, 0) < role_rank.get(min_role, 0):
            raise HTTPException(status_code=403, detail="Insufficient workspace role")
        return {"workspace": ws, "member_role": user_role}


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""
    workspace_type: str = "department"


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    workspace_type: str | None = None
    status: str | None = None


class WorkspaceMemberAdd(BaseModel):
    user_id: int
    role: str = "analyst"


class WorkspaceRoleUpdate(BaseModel):
    role: str


class WorkspaceSettingsUpdate(BaseModel):
    ai_provider: str | None = None
    executive_insights: int | None = None
    forecasting: int | None = None
    risk_analysis: int | None = None
    recommendations: int | None = None
    allow_uploads: int | None = None
    allow_ai_chat: int | None = None
    allow_analytics: int | None = None
    allow_pdf_export: int | None = None
    allow_executive_reports: int | None = None


@router.post("/")
async def create_workspace(payload: WorkspaceCreate, user: dict = Depends(_get_user_from_token)):
    require_permission(user["role"], "manage_workspaces")
    if payload.workspace_type not in WORKSPACE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Choose: {WORKSPACE_TYPES}")
    async with get_session_factory()() as db:
        ws = Workspace(
            name=payload.name, description=payload.description, workspace_type=payload.workspace_type,
            organization_id=user["organization_id"], owner_id=user["id"], created_by=user["id"],
        )
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        db.add(WorkspaceMember(workspace_id=ws.id, user_id=user["id"], role="workspace_admin"))
        db.add(WorkspaceSettings(workspace_id=ws.id))
        await db.commit()
        return {"id": ws.id, "name": ws.name, "description": ws.description, "workspace_type": ws.workspace_type, "status": ws.status}


@router.get("/")
async def list_workspaces(user: dict = Depends(_get_user_from_token)):
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Workspace).where(Workspace.organization_id == user["organization_id"])
        )
        wss = result.scalars().all()
        out = []
        for ws in wss:
            member = await db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == user["id"]
                )
            )
            m = member.scalar_one_or_none()
            role_in_ws = m.role if m else None
            out.append({
                "id": ws.id, "name": ws.name, "description": ws.description,
                "workspace_type": ws.workspace_type, "status": ws.status,
                "my_role": role_in_ws,
                "member_count": (await db.execute(
                    select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == ws.id)
                )).scalar() or 0,
                "doc_count": (await db.execute(
                    select(func.count(Document.id)).where(Document.workspace_id == ws.id)
                )).scalar() or 0,
            })
        return out


@router.get("/{ws_id}")
async def get_workspace(ws_id: int, user: dict = Depends(_get_user_from_token)):
    info = await _verify_workspace_access(ws_id, user)
    ws = info["workspace"]
    async with get_session_factory()() as db:
        members = (await db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id)
        )).scalars().all()
        settings = (await db.execute(
            select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == ws_id)
        )).scalar_one_or_none()
        return {
            "id": ws.id, "name": ws.name, "description": ws.description,
            "workspace_type": ws.workspace_type, "status": ws.status,
            "owner_id": ws.owner_id, "created_at": str(ws.created_at) if ws.created_at else None,
            "member_count": len(members),
            "doc_count": (await db.execute(
                select(func.count(Document.id)).where(Document.workspace_id == ws_id)
            )).scalar() or 0,
            "members": [
                {"id": m.id, "user_id": m.user_id, "role": m.role, "joined_at": str(m.joined_at) if m.joined_at else None}
                for m in members
            ],
            "settings": {
                "ai_provider": settings.ai_provider if settings else "gemini",
                "executive_insights": bool(settings.executive_insights) if settings else True,
                "forecasting": bool(settings.forecasting) if settings else True,
                "risk_analysis": bool(settings.risk_analysis) if settings else True,
                "recommendations": bool(settings.recommendations) if settings else True,
                "allow_uploads": bool(settings.allow_uploads) if settings else True,
                "allow_ai_chat": bool(settings.allow_ai_chat) if settings else True,
                "allow_analytics": bool(settings.allow_analytics) if settings else True,
                "allow_pdf_export": bool(settings.allow_pdf_export) if settings else True,
                "allow_executive_reports": bool(settings.allow_executive_reports) if settings else True,
            } if settings else {},
        }


@router.put("/{ws_id}")
async def update_workspace(ws_id: int, payload: WorkspaceUpdate, user: dict = Depends(_get_user_from_token)):
    info = await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    ws = info["workspace"]
    if payload.name:
        ws.name = payload.name
    if payload.description is not None:
        ws.description = payload.description
    if payload.workspace_type:
        if payload.workspace_type not in WORKSPACE_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid type. Choose: {WORKSPACE_TYPES}")
        ws.workspace_type = payload.workspace_type
    if payload.status:
        if payload.status not in ("active", "archived"):
            raise HTTPException(status_code=400, detail="Status must be active or archived")
        ws.status = payload.status
    async with get_session_factory()() as db:
        db.add(ws)
        await db.commit()
    return {"detail": "Workspace updated"}


@router.delete("/{ws_id}")
async def delete_workspace(ws_id: int, user: dict = Depends(_get_user_from_token)):
    info = await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    ws = info["workspace"]
    async with get_session_factory()() as db:
        await db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id))
        await db.execute(delete(WorkspaceSettings).where(WorkspaceSettings.workspace_id == ws_id))
        await db.delete(ws)
        await db.commit()
    return {"detail": "Workspace deleted"}


@router.post("/{ws_id}/members")
async def add_member(ws_id: int, payload: WorkspaceMemberAdd, user: dict = Depends(_get_user_from_token)):
    await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    if payload.role not in WORKSPACE_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose: {WORKSPACE_ROLES}")
    async with get_session_factory()() as db:
        existing = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == ws_id, WorkspaceMember.user_id == payload.user_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already a member")
        db.add(WorkspaceMember(workspace_id=ws_id, user_id=payload.user_id, role=payload.role))
        await db.commit()
    return {"detail": "Member added"}


@router.put("/{ws_id}/members/{user_id}")
async def update_member_role(ws_id: int, user_id: int, payload: WorkspaceRoleUpdate,
                             user: dict = Depends(_get_user_from_token)):
    await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    if payload.role not in WORKSPACE_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose: {WORKSPACE_ROLES}")
    async with get_session_factory()() as db:
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == ws_id, WorkspaceMember.user_id == user_id
            )
        )
        m = member.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Member not found")
        m.role = payload.role
        await db.commit()
    return {"detail": "Role updated"}


@router.delete("/{ws_id}/members/{user_id}")
async def remove_member(ws_id: int, user_id: int, user: dict = Depends(_get_user_from_token)):
    await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    async with get_session_factory()() as db:
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == ws_id, WorkspaceMember.user_id == user_id
            )
        )
        m = member.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Member not found")
        await db.delete(m)
        await db.commit()
    return {"detail": "Member removed"}


@router.get("/{ws_id}/settings")
async def get_settings(ws_id: int, user: dict = Depends(_get_user_from_token)):
    await _verify_workspace_access(ws_id, user)
    async with get_session_factory()() as db:
        s = (await db.execute(select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == ws_id))).scalar_one_or_none()
        if not s:
            return {}
        return {
            "ai_provider": s.ai_provider,
            "executive_insights": bool(s.executive_insights),
            "forecasting": bool(s.forecasting),
            "risk_analysis": bool(s.risk_analysis),
            "recommendations": bool(s.recommendations),
            "allow_uploads": bool(s.allow_uploads),
            "allow_ai_chat": bool(s.allow_ai_chat),
            "allow_analytics": bool(s.allow_analytics),
            "allow_pdf_export": bool(s.allow_pdf_export),
            "allow_executive_reports": bool(s.allow_executive_reports),
        }


@router.put("/{ws_id}/settings")
async def update_settings(ws_id: int, payload: WorkspaceSettingsUpdate, user: dict = Depends(_get_user_from_token)):
    await _verify_workspace_access(ws_id, user, min_role="workspace_admin")
    async with get_session_factory()() as db:
        s = (await db.execute(select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == ws_id))).scalar_one_or_none()
        if not s:
            s = WorkspaceSettings(workspace_id=ws_id)
            db.add(s)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(s, field, value)
        await db.commit()
    return {"detail": "Settings updated"}
