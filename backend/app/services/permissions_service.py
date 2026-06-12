from fastapi import HTTPException, status

ROLE_HIERARCHY = {"admin": 100, "manager": 60, "analyst": 30, "viewer": 10}

PERMISSIONS = {
    "upload_documents": ["admin", "manager", "analyst"],
    "delete_documents": ["admin", "manager"],
    "create_reports": ["admin", "manager", "analyst"],
    "view_reports": ["admin", "manager", "analyst", "viewer"],
    "view_dashboards": ["admin", "manager", "analyst", "viewer"],
    "manage_users": ["admin"],
    "manage_workspaces": ["admin", "manager"],
    "manage_organization": ["admin"],
    "run_analysis": ["admin", "manager", "analyst"],
    "manage_billing": ["admin"],
}


def role_value(role: str) -> int:
    return ROLE_HIERARCHY.get(role.lower(), 0)


def has_permission(role: str, permission: str) -> bool:
    allowed = PERMISSIONS.get(permission, [])
    return role.lower() in allowed


def require_permission(role: str, permission: str):
    if not has_permission(role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} requires role {PERMISSIONS.get(permission, '?')}",
        )


def role_at_least(user_role: str, minimum_role: str) -> bool:
    return role_value(user_role) >= role_value(minimum_role)
