import os
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.pages.service import PageService
from backend.pages.schema import (
    PageCreate,
    PageUpdate,
    PageResponse,
    PageSummaryListResponse,
)


router = APIRouter(
    prefix="/pages",
    tags=["Pages"],
)


def get_service() -> PageService:
    """Dependency: provide PageService with auto-init."""
    service = PageService()
    if not service.initialize():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize pages! (╥﹏╥)",
        )
    return service


@router.get("", response_model=PageSummaryListResponse)
async def list_pages(
    page: int = 1,
    per_page: int = 20,
    sort: str = "-sort_order",
    enabled: Optional[bool] = None,
    label: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    service: PageService = Depends(get_service),
):
    """List pages with filters."""
    return service.list_pages(
        page=page,
        per_page=per_page,
        sort=sort,
        enabled=enabled,
        label=label,
        tag=tag,
        search=search,
    )


@router.post("", response_model=PageResponse, status_code=201)
async def create_page(
    data: PageCreate,
    service: PageService = Depends(get_service),
):
    """Create a new page."""
    try:
        return service.create_page(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def page_stats(
    service: PageService = Depends(get_service),
):
    """Get page statistics."""
    return service.get_stats()


@router.get("/slug/suggest")
async def suggest_slug(
    title: str,
    service: PageService = Depends(get_service),
):
    """Suggest a unique slug for a given title."""
    slug = service.suggest_slug(title)
    return {"slug": slug, "title": title}


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    service: PageService = Depends(get_service),
):
    """Get a page by ID."""
    result = service.get_page(page_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find page '{page_id}'~ (╥﹏╥)",
        )
    return result


@router.get("/slug/{slug}", response_model=PageResponse)
async def get_page_by_slug(
    slug: str,
    service: PageService = Depends(get_service),
):
    """Get a page by slug."""
    result = service.get_page_by_slug(slug)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find page with slug '{slug}'~ (╥﹏╥)",
        )
    return result


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: str,
    data: PageUpdate,
    service: PageService = Depends(get_service),
):
    """Update a page."""
    try:
        return service.update_page(page_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{page_id}", status_code=204)
async def delete_page(
    page_id: str,
    service: PageService = Depends(get_service),
):
    """Delete a page."""
    try:
        service.delete_page(page_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{page_id}/enable", response_model=PageResponse)
async def enable_page(
    page_id: str,
    service: PageService = Depends(get_service),
):
    """Enable a page."""
    try:
        return service.update_page(page_id, PageUpdate(enabled=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{page_id}/disable", response_model=PageResponse)
async def disable_page(
    page_id: str,
    service: PageService = Depends(get_service),
):
    """Disable a page."""
    try:
        return service.update_page(page_id, PageUpdate(enabled=False))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
