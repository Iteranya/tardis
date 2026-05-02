import re
from typing import Optional, List
from pocketbase import PocketBase
from backend.util.auth import authenticate_admin
from backend.util.secrets import SecretsManager


class CollectionManager:
    """
    Aina-chan's Collection Manager! (◕‿◕✿)

    Manages collection *definitions* in PocketBase — not records!
    This is the engine behind Anita-CMS's custom content types.

    Fully self-contained module. Can be deleted without affecting
    other modules like pages, articles, or sites!
    """

    # ─── Initialization ───────────────────────────────────────

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        """Authenticate as superadmin for collection management."""
        if not self.admin_email or not self.admin_password:
            raise ValueError(
                "Aina-chan needs admin email and password to manage collections! ⊙﹏⊙"
            )

        try:
            result = authenticate_admin(
                self.client,
                self.admin_email,
                self.admin_password,
            )
            self._is_authenticated = result
            return result
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    def _ensure_auth(self) -> bool:
        """Internal helper to ensure we're authenticated."""
        if not self._is_authenticated:
            return self.authenticate_admin()
        return self._is_authenticated

    # ─── Field Type Helpers ───────────────────────────────────

    @staticmethod
    def make_text_field(
        name: str,
        required: bool = False,
        min: Optional[int] = None,
        max: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> dict:
        field = {"name": name, "type": "text", "required": required}
        if min is not None: 
            field["min"] = min
        if max is not None: 
            field["max"] = max
        if pattern: 
            field["pattern"] = pattern
        return field

    @staticmethod
    def make_number_field(
        name: str,
        required: bool = False,
        min: Optional[float] = None,
        max: Optional[float] = None,
        no_decimal: bool = False,
    ) -> dict:
        field = {"name": name, "type": "number", "required": required}
        if min is not None: 
            field["min"] = min
        if max is not None: 
            field["max"] = max
        if no_decimal: 
            field["noDecimal"] = True
        return field

    @staticmethod
    def make_bool_field(name: str, required: bool = False) -> dict:
        return {"name": name, "type": "bool", "required": required}

    @staticmethod
    def make_json_field(name: str, required: bool = False) -> dict:
        return {"name": name, "type": "json", "required": required}

    @staticmethod
    def make_relation_field(
        name: str,
        collection_id: str,
        required: bool = False,
        cascade_delete: bool = False,
        max_select: int = 1,
    ) -> dict:
        return {
            "name": name,
            "type": "relation",
            "required": required,
            "collectionId": collection_id,
            "cascadeDelete": cascade_delete,
            "maxSelect": max_select,
        }

    @staticmethod
    def make_file_field(
        name: str,
        required: bool = False,
        max_select: int = 1,
        max_size: int = 5_242_880,
        mime_types: Optional[List[str]] = None,
    ) -> dict:
        return {
            "name": name,
            "type": "file",
            "required": required,
            "maxSelect": max_select,
            "maxSize": max_size,
            "mimeTypes": mime_types or ["image/jpeg", "image/png", "image/webp"],
        }

    @staticmethod
    def make_select_field(
        name: str,
        values: List[str],
        required: bool = False,
        max_select: int = 1,
    ) -> dict:
        return {
            "name": name,
            "type": "select",
            "required": required,
            "values": values,
            "maxSelect": max_select,
        }

    @staticmethod
    def make_date_field(name: str, required: bool = False) -> dict:
        return {"name": name, "type": "date", "required": required}

    @staticmethod
    def make_autodate_field(
        name: str,
        on_create: bool = True,
        on_update: bool = False,
    ) -> dict:
        return {
            "name": name,
            "type": "autodate",
            "onCreate": on_create,
            "onUpdate": on_update,
        }

    @staticmethod
    def make_email_field(name: str, required: bool = False) -> dict:
        return {"name": name, "type": "email", "required": required}

    @staticmethod
    def make_url_field(name: str, required: bool = False) -> dict:
        return {"name": name, "type": "url", "required": required}

    @staticmethod
    def make_editor_field(name: str, required: bool = False, max: Optional[int] = None) -> dict:
        field = {"name": name, "type": "editor", "required": required}
        if max is not None: 
            field["max"] = max
        return field

    # ─── CRUD: Create ─────────────────────────────────────────

    def create_collection(self, schema: dict) -> Optional[dict]:
        """
        Create a new collection in PocketBase.

        Args:
            schema: Full collection schema dict with name, fields, rules, indexes.

        Returns:
            The created collection object, or None on failure.
        """
        if not self._ensure_auth():
            return None

        # Check if already exists
        existing = self.get_collection(schema.get("name", ""))
        if existing:
            print(f"Aina-chan says collection '{schema['name']}' already exists! (◕‿◕✿)")
            return existing

        try:
            result = self.client.collections.create(schema)
            field_count = len(schema.get("fields", []))
            print(f"Aina-chan created collection '{schema['name']}' with {field_count} fields ✨")
            return result
        except Exception as e:
            print(f"Aina-chan couldn't create collection! Error: {e} (╥﹏╥)")
            return None

    # ─── CRUD: Read ───────────────────────────────────────────

    def get_collection(self, name_or_id: str) -> Optional[dict]:
        """Get a collection by its name or ID."""
        if not self._ensure_auth():
            return None

        try:
            return self.client.collections.get_one(name_or_id)
        except Exception:
            # Try filtering by name
            try:
                result = self.client.collections.get_list(
                    query_params={"filter": f'name = "{name_or_id}"', "perPage": 1},
                )
                items = result.get("items", [])
                return items[0] if items else None
            except Exception:
                return None

    def list_collections(self, include_system: bool = False) -> List[dict]:
        """List all collections in PocketBase."""
        if not self._ensure_auth():
            return []

        try:
            result = self.client.collections.get_list(query_params={"perPage": 500})
            items = result.get("items", [])
            if not include_system:
                items = [c for c in items if not c.get("system", False)]
            return items
        except Exception as e:
            print(f"Aina-chan couldn't list collections! Error: {e} (╥﹏╥)")
            return []

    def get_collection_names(self, include_system: bool = False) -> List[str]:
        """Get just the names of all collections."""
        return [c.get("name", "") for c in self.list_collections(include_system=include_system)]

    # ─── CRUD: Update Schema ──────────────────────────────────

    def update_collection_schema(
        self,
        name_or_id: str,
        new_fields: List[dict],
        preserve_existing: bool = True,
        add_timestamps: bool = True,
    ) -> Optional[dict]:
        """
        Update a collection's field schema safely.

        Uses the SAFE flow: GET → merge field IDs → PATCH.
        This prevents accidental data loss!

        Args:
            name_or_id: Collection name or ID
            new_fields: The new/updated list of field definitions
            preserve_existing: If True, merge with existing fields (append/update)
                              If False, replace entirely (⚠️ dangerous!)
            add_timestamps: Auto-add created/updated fields if missing
        """
        if not self._ensure_auth():
            return None

        existing = self.get_collection(name_or_id)
        if not existing:
            print(f"Aina-chan couldn't find collection '{name_or_id}'! (╥﹏╥)")
            return None

        try:
            if preserve_existing:
                existing_fields = existing.get("fields", [])
                existing_by_name = {f.get("name"): f for f in existing_fields}

                merged_fields = []
                processed_names = set()

                for new_field in new_fields:
                    field_name = new_field.get("name")
                    existing_field = existing_by_name.get(field_name)

                    if existing_field:
                        # Preserve ID, update properties
                        merged = {**existing_field, **new_field}
                        merged["id"] = existing_field.get("id")
                        merged_fields.append(merged)
                    else:
                        merged_fields.append(new_field)

                    processed_names.add(field_name)

                # Add back existing fields that weren't in the update
                for existing_field in existing_fields:
                    name = existing_field.get("name")
                    if name not in processed_names:
                        # Skip old autodate if we're adding fresh ones
                        if existing_field.get("type") == "autodate" and add_timestamps:
                            continue
                        merged_fields.append(existing_field)

                fields_to_send = merged_fields
            else:
                fields_to_send = list(new_fields)
                print("⚠️ Aina-chan is using REPLACE mode! Data loss possible! (╥﹏╥)")

            # Ensure timestamp fields
            if add_timestamps:
                has_created = any(
                    f.get("name") == "created" and f.get("type") == "autodate"
                    for f in fields_to_send
                )
                has_updated = any(
                    f.get("name") == "updated" and f.get("type") == "autodate"
                    for f in fields_to_send
                )
                if not has_created:
                    fields_to_send.append({"name": "created", "type": "autodate", "onCreate": True, "onUpdate": False})
                if not has_updated:
                    fields_to_send.append({"name": "updated", "type": "autodate", "onCreate": True, "onUpdate": True})

            result = self.client.collections.update(name_or_id, {"fields": fields_to_send})
            print(f"Aina-chan updated schema for '{name_or_id}' ✨")
            return result

        except Exception as e:
            print(f"Aina-chan couldn't update collection! Error: {e} (╥﹏╥)")
            return None

    # ─── Field Operations ─────────────────────────────────────

    def add_field(self, collection_name: str, field: dict) -> Optional[dict]:
        """Add a single field to an existing collection."""
        return self.update_collection_schema(
            collection_name, [field], preserve_existing=True, add_timestamps=False,
        )

    def remove_field(self, collection_name: str, field_name: str) -> Optional[dict]:
        """
        Remove a field from a collection.

        ⚠️ Aina-chan warns: This drops the column and its data!
        """
        existing = self.get_collection(collection_name)
        if not existing:
            return None

        remaining = [f for f in existing.get("fields", []) if f.get("name") != field_name]

        if len(remaining) == len(existing.get("fields", [])):
            print(f"Aina-chan couldn't find field '{field_name}' in '{collection_name}'~ (╥﹏╥)")
            return None

        return self.update_collection_schema(
            collection_name, remaining, preserve_existing=False, add_timestamps=False,
        )

    # ─── CRUD: Update Rules ───────────────────────────────────

    def update_collection_rules(
        self,
        name_or_id: str,
        list_rule: Optional[str] = None,
        view_rule: Optional[str] = None,
        create_rule: Optional[str] = None,
        update_rule: Optional[str] = None,
        delete_rule: Optional[str] = None,
    ) -> Optional[dict]:
        """Update API rules for a collection without touching fields."""
        existing = self.get_collection(name_or_id)
        if not existing:
            return None

        patch = {}
        if list_rule is not None: 
            patch["listRule"] = list_rule
        if view_rule is not None: 
            patch["viewRule"] = view_rule
        if create_rule is not None: 
            patch["createRule"] = create_rule
        if update_rule is not None: 
            patch["updateRule"] = update_rule
        if delete_rule is not None: 
            patch["deleteRule"] = delete_rule

        if not patch:
            return existing

        try:
            result = self.client.collections.update(name_or_id, patch)
            print(f"Aina-chan updated rules for '{name_or_id}' ✨")
            return result
        except Exception as e:
            print(f"Aina-chan couldn't update rules! Error: {e} (╥﹏╥)")
            return None

    # ─── CRUD: Delete ─────────────────────────────────────────

    def delete_collection(self, name_or_id: str, confirm: bool = False) -> bool:
        """
        Delete a collection and ALL its data!

        ⚠️ DANGER! Irreversible! Aina-chan requires confirmation!
        """
        if not self._ensure_auth():
            return False

        if not confirm:
            print("⚠️ Aina-chan refuses! Set confirm=True to delete. This destroys ALL data! (╥﹏╥)")
            return False

        try:
            self.client.collections.delete(name_or_id)
            print(f"Aina-chan deleted collection '{name_or_id}'... (╥﹏╥)")
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete collection! Error: {e} (╥﹏╥)")
            return False

    # ─── Duplicate ────────────────────────────────────────────

    def duplicate_collection(self, source_name: str, new_name: str) -> Optional[dict]:
        """Duplicate a collection's schema to create a new one."""
        source = self.get_collection(source_name)
        if not source:
            return None

        new_schema = {
            "name": new_name,
            "type": source.get("type", "base"),
            "listRule": source.get("listRule", ""),
            "viewRule": source.get("viewRule", ""),
            "createRule": source.get("createRule", "@request.auth.id != ''"),
            "updateRule": source.get("updateRule", "@request.auth.id != ''"),
            "deleteRule": source.get("deleteRule", None),
            "indexes": source.get("indexes", []),
            "fields": source.get("fields", []),
        }

        return self.create_collection(new_schema)

    # ─── Schema Validation ────────────────────────────────────

    def validate_schema(self, name: str, fields: List[dict]) -> List[str]:
        """
        Validate a collection schema before creating it.

        Returns a list of warning/error messages (empty = all good!).
        """
        issues = []

        if not name or not name.strip():
            issues.append("❌ Collection name cannot be empty!")

        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            issues.append(f"❌ Collection name '{name}' must start with a letter and contain only lowercase letters, numbers, and underscores.")

        if not fields:
            issues.append("❌ Collection must have at least one field!")
            return issues

        # Check reserved names
        reserved = {"id", "created", "updated", "collectionId", "expand"}
        field_names = [f.get("name") for f in fields if f.get("name")]

        for fname in field_names:
            if fname in reserved:
                issues.append(f"⚠️ Field name '{fname}' is reserved by PocketBase!")

        # Check duplicates
        duplicates = [n for n in field_names if field_names.count(n) > 1]
        if duplicates:
            issues.append(f"❌ Duplicate field names: {set(duplicates)}")

        # Check missing props
        for field in fields:
            if "name" not in field:
                issues.append("❌ A field is missing the 'name' property!")
            if "type" not in field:
                issues.append(f"❌ Field '{field.get('name', '?')}' is missing the 'type' property!")

        return issues

    # ─── Utility ──────────────────────────────────────────────

    def is_system_collection(self, name_or_id: str) -> bool:
        """Check if a collection is a system collection."""
        col = self.get_collection(name_or_id)
        return col.get("system", False) if col else False

    def get_collection_field_names(self, name_or_id: str) -> List[str]:
        """Get the field names of a collection."""
        col = self.get_collection(name_or_id)
        if not col:
            return []
        return [f.get("name", "") for f in col.get("fields", [])]

    def get_collection_stats(self) -> dict:
        """Get stats about all custom collections."""
        collections = self.list_collections(include_system=False)
        total_fields = sum(len(c.get("fields", [])) for c in collections)

        return {
            "total_collections": len(collections),
            "total_fields": total_fields,
            "collections": [
                {
                    "name": c.get("name"),
                    "type": c.get("type"),
                    "field_count": len(c.get("fields", [])),
                    "system": c.get("system", False),
                }
                for c in collections
            ],
        }

    # ─── Pretty Print ─────────────────────────────────────────

    def print_collections(self, include_system: bool = False) -> None:
        """Print a nice overview of all collections to console."""
        collections = self.list_collections(include_system=include_system)

        print("\n" + "=" * 60)
        print("  📚  Aina-chan's Collection Overview")
        print("=" * 60)

        for col in collections:
            name = col.get("name", "?")
            col_type = col.get("type", "base")
            fields = col.get("fields", [])
            system = " ⚙️" if col.get("system") else ""
            list_rule = col.get("listRule", "null")

            if list_rule is None:
                access = "🔒 Admin"
            elif list_rule == "":
                access = "🌐 Public"
            else:
                access = "🔑 Auth"

            print(f"\n  📂 {name}{system}  ({col_type}, {len(fields)} fields, {access})")

            for f in fields:
                f_name = f.get("name", "?")
                f_type = f.get("type", "?")
                f_req = " *" if f.get("required") else ""

                extras = ""
                if f_type == "autodate": 
                    extras = " 📅"
                elif f_type == "file": 
                    extras = " 🖼️"
                elif f_type == "relation": 
                    extras = " 🔗"
                elif f_type == "editor": 
                    extras = " 📝"

                print(f"     ├─ {f_name}: {f_type}{f_req}{extras}")

        print("=" * 60 + "\n")
