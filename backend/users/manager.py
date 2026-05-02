import os
import re
from typing import Optional, List
from pocketbase import PocketBase
from backend.util.secrets import SecretsManager


class UserManager:
    """
    Aina-chan's User & Role Manager! (◕‿◕✿)

    Manages:
    - The 'roles' collection (custom)
    - Adding 'role' field to PocketBase's built-in users collection
    - User-role assignments
    - Permission checking

    Fully self-contained module. Can be deleted without breaking
    other modules — though user permissions won't work anymore!
    """

    ROLES_COLLECTION = "roles"

    @property
    def _roles_schema(self) -> dict:
        """The PocketBase schema for the roles collection."""
        return {
            "name": self.ROLES_COLLECTION,
            "type": "base",
            "listRule": "@request.auth.id != ''",
            "viewRule": "@request.auth.id != ''",
            "createRule": "@request.auth.id != ''",
            "updateRule": "@request.auth.id != ''",
            "deleteRule": None,
            "indexes": [
                "CREATE UNIQUE INDEX `idx_roles_name` ON `roles` (`name`)",
                "CREATE INDEX `idx_roles_sort` ON `roles` (`sort_order`)",
            ],
            "fields": [
                {"name": "name", "type": "text", "required": True, "min": 1, "max": 100},
                {"name": "description", "type": "text", "required": False, "max": 500},
                {"name": "permissions", "type": "json", "required": False},
                {"name": "is_staff", "type": "bool", "required": False},
                {"name": "sort_order", "type": "number", "required": False, "noDecimal": True, "min": 0},
                {"name": "custom", "type": "json", "required": False},
                {"name": "created", "type": "autodate", "onCreate": True, "onUpdate": False},
                {"name": "updated", "type": "autodate", "onCreate": True, "onUpdate": True},
            ],
        }

    # ─── Initialization ───────────────────────────────────────

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        if not self.admin_email or not self.admin_password:
            raise ValueError("Aina-chan needs admin email and password! ⊙﹏⊙")
        try:
            self.client.admins.auth_with_password(self.admin_email, self.admin_password)
            self._is_authenticated = True
            return True
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    def _ensure_auth(self) -> bool:
        if not self._is_authenticated:
            return self.authenticate_admin()
        return self._is_authenticated

    # ─── Ensure Roles Collection Exists ───────────────────────

    def ensure_roles_collection(self) -> bool:
        """Create the roles collection if it doesn't exist."""
        if not self._ensure_auth():
            return False
        try:
            try:
                self.client.collections.get_one(self.ROLES_COLLECTION)
                return True
            except Exception:
                self.client.collections.create(self._roles_schema)
                print("Aina-chan created the 'roles' collection! ✨")
                return True
        except Exception as e:
            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False

    # ─── Ensure Role Field on Users Collection ────────────────

    def ensure_role_field_on_users(self) -> bool:
        """
        Add a 'role' relation field to PocketBase's built-in users collection.

        This is needed so each user can have a role assigned.

        ⚠️ This modifies the system 'users' collection, but it's safe —
        Aina-chan only adds a field, never removes existing ones!
        """
        if not self._ensure_auth():
            return False

        try:
            # Get the users collection
            users_col = self.client.collections.get_one("users")

            # Check if 'role' field already exists
            existing_fields = users_col.get("fields", [])
            for field in existing_fields:
                if field.get("name") == "role":
                    return True  # Already exists!

            # Add the role field
            role_field = {
                "name": "role",
                "type": "relation",
                "required": False,
                "collectionId": self.ROLES_COLLECTION,
                "cascadeDelete": False,
                "maxSelect": 1,
            }

            existing_fields.append(role_field)
            self.client.collections.update("users", {"fields": existing_fields})
            print("Aina-chan added 'role' field to users collection! ✨")
            return True

        except Exception as e:
            print(f"Aina-chan couldn't add role field! Error: {e} (╥﹏╥)")
            return False

    def initialize(self) -> bool:
        """
        Initialize everything needed for the users module.

        Creates the roles collection and adds the role field to users.
        """
        if not self._ensure_auth():
            return False
        roles_ok = self.ensure_roles_collection()
        field_ok = self.ensure_role_field_on_users()
        return roles_ok and field_ok

    # ─── Role CRUD ────────────────────────────────────────────

    def create_role(self, data: dict) -> Optional[dict]:
        try:
            return self.client.collections.create(self.ROLES_COLLECTION, data)
        except Exception as e:
            print(f"Aina-chan couldn't create role! Error: {e} (╥﹏╥)")
            return None

    def get_role(self, role_id: str) -> Optional[dict]:
        try:
            return self.client.collections.get_one(self.ROLES_COLLECTION, role_id)
        except Exception:
            return None

    def get_role_by_name(self, name: str) -> Optional[dict]:
        try:
            result = self.client.collections.get_list(
                self.ROLES_COLLECTION,
                query_params={"filter": f'name = "{name}"', "limit": 1},
            )
            items = result.get("items", [])
            return items[0] if items else None
        except Exception:
            return None

    def update_role(self, role_id: str, data: dict) -> Optional[dict]:
        try:
            return self.client.collections.update(self.ROLES_COLLECTION, role_id, data)
        except Exception as e:
            print(f"Aina-chan couldn't update role! Error: {e} (╥﹏╥)")
            return None

    def delete_role(self, role_id: str) -> bool:
        try:
            self.client.collections.delete(self.ROLES_COLLECTION, role_id)
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete role! Error: {e} (╥﹏╥)")
            return False

    def list_roles(self, page: int = 1, per_page: int = 50) -> dict:
        try:
            return self.client.collections.get_list(
                self.ROLES_COLLECTION,
                query_params={"page": page, "perPage": per_page, "sort": "sort_order"},
            )
        except Exception as e:
            print(f"Aina-chan couldn't list roles! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── User-Role Operations ─────────────────────────────────

    def get_user(self, user_id: str) -> Optional[dict]:
        """Get a user from PocketBase's built-in users collection."""
        try:
            return self.client.collections.get_one("users", user_id)
        except Exception:
            return None

    def list_users(self, page: int = 1, per_page: int = 50) -> dict:
        """List users with their role info expanded."""
        try:
            return self.client.collections.get_list(
                "users",
                query_params={
                    "page": page,
                    "perPage": per_page,
                    "sort": "-created",
                    "expand": "role",
                },
            )
        except Exception as e:
            print(f"Aina-chan couldn't list users! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """
        Assign a role to a user.

        Since the 'role' field is a relation, we just set the role_id.
        Updating the role's permissions automatically affects all users!
        """
        try:
            self.client.collections.update("users", user_id, {"role": role_id})
            return True
        except Exception as e:
            print(f"Aina-chan couldn't assign role! Error: {e} (╥﹏╥)")
            return False

    def remove_role(self, user_id: str) -> bool:
        """Remove a user's role."""
        try:
            self.client.collections.update("users", user_id, {"role": None})
            return True
        except Exception as e:
            print(f"Aina-chan couldn't remove role! Error: {e} (╥﹏╥)")
            return False

    def get_user_role(self, user_id: str) -> Optional[dict]:
        """Get the full role object for a user."""
        try:
            user = self.client.collections.get_one(
                "users", user_id, query_params={"expand": "role"},
            )
            if user:
                return user.get("expand", {}).get("role")
            return None
        except Exception:
            return None

    # ─── Permission Checking ──────────────────────────────────

    def check_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: The user's ID
            permission: Permission key like 'pages_create', 'articles_delete'

        Returns:
            True if the user's role has this permission enabled.
        """
        role = self.get_user_role(user_id)
        if not role:
            return False

        permissions = role.get("permissions", {})
        if isinstance(permissions, dict):
            return permissions.get(permission, False)
        return False

    def check_permissions_bulk(self, user_id: str, permissions: List[str]) -> dict:
        """
        Check multiple permissions at once.

        Returns a dict of {permission: bool}.
        """
        role = self.get_user_role(user_id)
        result = {}

        if not role:
            return {p: False for p in permissions}

        role_perms = role.get("permissions", {})
        if not isinstance(role_perms, dict):
            return {p: False for p in permissions}

        for perm in permissions:
            result[perm] = role_perms.get(perm, False)

        return result

    def get_all_permissions(self, user_id: str) -> dict:
        """
        Get all permissions for a user.

        Returns the full permissions dict from their role, or all False.
        """
        role = self.get_user_role(user_id)
        if not role:
            return {}

        perms = role.get("permissions", {})
        return perms if isinstance(perms, dict) else {}

    # ─── Staff / Admin Check ──────────────────────────────────

    def is_staff(self, user_id: str) -> bool:
        """Check if a user has staff status (can access admin)."""
        role = self.get_user_role(user_id)
        if not role:
            return False
        return role.get("is_staff", False)

    def can_access_admin(self, user_id: str) -> bool:
        """Check if a user can access the admin dashboard."""
        role = self.get_user_role(user_id)
        if not role:
            return False
        permissions = role.get("permissions", {})
        if isinstance(permissions, dict):
            return permissions.get("admin_access", False)
        return False

    # ─── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get user and role statistics."""
        total_users = 0
        total_roles = 0

        try:
            user_result = self.client.collections.get_list(
                "users", query_params={"perPage": 1},
            )
            total_users = user_result.get("totalItems", 0)
        except Exception:
            pass

        try:
            role_result = self.client.collections.get_list(
                self.ROLES_COLLECTION, query_params={"perPage": 1},
            )
            total_roles = role_result.get("totalItems", 0)
        except Exception:
            pass

        return {
            "total_users": total_users,
            "total_roles": total_roles,
        }
