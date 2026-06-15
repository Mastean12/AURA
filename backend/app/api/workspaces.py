from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, delete

from app.database.database import get_session_factory
from app.models.workspace import Workspace, WorkspaceMember
from app.services.auth_service import decode_token, get_current_user
from app.services.permissions_service import require_permission

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


async def _get_user_from_token(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    payload = decode_token(authorization[7:])
    user = await get_current_user(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "role": user.role, "organization_id": user.organization_id}


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.post("/")
async def create_workspace(payload: WorkspaceCreate, user: dict = Depends(_get_user_from_token)):
    require_permission(user["role"], "manage_workspaces")
    if not user.get("organization_id"):
        raise HTTPException(status_code=400, detail="No organization")
    async with get_session_factory()() as db:
        ws = Workspace(name=payload.name, description=payload.description,
                       organization_id=user["organization_id"], created_by=user["id"])
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        member = WorkspaceMember(workspace_id=ws.id, user_id=user["id"], role="admin")
        db.add(member)
        await db.commit()
        return {"id": ws.id, "name": ws.name, "description": ws.description}


@router.get("/")
async def list_workspaces(user: dict = Depends(_get_user_from_token)):
    if not user.get("organization_id"):
        return []
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Workspace).where(Workspace.organization_id == user["organization_id"])
        )
        return [{"id": w.id, "name": w.name, "description": w.description} for w in result.scalars().all()]


@router.put("/{ws_id}")
async def update_workspace(ws_id: int, payload: WorkspaceUpdate, user: dict = Depends(_get_user_from_token)):
    require_permission(user["role"], "manage_workspaces")
    async with get_session_factory()() as db:
        result = await db.execute(select(Workspace).where(Workspace.id == ws_id))
        ws = result.scalar_one_or_none()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if ws.organization_id != user["organization_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if payload.name:
            ws.name = payload.name
        if payload.description is not None:
            ws.description = payload.description
        await db.commit()
        return {"id": ws.id, "name": ws.name, "description": ws.description}


@router.delete("/{ws_id}")
async def delete_workspace(ws_id: int, user: dict = Depends(_get_user_from_token)):
    require_permission(user["role"], "manage_workspaces")
    async with get_session_factory()() as db:
        result = await db.execute(select(Workspace).where(Workspace.id == ws_id))
        ws = result.scalar_one_or_none()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if ws.organization_id != user["organization_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        await db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id))
        await db.delete(ws)
        await db.commit()
        return {"detail": "Workspace deleted"}
