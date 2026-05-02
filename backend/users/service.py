from typing import Optional, List
from backend.users.manager import UserManager
from backend.users.schema import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    UserWithRoleResponse,
    PermissionCheckResponse,
    Permissions,
)


class UserService:
    """
    Aina-chan's Business Logic Layer for Users & Roles! (◕‿◕✿)

    Handles validation, permission checking, and user management.
    """

    def __init__(self):
        self.manager = UserManager()

    # ─── Lifecycle ────────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize roles collection and role field on users."""
        return self.manager.initialize()

    # ─── Role CRUD ────────────────────────────────────────────

    def create_role(self, data: RoleCreate) -> Optional[RoleResponse]:
        # Check for duplicate name
        existing = self.manager.get_role_by_name(data.name)
        if existing:
            raise ValueError(f"A role named '{data.name}' already exists! Aina-chan can't have duplicates~ (╥﹏╥)")

        result = self.manager.create_role(data.model_dump(exclude_unset=True))
        if not result:
            raise RuntimeError("Aina-chan couldn't create the role~")
        return RoleResponse(**result)

    def get_role(self, role_id: str) -> Optional[RoleResponse]:
        result = self.manager.get_role(role_id)
        if not result:
            return None
        return RoleResponse(**result)

    def update_role(self, role_id: str, data: RoleUpdate) -> Optional[RoleResponse]:
        existing = self.manager.get_role(role_id)
        if not existing:
            raise ValueError(f"Role '{role_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)

        # If name is being changed, check uniqueness
        if "name" in update_data and update_data["name"] != existing.get("name"):
            name_exists = self.manager.get_role_by_name(update_data["name"])
            if name_exists and name_exists["id"] != role_id:
                raise ValueError(f"Another role named '{update_data['name']}' already exists!")

        result = self.manager.update_role(role_id, update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the role~")
        return RoleResponse(**result)

    def delete_role(self, role_id: str, confirm: bool = False) -> bool:
        existing = self.manager.get_role(role_id)
        if not existing:
            raise ValueError(f"Role '{role_id}' not found~")

        if not confirm:
            raise ValueError("⚠️ Aina-chan requires confirmation! This will unset this role for all users! Set confirm=True~")

        # Remove this role from all users first
        try:
            users_result = self.manager.list_users(per_page=500)
            for user in users_result.get("items", []):
                expand = user.get("expand", {})
                user_role = expand.get("role", {})
                if user_role and user_role.get("id") == role_id:
                    self.manager.remove_role(user["id"])
        except Exception:
            pass

        return self.manager.delete_role(role_id)

    def list_roles(self, page: int = 1, per_page: int = 50) -> dict:
        result = self.manager.list_roles(page=page, per_page=per_page)
        return {
            "items": [RoleResponse(**item) for item in result.get("items", [])],
            "page": result.get("page", page),
            "per_page": result.get("perPage", per_page),
            "total_items": result.get("totalItems", 0),
            "total_pages": result.get("totalPages", 0),
        }

    # ─── User Management ──────────────────────────────────────

    def list_users(self, page: int = 1, per_page: int = 50) -> dict:
        result = self.manager.list_users(page=page, per_page=per_page)
        items = []
        for user in result.get("items", []):
            role_data = None
            expand = user.get("expand", {})
            if expand and "role" in expand and expand["role"]:
                role_data = RoleResponse(**expand["role"])

            items.append(UserWithRoleResponse(
                id=user.get("id", ""),
                email=user.get("email", ""),
                username=user.get("username"),
                verified=user.get("verified", False),
                avatar=user.get("avatar"),
                role=role_data,
                created=user.get("created", ""),
                updated=user.get("updated", ""),
            ))

        return {
            "items": items,
            "page": result.get("page", page),
            "per_page": result.get("perPage", per_page),
            "total_items": result.get("totalItems", 0),
            "total_pages": result.get("totalPages", 0),
        }

    def get_user_with_role(self, user_id: str) -> Optional[UserWithRoleResponse]:
        user = self.manager.get_user(user_id)
        if not user:
            return None

        role_data = None
        try:
            user_with_expand = self.manager.client.collections.get_one(
                "users", user_id, query_params={"expand": "role"},
            )
            expand = user_with_expand.get("expand", {})
            if expand and "role" in expand and expand["role"]:
                role_data = RoleResponse(**expand["role"])
        except Exception:
            pass

        return UserWithRoleResponse(
            id=user.get("id", ""),
            email=user.get("email", ""),
            username=user.get("username"),
            verified=user.get("verified", False),
            avatar=user.get("avatar"),
            role=role_data,
            created=user.get("created", ""),
            updated=user.get("updated", ""),
        )

    def assign_role(self, user_id: str, role_id: str) -> Optional[UserWithRoleResponse]:
        # Check user exists
        user = self.manager.get_user(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found~")

        # Check role exists
        role = self.manager.get_role(role_id)
        if not role:
            raise ValueError(f"Role '{role_id}' not found~")

        if not self.manager.assign_role(user_id, role_id):
            raise RuntimeError("Aina-chan couldn't assign the role~")

        return self.get_user_with_role(user_id)

    def remove_role(self, user_id: str) -> Optional[UserWithRoleResponse]:
        user = self.manager.get_user(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found~")

        if not self.manager.remove_role(user_id):
            raise RuntimeError("Aina-chan couldn't remove the role~")

        return self.get_user_with_role(user_id)

    # ─── Permission Checking ──────────────────────────────────

    def check_permission(self, user_id: str, permission: str) -> PermissionCheckResponse:
        allowed = self.manager.check_permission(user_id, permission)
        role = self.manager.get_user_role(user_id)
        role_name = role.get("name") if role else None

        return PermissionCheckResponse(
            permission=permission,
            allowed=allowed,
            role=role_name,
        )

    def get_my_permissions(self, user_id: str) -> dict:
        """Get all permissions for a user."""
        return self.manager.get_all_permissions(user_id)

    # ─── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self.manager.get_stats()
