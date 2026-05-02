from typing import Optional, List
from backend.collections.manager import CollectionManager
from backend.collections.schema import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    FieldAddRequest,
    FieldRemoveRequest,
    SchemaValidationResponse,
)


class CollectionService:
    """
    Aina-chan's Business Logic Layer for Collections! (◕‿◕✿)

    Handles validation, transformation, and complex workflows
    for managing collection definitions.
    """

    def __init__(self):
        self.manager = CollectionManager()

    # ─── CRUD ─────────────────────────────────────────────────

    def create_collection(self, data: CollectionCreate) -> Optional[CollectionResponse]:
        """Create a new collection with validation."""
        # Validate schema first
        field_dicts = [f.model_dump(exclude_unset=True) for f in data.fields]
        issues = self.manager.validate_schema(data.name, field_dicts)
        errors = [i for i in issues if i.startswith("❌")]
        if errors:
            raise ValueError(f"Schema validation failed: {'; '.join(errors)}")

        # Build the full schema
        schema = {
            "name": data.name,
            "type": data.type,
            "listRule": data.listRule,
            "viewRule": data.viewRule,
            "createRule": data.createRule,
            "updateRule": data.updateRule,
            "deleteRule": data.deleteRule,
            "indexes": data.indexes or [],
            "fields": field_dicts,
        }

        # Add timestamps if requested
        if data.addTimestamps:
            has_created = any(f.get("name") == "created" for f in field_dicts)
            has_updated = any(f.get("name") == "updated" for f in field_dicts)
            if not has_created:
                schema["fields"].append({
                    "name": "created", "type": "autodate",
                    "onCreate": True, "onUpdate": False,
                })
            if not has_updated:
                schema["fields"].append({
                    "name": "updated", "type": "autodate",
                    "onCreate": True, "onUpdate": True,
                })

        result = self.manager.create_collection(schema)
        if not result:
            raise RuntimeError("Aina-chan couldn't create the collection~")
        return CollectionResponse(**result)

    def get_collection(self, name_or_id: str) -> Optional[CollectionResponse]:
        result = self.manager.get_collection(name_or_id)
        if not result:
            return None
        return CollectionResponse(**result)

    def list_collections(self, include_system: bool = False) -> List[CollectionResponse]:
        results = self.manager.list_collections(include_system=include_system)
        return [CollectionResponse(**c) for c in results]

    def update_collection_rules(self, name_or_id: str, data: CollectionUpdate) -> Optional[CollectionResponse]:
        existing = self.manager.get_collection(name_or_id)
        if not existing:
            raise ValueError(f"Collection '{name_or_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return CollectionResponse(**existing)

        result = self.manager.update_collection_rules(name_or_id, **update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the collection~")
        return CollectionResponse(**result)

    def delete_collection(self, name_or_id: str, confirm: bool = False) -> bool:
        existing = self.manager.get_collection(name_or_id)
        if not existing:
            raise ValueError(f"Collection '{name_or_id}' not found~")

        if existing.get("system"):
            raise ValueError(f"Collection '{name_or_id}' is a system collection! Aina-chan can't delete it! (╥﹏╥)")

        if not self.manager.delete_collection(name_or_id, confirm=confirm):
            raise RuntimeError("Aina-chan couldn't delete the collection~")
        return True

    # ─── Field Operations ─────────────────────────────────────

    def add_field(self, name_or_id: str, data: FieldAddRequest) -> Optional[CollectionResponse]:
        existing = self.manager.get_collection(name_or_id)
        if not existing:
            raise ValueError(f"Collection '{name_or_id}' not found~")

        field_dict = data.field.model_dump(exclude_unset=True)

        # Check for duplicate field name
        current_names = [f.get("name") for f in existing.get("fields", [])]
        if field_dict.get("name") in current_names:
            raise ValueError(f"Field '{field_dict['name']}' already exists in '{name_or_id}'!")

        result = self.manager.add_field(name_or_id, field_dict)
        if not result:
            raise RuntimeError("Aina-chan couldn't add the field~")
        return CollectionResponse(**result)

    def remove_field(self, name_or_id: str, data: FieldRemoveRequest) -> Optional[CollectionResponse]:
        existing = self.manager.get_collection(name_or_id)
        if not existing:
            raise ValueError(f"Collection '{name_or_id}' not found~")

        result = self.manager.remove_field(name_or_id, data.field_name)
        if not result:
            raise RuntimeError("Aina-chan couldn't remove the field~")
        return CollectionResponse(**result)

    # ─── Duplicate ────────────────────────────────────────────

    def duplicate_collection(self, source_name: str, new_name: str) -> Optional[CollectionResponse]:
        existing = self.manager.get_collection(source_name)
        if not existing:
            raise ValueError(f"Source collection '{source_name}' not found~")

        if self.manager.get_collection(new_name):
            raise ValueError(f"Collection '{new_name}' already exists! Aina-chan can't duplicate~")

        result = self.manager.duplicate_collection(source_name, new_name)
        if not result:
            raise RuntimeError("Aina-chan couldn't duplicate the collection~")
        return CollectionResponse(**result)

    # ─── Validation ───────────────────────────────────────────

    def validate_schema(self, data: CollectionCreate) -> SchemaValidationResponse:
        field_dicts = [f.model_dump(exclude_unset=True) for f in data.fields]
        issues = self.manager.validate_schema(data.name, field_dicts)

        errors = [i for i in issues if i.startswith("❌")]
        warnings = [i for i in issues if i.startswith("⚠️")]

        return SchemaValidationResponse(
            valid=len(errors) == 0,
            warnings=warnings,
            errors=errors,
        )

    # ─── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self.manager.get_collection_stats()
