from fastapi import APIRouter, Depends, HTTPException, Query
from backend.users.service import UserService
from backend.users.schema import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    UserWithRoleResponse,
    UserListResponse,
    UserRoleAssignment,
    PermissionCheckRequest,
    PermissionCheckResponse,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_service() -> UserService:
    service = UserService()
    if not service.initialize():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize users module! (╥﹏╥)",
        )
    return service


# ─── Role Routes ────────────────────────────────────────────────

@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    page: int = 1,
    per_page: int = 50,
    service: UserService = Depends(get_service),
):
    """List all roles."""
    return service.list_roles(page=page, per_page=per_page)


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    data: RoleCreate,
    service: UserService = Depends(get_service),
):
    """Create a new role with permissions."""
    try:
        return service.create_role(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles/stats")
async def role_stats(
    service: UserService = Depends(get_service),
):
    """Get user and role statistics."""
    return service.get_stats()


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    service: UserService = Depends(get_service),
):
    """Get a role by ID."""
    result = service.get_role(role_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find role '{role_id}'~ (╥﹏╥)",
        )
    return result


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    data: RoleUpdate,
    service: UserService = Depends(get_service),
):
    """
    Update a role.

    ⚠️ Changes apply to ALL users with this role immediately!
    """
    try:
        return service.update_role(role_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: str,
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
    service: UserService = Depends(get_service),
):
    """
    Delete a role.

    ⚠️ This removes the role from all users assigned to it!
    Aina-chan requires confirm=True!
    """
    try:
        service.delete_role(role_id, confirm=confirm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── User Management Routes ─────────────────────────────────────

@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    per_page: int = 50,
    service: UserService = Depends(get_service),
):
    """List all users with their roles."""
    return service.list_users(page=page, per_page=per_page)


@router.get("/me", response_model=UserWithRoleResponse)
async def get_current_user(
    service: UserService = Depends(get_service),
):
    """
    Get the current authenticated user with role info.

    Note: In a real app, you'd extract the user ID from the JWT token.
    For now, Aina-chan returns a placeholder — Senpai will need to
    wire up proper auth middleware! (◕‿◕✿)
    """
    # Placeholder: In production, get user_id from auth middleware
    raise HTTPException(
        status_code=501,
        detail="Auth middleware not yet implemented! "
               "Aina-chan will help Senpai set this up~",
    )


@router.get("/{user_id}", response_model=UserWithRoleResponse)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_service),
):
    """Get a user by ID with their role."""
    result = service.get_user_with_role(user_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find user '{user_id}'~ (╥﹏╥)",
        )
    return result


@router.put("/{user_id}/role", response_model=UserWithRoleResponse)
async def assign_user_role(
    user_id: str,
    data: UserRoleAssignment,
    service: UserService = Depends(get_service),
):
    """
    Assign a role to a user.

    Updating the role's permissions later will automatically
    affect this user! (◕‿◕✿)
    """
    try:
        return service.assign_role(user_id, data.role_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/role", response_model=UserWithRoleResponse)
async def remove_user_role(
    user_id: str,
    service: UserService = Depends(get_service),
):
    """Remove a user's role."""
    try:
        return service.remove_role(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Permission Routes ──────────────────────────────────────────

@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    user_id: str = Query(..., description="User ID to check permission for"),
    data: PermissionCheckRequest = ...,
    service: UserService = Depends(get_service),
):
    """Check if a user has a specific permission."""
    return service.check_permission(user_id, data.permission)


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    service: UserService = Depends(get_service),
):
    """Get all permissions for a user."""
    return {
        "user_id": user_id,
        "permissions": service.get_my_permissions(user_id),
    }
