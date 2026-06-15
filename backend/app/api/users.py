from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database.database import get_session_factory
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.document import Document
from app.models.ai_usage import AIUsage
from app.services.auth_service import decode_token, get_current_user, hash_password, create_access_token
from app.services.permissions_service import require_permission
from app.services.email_service import send_workspace_invite
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


async def _get_admin(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(authorization[7:])
    user = await get_current_user(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    require_permission(user.role, "manage_users")
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "role": user.role, "organization_id": user.organization_id}


class InviteUserRequest(BaseModel):
    full_name: str
    email: str
    role: str = "analyst"
    workspace_id: int | None = None


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    status: str | None = None


@router.get("/")
async def list_users(
    search: str = Query(""), status: str = Query(""),
    role: str = Query(""), admin: dict = Depends(_get_admin),
):
    async with get_session_factory()() as db:
        q = select(User).where(User.organization_id == admin["organization_id"])
        if search:
            q = q.where(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
        if status:
            is_active = status == "active"
            if status == "pending":
                q = q.where(User.is_active == False, User.is_verified == False)
            elif status == "disabled":
                q = q.where(User.is_active == False, User.is_verified == True)
            else:
                q = q.where(User.is_active == is_active)
        if role:
            q = q.where(User.role == role)
        q = q.order_by(User.created_at.desc())

        results = (await db.execute(q)).scalars().all()
        users = []
        for u in results:
            status_label = "active" if u.is_active else "pending" if not u.is_verified else "disabled"
            last_login = str(u.last_login) if u.last_login else None
            ws_count = (await db.execute(
                select(func.count(WorkspaceMember.id)).where(WorkspaceMember.user_id == u.id)
            )).scalar() or 0
            doc_count = (await db.execute(
                select(func.count(Document.id)).where(Document.uploaded_by == u.id)
            )).scalar() or 0
            users.append({
                "id": u.id, "full_name": u.full_name, "email": u.email,
                "role": u.role, "status": status_label, "last_login": last_login,
                "workspace_count": ws_count, "document_count": doc_count,
            })
        return {"users": users, "total": len(users)}


@router.get("/{user_id}")
async def get_user(user_id: int, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        status_label = "active" if u.is_active else "pending" if not u.is_verified else "disabled"

        ws_memberships = (await db.execute(
            select(WorkspaceMember, Workspace.name)
            .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == u.id)
        )).all()
        workspaces = [{"workspace_id": m.WorkspaceMember.workspace_id, "name": m.name, "role": m.WorkspaceMember.role} for m in ws_memberships]

        doc_count = (await db.execute(
            select(func.count(Document.id)).where(Document.uploaded_by == u.id)
        )).scalar() or 0

        ai_count = (await db.execute(
            select(func.count(AIUsage.id))
        )).scalar() or 0

        return {
            "id": u.id, "full_name": u.full_name, "email": u.email,
            "role": u.role, "status": status_label, "last_login": str(u.last_login) if u.last_login else None,
            "is_active": u.is_active, "is_verified": u.is_verified,
            "created_at": str(u.created_at) if u.created_at else None,
            "workspaces": workspaces,
            "document_count": doc_count,
            "ai_requests": ai_count,
        }


@router.put("/{user_id}")
async def update_user(user_id: int, payload: UpdateUserRequest, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        if payload.full_name:
            u.full_name = payload.full_name
        if payload.role:
            if payload.role not in ("admin", "manager", "analyst", "viewer"):
                raise HTTPException(status_code=400, detail="Invalid role")
            u.role = payload.role
        if payload.status == "active":
            u.is_active = True
        elif payload.status == "disabled":
            u.is_active = False
        await db.commit()
        await log_action(admin["id"], "update_user", f"user_id={user_id}", status="success")
    return {"detail": "User updated"}


@router.post("/{user_id}/disable")
async def disable_user(user_id: int, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        u.is_active = False
        await db.commit()
        await log_action(admin["id"], "disable_user", f"user_id={user_id}", status="success")
    return {"detail": "User disabled"}


@router.post("/{user_id}/activate")
async def activate_user(user_id: int, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        u.is_active = True
        await db.commit()
        await log_action(admin["id"], "activate_user", f"user_id={user_id}", status="success")
    return {"detail": "User activated"}


@router.post("/invite")
async def invite_user(payload: InviteUserRequest, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already exists with this email")

        import secrets
        temp_password = secrets.token_urlsafe(12)
        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(temp_password),
            role=payload.role,
            organization_id=admin["organization_id"],
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        if payload.workspace_id:
            ws = await db.execute(select(Workspace).where(Workspace.id == payload.workspace_id, Workspace.organization_id == admin["organization_id"]))
            ws_obj = ws.scalar_one_or_none()
            if ws_obj:
                existing_member = await db.execute(
                    select(WorkspaceMember).where(WorkspaceMember.workspace_id == payload.workspace_id, WorkspaceMember.user_id == user.id)
                )
                if not existing_member.scalar_one_or_none():
                    db.add(WorkspaceMember(workspace_id=payload.workspace_id, user_id=user.id, role=payload.role))

        await db.commit()
        await log_action(admin["id"], "invite_user", f"user_id={user.id}, email={payload.email}", status="success")

    ws_name = f"workspace #{payload.workspace_id}" if payload.workspace_id else "your organization"
    login_url = "http://localhost:3000/login"
    await send_workspace_invite(payload.email, admin["full_name"], ws_name, payload.role, "your organization", login_url)

    return {"detail": f"Invitation sent to {payload.email}", "user_id": user.id, "temp_password": temp_password}


@router.get("/{user_id}/workspaces")
async def get_user_workspaces(user_id: int, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        memberships = (await db.execute(
            select(WorkspaceMember, Workspace.name)
            .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
        )).all()
        return [{"workspace_id": m.WorkspaceMember.workspace_id, "name": m.name, "role": m.WorkspaceMember.role} for m in memberships]


@router.post("/{user_id}/workspaces/{ws_id}")
async def assign_workspace(user_id: int, ws_id: int, admin: dict = Depends(_get_admin)):
    async with get_session_factory()() as db:
        u = await db.get(User, user_id)
        if not u or u.organization_id != admin["organization_id"]:
            raise HTTPException(status_code=404, detail="User not found")
        ws = await db.execute(select(Workspace).where(Workspace.id == ws_id, Workspace.organization_id == admin["organization_id"]))
        ws_obj = ws.scalar_one_or_none()
        if not ws_obj:
            raise HTTPException(status_code=404, detail="Workspace not found")
        existing = await db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id, WorkspaceMember.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already assigned to this workspace")
        db.add(WorkspaceMember(workspace_id=ws_id, user_id=user_id, role=u.role))
        await db.commit()
        await log_action(admin["id"], "assign_workspace", f"user_id={user_id}, workspace_id={ws_id}", status="success")
    return {"detail": "User assigned to workspace"}
