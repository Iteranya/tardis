from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

class Collection:
    # --- Core ---
    title: str                                   # Text, required, min:1, max:200
    slug: str                                    # Text, required, unique URL path
    desc: Optional[str] = None                   # Text, optional description

    # --- Classification ---
    labels: Optional[List[str]] = None           # Json or select (if predefined)
    tags: Optional[List[str]] = None             # Json or select (if predefined)
    security: Optional[List[str]] = None         # List of Security Rules, None means superuser only

    # --- Behavior ---
    sort_order: int = 0                          # Number, integer for manual ordering

    # --- Extensibility ---
    custom: Optional[Dict[str, Any]] = None      # Json, for any extra needs



# ─── Create Schema ───

class CollectionCreate(BaseModel):
    """
    Aina-chan's schema for creating a new Collection entry! (◕‿◕✿)

    Collections are flexible containers that can represent anything —
    categories, portfolios, projects, or custom content types!
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display title for the collection",
        examples=["My Awesome Collection", "Character Gallery"],
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9\-]+$",
        description="URL-friendly identifier (lowercase, hyphens only)",
        examples=["my-awesome-collection", "character-gallery"],
    )

    desc: Optional[str] = Field(
        None,
        max_length=1000,
        description="Brief description of what this collection contains",
        examples=["A collection of all my favorite characters~"],
    )

    labels: Optional[List[str]] = Field(
        None,
        description="Categorization labels for filtering",
        examples=[["featured", "popular", "new"]],
    )

    tags: Optional[List[str]] = Field(
        None,
        description="Free-form tags for search and grouping",
        examples=[["anime", "game", "art"]],
    )

    security: Optional[List[str]] = Field(
        None,
        description=(
            "List of security rules for access control.\n"
            "- `None` means superuser only (highest restriction)\n"
            "- `[]` (empty list) means public\n"
            "- `[\"@request.auth.id != ''\"]` means any authenticated user\n"
            "- `[\"author = @request.auth.id\"]` means owner only"
        ),
        examples=[None, [], ["@request.auth.id != ''"]],
    )

    sort_order: int = Field(
        0,
        ge=0,
        description="Sorting priority (lower = appears first)",
        examples=[0, 1, 10],
    )

    custom: Optional[Dict[str, Any]] = Field(
        None,
        description="Extendable key-value store for any extra data Senpai needs!",
        examples=[{"theme": "dark", "icon": "star", "layout": "grid"}],
    )

    # ─── Validation ───

    @field_validator("security")
    @classmethod
    def validate_security(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Aina-chan makes sure security rules make sense~"""
        if v is not None:
            # Remove empty strings
            v = [rule for rule in v if rule.strip()]
            if not v:
                return []  # Empty list = public access
        return v

    @field_validator("labels", "tags")
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Clean up labels and tags — lowercase and strip whitespace!"""
        if v is not None:
            v = [item.strip().lower() for item in v if item.strip()]
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for item in v:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result if result else None
        return v


# ─── Update Schema ───

class CollectionUpdate(BaseModel):
    """
    Schema for updating an existing Collection.

    All fields are optional so Senpai can do partial updates! ✨
    """

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Display title for the collection",
    )

    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9\-]+$",
        description="URL-friendly identifier",
    )

    desc: Optional[str] = Field(
        None,
        max_length=1000,
        description="Brief description of the collection",
    )

    labels: Optional[List[str]] = Field(
        None,
        description="Categorization labels",
    )

    tags: Optional[List[str]] = Field(
        None,
        description="Free-form tags",
    )

    security: Optional[List[str]] = Field(
        None,
        description="Security rules for access control",
    )

    sort_order: Optional[int] = Field(
        None,
        ge=0,
        description="Sorting priority",
    )

    custom: Optional[Dict[str, Any]] = Field(
        None,
        description="Extendable key-value store",
    )

    # ─── Validation ───

    @field_validator("security")
    @classmethod
    def validate_security(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            v = [rule for rule in v if rule.strip()]
            return v if v else []
        return v

    @field_validator("labels", "tags")
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            v = [item.strip().lower() for item in v if item.strip()]
            seen = set()
            result = []
            for item in v:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result if result else None
        return v


# ─── Response Schema ───

class CollectionResponse(BaseModel):
    """
    Schema for Collection data returned by the API.

    Aina-chan includes all the PocketBase metadata too~ (◕‿◕✿)
    """

    id: str = Field(
        ...,
        description="PocketBase record ID",
        examples=["abc123def456"],
    )

    title: str
    slug: str
    desc: Optional[str] = None

    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    security: Optional[List[str]] = None

    sort_order: int = 0
    custom: Optional[Dict[str, Any]] = None

    # PocketBase metadata
    created: str = Field(
        ...,
        description="ISO 8601 timestamp of creation",
        examples=["2026-05-02 10:30:00.000Z"],
    )

    updated: str = Field(
        ...,
        description="ISO 8601 timestamp of last update",
        examples=["2026-05-02 14:45:00.000Z"],
    )

    class Config:
        from_attributes = True


# ─── List Response Schema ───

class CollectionListResponse(BaseModel):
    """Paginated list of Collections."""

    items: List[CollectionResponse]
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=500)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


# ─── PocketBase JSON Schema (for creating the collection itself!) ───

def get_collection_pb_schema() -> dict:
    """
    Returns the PocketBase collection schema JSON for 'collections'.

    Aina-chan made this so Senpai can use it with
    PageCollectionManager-style initialization! ✨

    The security field uses PocketBase's built-in API rules
    so Senpai doesn't have to reinvent the wheel~ (◕‿◕✿)
    """
    return {
        "name": "collections",
        "type": "base",
        "listRule": "",        # Public read by default
        "viewRule": "",
        "createRule": "@request.auth.id != ''",
        "updateRule": "@request.auth.id != ''",
        "deleteRule": None,     # Superuser only
        "indexes": [
            "CREATE UNIQUE INDEX `idx_collections_slug` ON `collections` (`slug`)",
        ],
        "fields": [
            # ── Core ──
            {
                "name": "title",
                "type": "text",
                "required": True,
                "min": 1,
                "max": 200,
            },
            {
                "name": "slug",
                "type": "text",
                "required": True,
                "min": 1,
                "max": 200,
                "pattern": "^[a-z0-9\\-]+$",
            },
            {
                "name": "desc",
                "type": "text",
                "required": False,
                "max": 1000,
            },

            # ── Classification ──
            {
                "name": "labels",
                "type": "json",
                "required": False,
            },
            {
                "name": "tags",
                "type": "json",
                "required": False,
            },
            {
                "name": "security",
                "type": "json",
                "required": False,
            },

            # ── Behavior ──
            {
                "name": "sort_order",
                "type": "number",
                "required": False,
                "noDecimal": True,
                "min": 0,
            },

            # ── Extensibility ──
            {
                "name": "custom",
                "type": "json",
                "required": False,
            },

            # ── Timestamps ──
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
        ],
    }
