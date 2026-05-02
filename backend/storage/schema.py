from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

class Page:
    # --- Core ---
    title: str                                   # Text, required, min:1, max:200
    slug: str                                    # Text, required, unique URL path
    desc: Optional[str] = None                   # Text, optional description

    # --- Content ---
    content_id: Optional[str] = None             # Relation to a "contents" collection
    thumb: Optional[str] = None                  # File field for thumbnail image

    # --- Classification ---
    labels: Optional[List[str]] = None           # Json or select (if predefined)
    tags: Optional[List[str]] = None             # Json or select (if predefined)

    # --- Behavior ---
    enabled: bool = False                        # Bool, is page active?
    sort_order: int = 0                          # Number, integer for manual ordering

    # --- Extensibility ---
    custom: Optional[Dict[str, Any]] = None      # Json, for any extra needs


# ─── Pydantic Schemas ───

class PageCreate(BaseModel):
    """Schema for creating a new page."""
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    desc: Optional[str] = Field(None, max_length=500)
    content_id: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: bool = False
    sort_order: int = 0
    custom: Optional[dict] = None


class PageUpdate(BaseModel):
    """Schema for updating a page (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    desc: Optional[str] = Field(None, max_length=500)
    content_id: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None
    custom: Optional[dict] = None


class PageResponse(BaseModel):
    """Schema for page response data."""
    id: str
    title: str
    slug: str
    desc: Optional[str] = None
    content_id: Optional[str] = None
    thumb: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: bool
    sort_order: int
    custom: Optional[dict] = None
    created: str
    updated: str

    class Config:
        from_attributes = True


class PageListResponse(BaseModel):
    """Schema for paginated page list."""
    items: List[PageResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int
