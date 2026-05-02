from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    desc: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=100)
    draft: Optional[str] = None
    release: Optional[str] = None
    thumb: Optional[str] = None
    gallery: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: bool = False
    sort_order: int = 0
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


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200, pattern=r"^[a-z0-9\-]+$")
    desc: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=100)
    draft: Optional[str] = None
    release: Optional[str] = None
    thumb: Optional[str] = None
    gallery: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
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


class ArticleResponse(BaseModel):
    id: str
    title: str
    slug: str
    desc: Optional[str] = None
    author: Optional[str] = None
    draft: Optional[str] = None
    release: Optional[str] = None
    thumb: Optional[str] = None
    gallery: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: bool = False
    sort_order: int = 0
    custom: Optional[Dict[str, Any]] = None
    created: str
    updated: str

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    items: List[ArticleResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int


class ArticleSummary(BaseModel):
    id: str
    title: str
    slug: str
    desc: Optional[str] = None
    author: Optional[str] = None
    thumb: Optional[str] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    enabled: bool
    sort_order: int
    created: str
    updated: str

    class Config:
        from_attributes = True


class ArticleSummaryListResponse(BaseModel):
    items: List[ArticleSummary]
    page: int
    per_page: int
    total_items: int
    total_pages: int
