from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Field Schemas ──────────────────────────────────────────────

class FieldDefinition(BaseModel):
    """Schema for defining a single field in a collection."""
    name: str = Field(..., description="Field/column name")
    type: str = Field(..., description="Field type: text, number, bool, json, relation, file, select, date, autodate, email, url, editor")
    required: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    pattern: Optional[str] = None  # For text fields
    noDecimal: Optional[bool] = None  # For number fields
    values: Optional[List[str]] = None  # For select fields
    maxSelect: Optional[int] = None  # For select/relation/file
    collectionId: Optional[str] = None  # For relation fields
    cascadeDelete: Optional[bool] = None  # For relation fields
    maxSize: Optional[int] = None  # For file fields
    mimeTypes: Optional[List[str]] = None  # For file fields
    onCreate: Optional[bool] = None  # For autodate fields
    onUpdate: Optional[bool] = None  # For autodate fields


class FieldResponse(BaseModel):
    """Schema for field data returned by PocketBase."""
    id: Optional[str] = None
    name: str
    type: str
    required: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    pattern: Optional[str] = None
    noDecimal: Optional[bool] = None
    values: Optional[List[str]] = None
    maxSelect: Optional[int] = None
    collectionId: Optional[str] = None
    cascadeDelete: Optional[bool] = None
    maxSize: Optional[int] = None
    mimeTypes: Optional[List[str]] = None
    onCreate: Optional[bool] = None
    onUpdate: Optional[bool] = None


# ─── Collection Schemas ─────────────────────────────────────────

class CollectionCreate(BaseModel):
    """Schema for creating a new collection (content type)."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Collection name (table name, e.g., 'projects', 'products'). "
                    "Must start with a letter and contain only lowercase letters, numbers, and underscores.",
        examples=["projects", "products", "testimonials"],
    )
    type: str = Field(
        "base",
        pattern=r"^(base|auth|view)$",
        description="Collection type: 'base' for standard, 'auth' for authentication, 'view' for SQL views",
    )
    fields: List[FieldDefinition] = Field(
        ...,
        min_length=1,
        description="List of field definitions for the collection",
    )
    listRule: Optional[str] = Field(
        "",
        description="List API rule: ''=public, None=admin only, or a filter expression",
    )
    viewRule: Optional[str] = Field(
        "",
        description="View API rule",
    )
    createRule: Optional[str] = Field(
        "@request.auth.id != ''",
        description="Create API rule",
    )
    updateRule: Optional[str] = Field(
        "@request.auth.id != ''",
        description="Update API rule",
    )
    deleteRule: Optional[str] = Field(
        None,
        description="Delete API rule: None=admin only",
    )
    indexes: Optional[List[str]] = Field(
        None,
        description="SQL index statements",
        examples=[["CREATE UNIQUE INDEX `idx_projects_slug` ON `projects` (`slug`)"]],
    )
    addTimestamps: bool = Field(
        True,
        description="Automatically add created/updated autodate fields",
    )


class CollectionUpdate(BaseModel):
    """Schema for updating a collection's rules or metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    listRule: Optional[str] = None
    viewRule: Optional[str] = None
    createRule: Optional[str] = None
    updateRule: Optional[str] = None
    deleteRule: Optional[str] = None


class CollectionResponse(BaseModel):
    """Schema for collection data returned by the API."""
    id: str
    name: str
    type: str = "base"
    system: bool = False
    listRule: Optional[str] = None
    viewRule: Optional[str] = None
    createRule: Optional[str] = None
    updateRule: Optional[str] = None
    deleteRule: Optional[str] = None
    indexes: List[str] = []
    fields: List[FieldResponse] = []
    created: str
    updated: str

    class Config:
        from_attributes = True


class CollectionListResponse(BaseModel):
    """Paginated list of collections."""
    items: List[CollectionResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int


# ─── Field Operations ───────────────────────────────────────────

class FieldAddRequest(BaseModel):
    """Schema for adding a single field to an existing collection."""
    field: FieldDefinition


class FieldRemoveRequest(BaseModel):
    """Schema for removing a field from a collection."""
    field_name: str = Field(..., description="Name of the field to remove")


# ─── Schema Validation Response ─────────────────────────────────

class SchemaValidationResponse(BaseModel):
    """Results of schema validation."""
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []
