from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ─── Permission Models ──────────────────────────────────────────

class Permissions(BaseModel):
    """
    Aina-chan's permission flags! (◕‿◕✿)

    Each permission is a boolean. True = allowed, False = denied.
    If a field is missing, it defaults to False (denied).
    """
    # Pages
    pages_view: bool = False
    pages_create: bool = False
    pages_edit: bool = False
    pages_delete: bool = False

    # Articles
    articles_view: bool = False
    articles_create: bool = False
    articles_edit: bool = False
    articles_delete: bool = False
    articles_publish: bool = False

    # Sites
    sites_view: bool = False
    sites_create: bool = False
    sites_edit: bool = False
    sites_delete: bool = False
    sites_publish: bool = False

    # Collections (schema management)
    collections_view: bool = False
    collections_create: bool = False
    collections_edit: bool = False
    collections_delete: bool = False

    # Storage
    storage_upload: bool = False
    storage_delete: bool = False

    # Users & Roles
    users_view: bool = False
    users_manage: bool = False
    roles_view: bool = False
    roles_manage: bool = False

    # Settings
    settings_view: bool = False
    settings_manage: bool = False

    # Admin dashboard access
    admin_access: bool = False


class PermissionOverride(BaseModel):
    """Individual permission override (for flexibility)."""
    permission: str = Field(..., description="Permission key, e.g. 'pages_create'")
    value: bool = Field(..., description="True = allow, False = deny")


# ─── Role Schemas ───────────────────────────────────────────────

class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Role name (e.g., 'Admin', 'Editor', 'Viewer')",
        examples=["Editor", "Moderator", "Contributor"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of what this role can do",
        examples=["Can create and edit content, but not manage users"],
    )
    permissions: Permissions = Field(
        default_factory=Permissions,
        description="Permission flags for this role",
    )
    is_staff: bool = Field(
        False,
        description="Staff status — can access admin panel",
    )
    sort_order: int = Field(
        0,
        ge=0,
        description="Sorting priority (lower = higher in lists)",
    )
    custom: Optional[Dict[str, Any]] = Field(
        None,
        description="Extendable key-value store",
        examples=[{"color": "#ff0000", "icon": "shield"}],
    )


class RoleUpdate(BaseModel):
    """Schema for updating a role (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[Permissions] = None
    is_staff: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    custom: Optional[Dict[str, Any]] = None


class RoleResponse(BaseModel):
    """Schema for role data returned by the API."""
    id: str
    name: str
    description: Optional[str] = None
    permissions: Permissions = Permissions()
    is_staff: bool = False
    sort_order: int = 0
    custom: Optional[Dict[str, Any]] = None
    created: str
    updated: str

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Paginated list of roles."""
    items: List[RoleResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int


# ─── User-Role Schemas ──────────────────────────────────────────

class UserRoleAssignment(BaseModel):
    """Schema for assigning a role to a user."""
    role_id: str = Field(..., description="The role ID to assign")
    # The user is identified by the user_id in the URL path


class UserWithRoleResponse(BaseModel):
    """
    Schema for user data including their role.

    Aina-chan returns the full role object so Senpai doesn't
    need a second API call! (◕‿◕✿)
    """
    id: str
    email: str
    username: Optional[str] = None
    verified: bool = False
    avatar: Optional[str] = None
    role: Optional[RoleResponse] = None
    created: str
    updated: str


class UserListResponse(BaseModel):
    """Paginated list of users with their roles."""
    items: List[UserWithRoleResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int


# ─── Permission Check ───────────────────────────────────────────

class PermissionCheckRequest(BaseModel):
    """Request to check if current user has a specific permission."""
    permission: str = Field(
        ...,
        description="Permission to check, e.g. 'pages_create', 'articles_delete'",
    )


class PermissionCheckResponse(BaseModel):
    """Result of a permission check."""
    permission: str
    allowed: bool
    role: Optional[str] = None
