from typing import Optional, List
from pocketbase import PocketBase
from util.secrets import SecretsManager


class CollectionSchemaManager:
    """
    Aina-chan's Collection Schema Manager for Anita-CMS! (◕‿◕✿)

    This manages the *collection definitions* in PocketBase itself,
    NOT the records within them!

    Think of it as a mini PocketBase Admin panel:
    - Create new content types (collections) dynamically
    - Update schemas safely
    - Delete collections (⚠️ dangerous!)
    - List and inspect existing collections

    This is what gives Anita-CMS the power to create custom
    content types on the fly, like WordPress custom post types! ✨
    """

    def __init__(
        self,
        pb_url: Optional[str] = None,
        admin_email: Optional[str] = None,
        admin_password: Optional[str] = None,
    ):
        """
        Initialize the schema manager with PocketBase connection.

        Falls back to SecretsManager if credentials aren't provided.
        """
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password

        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    # ─── Authentication ──────────────────────────────────────────

    def authenticate_admin(self) -> bool:
        """
        Authenticate as superadmin for collection management.

        Aina-chan needs this to create/update/delete collections! (｀・ω・´)
        """
        if not self.admin_email or not self.admin_password:
            raise ValueError(
                "Aina-chan needs admin email and password to manage "
                "collection schemas! ⊙﹏⊙"
            )

        try:
            self.client.admins.auth_with_password(
                self.admin_email,
                self.admin_password,
            )
            self._is_authenticated = True
            return True
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    def _ensure_auth(self) -> bool:
        """Internal helper to ensure we're authenticated."""
        if not self._is_authenticated:
            return self.authenticate_admin()
        return self._is_authenticated

    # ─── Field Type Templates ─────────────────────────────────────

    @staticmethod
    def make_text_field(
        name: str,
        required: bool = False,
        min: Optional[int] = None,
        max: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> dict:
        """Create a text field definition."""
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
        """Create a number field definition."""
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
        """Create a boolean field definition."""
        return {"name": name, "type": "bool", "required": required}

    @staticmethod
    def make_json_field(name: str, required: bool = False) -> dict:
        """Create a JSON field definition."""
        return {"name": name, "type": "json", "required": required}

    @staticmethod
    def make_relation_field(
        name: str,
        collection_id: str,
        required: bool = False,
        cascade_delete: bool = False,
        max_select: int = 1,
    ) -> dict:
        """Create a relation field (foreign key)."""
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
        """Create a file/upload field."""
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
        """Create a select/dropdown/enum field."""
        return {
            "name": name,
            "type": "select",
            "required": required,
            "values": values,
            "maxSelect": max_select,
        }

    @staticmethod
    def make_date_field(
        name: str,
        required: bool = False,
    ) -> dict:
        """Create a date field."""
        return {"name": name, "type": "date", "required": required}

    @staticmethod
    def make_autodate_field(
        name: str,
        on_create: bool = True,
        on_update: bool = False,
    ) -> dict:
        """Create an auto-date field (managed by PocketBase)."""
        return {
            "name": name,
            "type": "autodate",
            "onCreate": on_create,
            "onUpdate": on_update,
        }

    @staticmethod
    def make_email_field(name: str, required: bool = False) -> dict:
        """Create an email field."""
        return {"name": name, "type": "email", "required": required}

    @staticmethod
    def make_url_field(name: str, required: bool = False) -> dict:
        """Create a URL field."""
        return {"name": name, "type": "url", "required": required}

    @staticmethod
    def make_editor_field(
        name: str,
        required: bool = False,
        max: Optional[int] = None,
    ) -> dict:
        """Create a rich text editor field (Tiptap)."""
        field = {"name": name, "type": "editor", "required": required}
        if max is not None: 
            field["max"] = max
        return field

    # ─── Default Timestamp Fields ────────────────────────────────

    @staticmethod
    def default_timestamp_fields() -> List[dict]:
        """
        Returns the standard created/updated autodate fields.

        Aina-chan recommends adding these to every collection! ✨
        """
        return [
            {
                "name": "created",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": False,
            },
            {
                "name": "updated",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": True,
            },
        ]

    # ─── Create Collection ───────────────────────────────────────

    def create_collection(
        self,
        name: str,
        fields: List[dict],
        type: str = "base",
        list_rule: Optional[str] = "",
        view_rule: Optional[str] = "",
        create_rule: Optional[str] = "@request.auth.id != ''",
        update_rule: Optional[str] = "@request.auth.id != ''",
        delete_rule: Optional[str] = None,
        indexes: Optional[List[str]] = None,
        add_timestamps: bool = True,
    ) -> Optional[dict]:
        """
        Create a new collection in PocketBase!

        Args:
            name: Collection name (table name, e.g., "posts", "projects")
            fields: List of field definitions
            type: "base", "auth", or "view"
            list_rule: ""=public, None=admin only, "expr"=filter
            view_rule: Same as above
            create_rule: Same as above
            update_rule: Same as above
            delete_rule: Same as above
            indexes: List of SQL index statements
            add_timestamps: Auto-add created/updated fields

        Returns:
            The created collection object, or None on failure.

        Example:
            manager.create_collection(
                name="projects",
                fields=[
                    manager.make_text_field("title", required=True, min=1, max=200),
                    manager.make_text_field("slug", required=True, pattern="^[a-z0-9\\-]+$"),
                    manager.make_editor_field("content"),
                    manager.make_select_field("status", ["draft", "published"]),
                ],
                indexes=[
                    "CREATE UNIQUE INDEX `idx_projects_slug` ON `projects` (`slug`)"
                ],
            )
        """
        if not self._ensure_auth():
            return None

        # Check if collection already exists
        existing = self.get_collection(name)
        if existing:
            print(
                f"Aina-chan says collection '{name}' already exists! "
                f"Use update_collection() to modify it~ (◕‿◕✿)"
            )
            return existing

        # Build the schema payload
        schema_fields = list(fields)
        if add_timestamps:
            schema_fields.extend(self.default_timestamp_fields())

        schema = {
            "name": name,
            "type": type,
            "listRule": list_rule,
            "viewRule": view_rule,
            "createRule": create_rule,
            "updateRule": update_rule,
            "deleteRule": delete_rule,
            "indexes": indexes or [],
            "fields": schema_fields,
        }

        try:
            result = self.client.collections.create(schema)
            print(
                f"Aina-chan created collection '{name}' with "
                f"{len(schema_fields)} fields ✨"
            )
            return result
        except Exception as e:
            print(
                f"Aina-chan couldn't create collection '{name}'! "
                f"Error: {e} (╥﹏╥)"
            )
            return None

    # ─── Get Collection ──────────────────────────────────────────

    def get_collection(self, name_or_id: str) -> Optional[dict]:
        """
        Get a collection by its name or ID.

        Aina-chan will try name first, then ID as fallback~ (◕‿◕✿)
        """
        if not self._ensure_auth():
            return None

        try:
            return self.client.collections.get_one(name_or_id)
        except Exception:
            try:
                # Maybe it's a name, try listing and filtering
                result = self.client.collections.get_list(
                    query_params={"filter": f'name = "{name_or_id}"'},
                )
                items = result.get("items", [])
                if items:
                    return items[0]
            except Exception:
                pass

            print(
                f"Aina-chan couldn't find collection '{name_or_id}'~ (╥﹏╥)"
            )
            return None

    # ─── List Collections ────────────────────────────────────────

    def list_collections(
        self,
        include_system: bool = False,
    ) -> List[dict]:
        """
        List all collections in PocketBase.

        Args:
            include_system: Whether to include system collections
                           (like _pb_users_auth_, _pb_migrations_, etc.)

        Returns:
            List of collection objects.
        """
        if not self._ensure_auth():
            return []

        try:
            result = self.client.collections.get_list(
                query_params={"perPage": 500},
            )
            items = result.get("items", [])

            if not include_system:
                items = [c for c in items if not c.get("system", False)]

            return items
        except Exception as e:
            print(
                f"Aina-chan couldn't list collections! Error: {e} (╥﹏╥)"
            )
            return []

    def get_collection_names(self, include_system: bool = False) -> List[str]:
        """Get just the names of all collections."""
        return [
            c.get("name", "")
            for c in self.list_collections(include_system=include_system)
        ]

    # ─── Update Collection Schema (Safe Way!) ────────────────────

    def update_collection_schema(
        self,
        name_or_id: str,
        new_fields: List[dict],
        preserve_existing: bool = True,
        add_timestamps: bool = True,
    ) -> Optional[dict]:
        """
        Update a collection's schema fields.

        ⚠️ AINA-CHAN'S WARNING:
        This uses the SAFE update flow:
        1. GET the existing collection
        2. Preserve existing field IDs (so data isn't dropped)
        3. Add/update fields
        4. PATCH

        Args:
            name_or_id: Collection name or ID to update
            new_fields: The COMPLETE new list of fields (see below)
            preserve_existing: If True, merge with existing fields
            add_timestamps: Auto-add created/updated fields

        IMPORTANT:
        If preserve_existing is True, the new_fields will be APPENDED
        to the existing fields. If False, new_fields REPLACES everything
        (dangerous! Aina-chan doesn't recommend this!)

        Returns:
            Updated collection object, or None on failure.
        """
        if not self._ensure_auth():
            return None

        # Step 1: GET the existing collection
        existing = self.get_collection(name_or_id)
        if not existing:
            print(
                f"Aina-chan couldn't find collection '{name_or_id}'! "
                f"Can't update~ (╥﹏╥)"
            )
            return None

        try:
            if preserve_existing:
                # Step 2: Keep existing fields with their IDs
                existing_fields = existing.get("fields", [])

                # Build a lookup of existing fields by name
                existing_by_name = {}
                for f in existing_fields:
                    existing_by_name[f.get("name")] = f

                # Merge: update existing, add new
                merged_fields = []
                processed_names = set()

                for new_field in new_fields:
                    field_name = new_field.get("name")
                    existing_field = existing_by_name.get(field_name)

                    if existing_field:
                        # Preserve ID, update properties
                        merged_field = {**existing_field, **new_field}
                        merged_field["id"] = existing_field["id"]
                        merged_fields.append(merged_field)
                    else:
                        # New field, no ID needed (PocketBase assigns one)
                        merged_fields.append(new_field)

                    processed_names.add(field_name)

                # Add back existing fields that weren't in new_fields
                for existing_field in existing_fields:
                    if existing_field.get("name") not in processed_names:
                        # Skip autodate fields if we're adding our own
                        if existing_field.get("type") == "autodate" and add_timestamps:
                            continue
                        merged_fields.append(existing_field)

                fields_to_send = merged_fields

            else:
                # ⚠️ Replace mode — Aina-chan is nervous about this!
                fields_to_send = list(new_fields)
                print(
                    "⚠️ Aina-chan is using REPLACE mode! "
                    "Existing fields without matching names will be DROPPED! "
                    "Data loss may occur! (╥﹏╥)"
                )

            if add_timestamps:
                # Make sure we have created/updated fields
                has_created = any(
                    f.get("name") == "created" and f.get("type") == "autodate"
                    for f in fields_to_send
                )
                has_updated = any(
                    f.get("name") == "updated" and f.get("type") == "autodate"
                    for f in fields_to_send
                )

                if not has_created:
                    fields_to_send.append({
                        "name": "created",
                        "type": "autodate",
                        "onCreate": True,
                        "onUpdate": False,
                    })
                if not has_updated:
                    fields_to_send.append({
                        "name": "updated",
                        "type": "autodate",
                        "onCreate": True,
                        "onUpdate": True,
                    })

            # Step 3: PATCH the collection with the merged fields
            patch_data = {"fields": fields_to_send}

            # Also allow updating rules if they're in the existing collection
            if "listRule" in existing:
                patch_data["listRule"] = existing["listRule"]
            if "viewRule" in existing:
                patch_data["viewRule"] = existing["viewRule"]

            result = self.client.collections.update(
                name_or_id,
                patch_data,
            )
            print(
                f"Aina-chan updated collection '{name_or_id}' schema "
                f"with {len(fields_to_send)} fields ✨"
            )
            return result

        except Exception as e:
            print(
                f"Aina-chan couldn't update collection '{name_or_id}'! "
                f"Error: {e} (╥﹏╥)"
            )
            return None

    # ─── Partial Update (Add Single Field) ───────────────────────

    def add_field(
        self,
        collection_name: str,
        field: dict,
    ) -> Optional[dict]:
        """
        Add a single field to an existing collection.

        This is a convenience wrapper around update_collection_schema
        that Aina-chan made so Senpai doesn't have to pass the full list! ✨

        Args:
            collection_name: Name of the collection to modify
            field: Field definition dict

        Returns:
            Updated collection object, or None on failure.
        """
        return self.update_collection_schema(
            collection_name,
            new_fields=[field],
            preserve_existing=True,
            add_timestamps=False,
        )

    def remove_field(
        self,
        collection_name: str,
        field_name: str,
    ) -> Optional[dict]:
        """
        Remove a field from a collection.

        ⚠️ Aina-chan warns: This will DROP the column and its data!

        Args:
            collection_name: Name of the collection
            field_name: Name of the field to remove

        Returns:
            Updated collection object, or None on failure.
        """
        existing = self.get_collection(collection_name)
        if not existing:
            return None

        # Filter out the field to remove
        remaining_fields = [
            f for f in existing.get("fields", [])
            if f.get("name") != field_name
        ]

        if len(remaining_fields) == len(existing.get("fields", [])):
            print(
                f"Aina-chan couldn't find field '{field_name}' in "
                f"collection '{collection_name}'~ (╥﹏╥)"
            )
            return None

        return self.update_collection_schema(
            collection_name,
            new_fields=remaining_fields,
            preserve_existing=False,
            add_timestamps=False,
        )

    # ─── Delete Collection ───────────────────────────────────────

    def delete_collection(
        self,
        name_or_id: str,
        confirm: bool = False,
    ) -> bool:
        """
        Delete a collection and ALL its data!

        ⚠️ DANGER! This is irreversible!
        Aina-chan requires confirmation for safety~ (╥﹏╥)

        Args:
            name_or_id: Collection name or ID to delete
            confirm: Must be True to actually delete

        Returns:
            True if deleted, False otherwise.
        """
        if not self._ensure_auth():
            return False

        if not confirm:
            print(
                "⚠️ Aina-chan refuses to delete without confirmation! "
                "Set confirm=True if Senpai is absolutely sure~ "
                "This will delete ALL DATA in the collection! (╥﹏╥)"
            )
            return False

        try:
            self.client.collections.delete(name_or_id)
            print(
                f"Aina-chan deleted collection '{name_or_id}' and all its "
                f"data... Senpai please be careful next time~ (╥﹏╥)"
            )
            return True
        except Exception as e:
            print(
                f"Aina-chan couldn't delete collection '{name_or_id}'! "
                f"Error: {e} (╥﹏╥)"
            )
            return False

    # ─── Update Collection Rules ─────────────────────────────────

    def update_collection_rules(
        self,
        name_or_id: str,
        list_rule: Optional[str] = None,
        view_rule: Optional[str] = None,
        create_rule: Optional[str] = None,
        update_rule: Optional[str] = None,
        delete_rule: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Update API rules for a collection without touching fields.

        Aina-chan made this separate so Senpai can change permissions
        without messing with the schema! (◕‿◕✿)

        Rule values:
        - `""` (empty string) = Public access
        - `None` = Admin/Superuser only
        - Any string = PocketBase filter expression
        """
        existing = self.get_collection(name_or_id)
        if not existing:
            return None

        patch_data = {}
        if list_rule is not None: 
            patch_data["listRule"] = list_rule
        if view_rule is not None: 
            patch_data["viewRule"] = view_rule
        if create_rule is not None: 
            patch_data["createRule"] = create_rule
        if update_rule is not None: 
            patch_data["updateRule"] = update_rule
        if delete_rule is not None: 
            patch_data["deleteRule"] = delete_rule

        if not patch_data:
            return existing

        try:
            result = self.client.collections.update(name_or_id, patch_data)
            print(
                f"Aina-chan updated rules for collection '{name_or_id}' ✨"
            )
            return result
        except Exception as e:
            print(
                f"Aina-chan couldn't update rules! Error: {e} (╥﹏╥)"
            )
            return None

    # ─── Duplicate Collection ────────────────────────────────────

    def duplicate_collection(
        self,
        source_name: str,
        new_name: str,
        copy_data: bool = False,
    ) -> Optional[dict]:
        """
        Duplicate a collection's schema to create a new collection.

        Args:
            source_name: Name of the collection to copy
            new_name: Name for the new collection
            copy_data: Not yet implemented (PocketBase doesn't support
                      bulk record copying natively)

        Returns:
            The new collection object, or None on failure.
        """
        source = self.get_collection(source_name)
        if not source:
            return None

        # Copy the schema (exclude system fields, ID, name)
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

        try:
            result = self.client.collections.create(new_schema)
            print(
                f"Aina-chan duplicated '{source_name}' → '{new_name}' ✨"
            )
            return result
        except Exception as e:
            print(
                f"Aina-chan couldn't duplicate collection! Error: {e} (╥﹏╥)"
            )
            return None

    # ─── Schema Validation ───────────────────────────────────────

    def validate_schema(
        self,
        name: str,
        fields: List[dict],
    ) -> List[str]:
        """
        Validate a collection schema before creating it.

        Aina-chan will check for common issues! (｀・ω・´)

        Returns:
            List of warning/error messages (empty = all good!)
        """
        warnings = []

        if not name or not name.strip():
            warnings.append("❌ Collection name cannot be empty!")

        if not name.isidentifier() and not name.replace("_", "").isalnum():
            warnings.append(
                "⚠️ Collection name should be alphanumeric with underscores "
                f"(got '{name}')"
            )

        if not fields:
            warnings.append("❌ Collection must have at least one field!")
            return warnings

        # Check for reserved field names
        reserved = {"id", "created", "updated", "collectionId"}
        field_names = [f.get("name") for f in fields if f.get("name")]

        for name in field_names:
            if name in reserved:
                warnings.append(
                    f"⚠️ Field name '{name}' is reserved by PocketBase "
                    f"and may cause issues!"
                )

        # Check for duplicate field names
        duplicates = [
            name for name in field_names
            if field_names.count(name) > 1
        ]
        if duplicates:
            warnings.append(
                f"❌ Duplicate field names found: {set(duplicates)}"
            )

        # Check for missing required properties
        for field in fields:
            if "name" not in field:
                warnings.append("❌ A field is missing the 'name' property!")
            if "type" not in field:
                warnings.append(
                    f"❌ Field '{field.get('name', '?')}' is missing "
                    f"the 'type' property!"
                )

        return warnings

    # ─── Pretty Print ────────────────────────────────────────────

    def print_collections(self, include_system: bool = False) -> None:
        """Print a nice overview of all collections."""
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

            # Determine access badge
            if list_rule is None:
                access = "🔒 Admin"
            elif list_rule == "":
                access = "🌐 Public"
            else:
                access = "🔑 Auth"

            print(
                f"\n  📂 {name}{system}"
                f"  ({col_type}, {len(fields)} fields, {access})"
            )

            # Print fields
            for f in fields:
                f_name = f.get("name", "?")
                f_type = f.get("type", "?")
                f_req = " *" if f.get("required") else ""
                f_id = f.get("id", "")[:8] + ".." if f.get("id") else ""

                # Special field indicators
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