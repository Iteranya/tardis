from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class StorageCreate(BaseModel):
    """Schema for creating a new storage/media record."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename",
        examples=["hero-banner.jpg", "logo.png", "presentation.pdf"],
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9_\-\.\/]+$",
        description="Stored file path/identifier (unique)",
        examples=["uploads/images/hero-banner.jpg", "media/logo.png"],
    )
    mime_type: str = Field(
        ...,
        max_length=100,
        description="MIME type of the file",
        examples=["image/jpeg", "image/png", "application/pdf", "video/mp4"],
    )
    size: int = Field(
        ...,
        ge=0,
        description="File size in bytes",
        examples=[1024, 2048000, 10485760],
    )
    width: Optional[int] = Field(
        None,
        ge=0,
        description="Image width in pixels (if applicable)",
    )
    height: Optional[int] = Field(
        None,
        ge=0,
        description="Image height in pixels (if applicable)",
    )
    duration: Optional[float] = Field(
        None,
        ge=0,
        description="Duration in seconds for audio/video files",
    )
    alt_text: Optional[str] = Field(
        None,
        max_length=500,
        description="Alt text for accessibility",
        examples=["Aina-chan coding on her laptop"],
    )
    caption: Optional[str] = Field(
        None,
        max_length=1000,
        description="Caption or description of the media",
        examples=["Hero banner for the about page"],
    )
    folder: Optional[str] = Field(
        None,
        max_length=200,
        description="Virtual folder path for organization",
        examples=["images/banners", "documents/pdfs", "videos/tutorials"],
    )
    labels: Optional[List[str]] = Field(
        None,
        description="Labels for categorization",
        examples=[["image", "banner", "homepage"]],
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Free-form tags for search",
        examples=[["hero", "landing", "background"]],
    )
    uploaded_by: Optional[str] = Field(
        None,
        max_length=100,
        description="Who uploaded the file",
        examples=["Aina-chan", "Artes-senpai"],
    )
    checksum: Optional[str] = Field(
        None,
        max_length=64,
        description="File integrity hash (e.g., SHA-256)",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    )
    is_public: bool = Field(
        True,
        description="Whether the file is publicly accessible",
    )
    custom: Optional[Dict[str, Any]] = Field(
        None,
        description="Extendable key-value store",
        examples=[{"photographer": "Aina-chan", "license": "MIT"}],
    )

    @field_validator("labels", "tags")
    @classmethod
    def clean_string_lists(cls, v):
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


class StorageUpdate(BaseModel):
    """Schema for updating a storage record (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9_\-\.\/]+$")
    mime_type: Optional[str] = Field(None, max_length=100)
    size: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    duration: Optional[float] = Field(None, ge=0)
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = Field(None, max_length=1000)
    folder: Optional[str] = Field(None, max_length=200)
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    uploaded_by: Optional[str] = Field(None, max_length=100)
    checksum: Optional[str] = Field(None, max_length=64)
    is_public: Optional[bool] = None
    custom: Optional[Dict[str, Any]] = None

    @field_validator("labels", "tags")
    @classmethod
    def clean_string_lists(cls, v):
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


class StorageResponse(BaseModel):
    """Schema for storage record returned by the API."""
    id: str
    name: str
    slug: str
    mime_type: str
    size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    folder: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    uploaded_by: Optional[str] = None
    checksum: Optional[str] = None
    is_public: bool = True
    custom: Optional[Dict[str, Any]] = None
    created: str
    updated: str

    class Config:
        from_attributes = True


class StorageListResponse(BaseModel):
    """Paginated list of storage records."""
    items: List[StorageResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int


class StorageSummary(BaseModel):
    """Lightweight version for listing views (no heavy metadata)."""
    id: str
    name: str
    slug: str
    mime_type: str
    size: int
    width: Optional[int] = None
    height: Optional[int] = None
    folder: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: bool
    created: str
    updated: str

    class Config:
        from_attributes = True


class StorageSummaryListResponse(BaseModel):
    """Paginated list of storage summaries."""
    items: List[StorageSummary]
    page: int
    per_page: int
    total_items: int
    total_pages: int
