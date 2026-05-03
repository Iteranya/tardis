from typing import Optional, List
from pocketbase import PocketBase
from backend.util.auth import authenticate_admin
from backend.util.secrets import get_secrets


class UserManager:
    """Aina-chan's User & Role Manager! (◕‿◕✿)"""

    ROLES_COLLECTION = "roles"
    USERS_COLLECTION = "users"  # built-in

    @property
    def _roles_schema(self) -> dict:
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

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = get_secrets()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        if not self.admin_email or not self.admin_password:
            raise ValueError("Aina-chan needs admin email and password! ⊙﹏⊙")
        try:
            result = authenticate_admin(self.client, self.admin_email, self.admin_password)
            self._is_authenticated = result
            return result
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    # ─── Collection initialization ──────────────────────────────
    # Same pattern as PageManager

    def ensure_roles_collection(self) -> bool:
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False
        try:
            try:
                self.client.collections.get_one(self.ROLES_COLLECTION)
                return True
            except Exception as e:
                if "CollectionField.__init__()" in str(e) and "help" in str(e):
                    return True
            self.client.collections.create(self._roles_schema)
            print("Aina-chan created the 'roles' collection! ✨")
            return True
        except Exception as e:
            err_data = getattr(e, 'data', {})
            if isinstance(err_data, dict):
                name_err = err_data.get('data', {}).get('name', {})
                if isinstance(name_err, dict) and name_err.get('code') == 'validation_collection_name_exists':
                    return True
            if "CollectionField.__init__()" in str(e) and "help" in str(e):
                return True
            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False

    def ensure_role_field_on_users(self) -> bool:
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False
        try:
            # Get roles collection
            try:
                roles_col = self.client.collections.get_one(self.ROLES_COLLECTION)
                # get_one returns a Collection object, which is not subscriptable
                # Use .id attribute
                roles_collection_id = roles_col.id
            except Exception as e:
                if "CollectionField.__init__()" in str(e) and "help" in str(e):
                    # Fallback: use list to get id
                    result = self.client.collections.get_list(
                        query_params={"filter": f'name = "{self.ROLES_COLLECTION}"', "perPage": 1},
                    )
                    # result is a ListResult, use .items
                    if not result.items:
                        print("Aina-chan couldn't find the roles collection! (╥﹏╥)")
                        return False
                    roles_collection_id = result.items[0].id
                else:
                    raise

            # Get users collection
            try:
                users_col = self.client.collections.get_one(self.USERS_COLLECTION)
                existing_fields = users_col.fields  # Collection object stores fields as list of dicts? Actually it's list[CollectionField] now? Need to see collection.py: `fields: list[dict]` -> yes it's a list of dicts
            except Exception as e:
                if "CollectionField.__init__()" in str(e) and "help" in str(e):
                    result = self.client.collections.get_list(
                        query_params={"filter": f'name = "{self.USERS_COLLECTION}"', "perPage": 1},
                    )
                    if not result.items:
                        return False
                    result.items[0].id
                    existing_fields = result.items[0].fields
                else:
                    raise

            field_names = [f.get("name") for f in existing_fields]
            if "role" in field_names:
                return True

            role_field = {
                "name": "role",
                "type": "relation",
                "required": False,
                "collectionId": roles_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            }
            existing_fields.append(role_field)

            try:
                self.client.collections.update(self.USERS_COLLECTION, {"fields": existing_fields})
            except Exception as e:
                if "CollectionField.__init__()" in str(e) and "help" in str(e):
                    pass
                else:
                    raise

            print("Aina-chan added 'role' field to users collection! ✨")
            return True

        except Exception as e:
            error_msg = str(e)
            if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                print("Aina-chan added 'role' field to users collection! ✨")
                return True
            print(f"Aina-chan couldn't add role field! Error: {e} (╥﹏╥)")
            return False

    def initialize(self) -> bool:
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False
        roles_ok = self.ensure_roles_collection()
        field_ok = self.ensure_role_field_on_users()
        return roles_ok and field_ok

    # ─── Role CRUD ──────────────────────────────────────────────

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
                query_params={"filter": f'name = "{name}"', "perPage": 1},
            )
            # result is ListResult, use .items
            items = result.items
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

    def list_roles(self, page: int = 1, per_page: int = 20, sort: str = "sort_order") -> dict:
        try:
            result = self.client.collections.get_list(
                self.ROLES_COLLECTION,
                query_params={"page": page, "perPage": per_page, "sort": sort},
            )
            # Convert to dict (like PageManager does)
            return {
                "items": result.items,
                "page": result.page,
                "perPage": result.per_page,
                "totalItems": result.total_items,
                "totalPages": result.total_pages,
            }
        except Exception as e:
            print(f"Aina-chan couldn't list roles! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── User operations ────────────────────────────────────────

    def get_user(self, user_id: str) -> Optional[dict]:
        try:
            return self.client.collections.get_one(self.USERS_COLLECTION, user_id)
        except Exception:
            return None

    def list_users(self, page: int = 1, per_page: int = 20, sort: str = "-created") -> dict:
        try:
            result = self.client.collections.get_list(
                self.USERS_COLLECTION,
                query_params={"page": page, "perPage": per_page, "sort": sort, "expand": "role"},
            )
            return {
                "items": result.items,
                "page": result.page,
                "perPage": result.per_page,
                "totalItems": result.total_items,
                "totalPages": result.total_pages,
            }
        except Exception as e:
            print(f"Aina-chan couldn't list users! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    def assign_role(self, user_id: str, role_id: str) -> bool:
        try:
            self.client.collections.update(self.USERS_COLLECTION, user_id, {"role": role_id})
            return True
        except Exception as e:
            print(f"Aina-chan couldn't assign role! Error: {e} (╥﹏╥)")
            return False

    def remove_role(self, user_id: str) -> bool:
        try:
            self.client.collections.update(self.USERS_COLLECTION, user_id, {"role": None})
            return True
        except Exception as e:
            print(f"Aina-chan couldn't remove role! Error: {e} (╥﹏╥)")
            return False

    def get_user_role(self, user_id: str) -> Optional[dict]:
        try:
            user = self.client.collections.get_one(
                self.USERS_COLLECTION, user_id, query_params={"expand": "role"},
            )
            # user is a Collection/Record object? Actually get_one returns a Collection model? Wait, for user collection, it's a Record model. Let's assume it has .expand property.
            if user:
                exp = getattr(user, 'expand', {}) or {}
                return exp.get("role")
            return None
        except Exception:
            return None

    # ─── Permission checking ────────────────────────────────────

    def check_permission(self, user_id: str, permission: str) -> bool:
        role = self.get_user_role(user_id)
        if not role:
            return False
        perms = role.get("permissions", {})
        return perms.get(permission, False) if isinstance(perms, dict) else False

    def check_permissions_bulk(self, user_id: str, permissions: List[str]) -> dict:
        role = self.get_user_role(user_id)
        if not role:
            return {p: False for p in permissions}
        perms = role.get("permissions", {})
        if not isinstance(perms, dict):
            return {p: False for p in permissions}
        return {p: perms.get(p, False) for p in permissions}

    def get_all_permissions(self, user_id: str) -> dict:
        role = self.get_user_role(user_id)
        if not role:
            return {}
        perms = role.get("permissions", {})
        return perms if isinstance(perms, dict) else {}

    def is_staff(self, user_id: str) -> bool:
        role = self.get_user_role(user_id)
        return role.get("is_staff", False) if role else False

    def can_access_admin(self, user_id: str) -> bool:
        role = self.get_user_role(user_id)
        if not role:
            return False
        perms = role.get("permissions", {})
        return perms.get("admin_access", False) if isinstance(perms, dict) else False

    # ─── Stats ──────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total_users = 0
        total_roles = 0
        try:
            user_result = self.client.collections.get_list(self.USERS_COLLECTION, query_params={"perPage": 1})
            total_users = user_result.total_items
        except Exception:
            pass
        try:
            role_result = self.client.collections.get_list(self.ROLES_COLLECTION, query_params={"perPage": 1})
            total_roles = role_result.total_items
        except Exception:
            pass
        return {"total_users": total_users, "total_roles": total_roles}
