from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.site.service import SiteService
from backend.site.schema import (
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    SiteSummaryListResponse,
)
import os, tempfile

router = APIRouter(
    prefix="/sites",
    tags=["Sites"],
)


def get_service() -> SiteService:
    service = SiteService()
    if not service.initialize():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize sites! (╥﹏╥)",
        )
    return service


@router.get("", response_model=SiteSummaryListResponse)
async def list_sites(
    page: int = 1,
    per_page: int = 20,
    sort: str = "-sort_order",
    enabled: Optional[bool] = None,
    author: Optional[str] = None,
    label: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    service: SiteService = Depends(get_service),
):
    """List site entries with filters."""
    return service.list_sites(
        page=page,
        per_page=per_page,
        sort=sort,
        enabled=enabled,
        author=author,
        label=label,
        tag=tag,
        search=search,
    )


@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(
    data: SiteCreate,
    service: SiteService = Depends(get_service),
):
    """Create a new site entry."""
    try:
        return service.create_site(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def site_stats(
    service: SiteService = Depends(get_service),
):
    """Get site statistics."""
    return service.get_stats()


@router.get("/slug/suggest")
async def suggest_slug(
    title: str,
    service: SiteService = Depends(get_service),
):
    """Suggest a unique slug for a given title."""
    slug = service.suggest_slug(title)
    return {"slug": slug, "title": title}


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    service: SiteService = Depends(get_service),
):
    """Get a site entry by ID."""
    result = service.get_site(site_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find site '{site_id}'~ (╥﹏╥)",
        )
    return result


@router.get("/slug/{slug}", response_model=SiteResponse)
async def get_site_by_slug(
    slug: str,
    service: SiteService = Depends(get_service),
):
    """Get a site entry by slug."""
    result = service.get_site_by_slug(slug)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find site with slug '{slug}'~ (╥﹏╥)",
        )
    return result


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    data: SiteUpdate,
    service: SiteService = Depends(get_service),
):
    """Update a site entry."""
    try:
        return service.update_site(site_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: str,
    service: SiteService = Depends(get_service),
):
    """Delete a site entry."""
    try:
        service.delete_site(site_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{site_id}/publish", response_model=SiteResponse)
async def publish_site(
    site_id: str,
    service: SiteService = Depends(get_service),
):
    """Publish a site entry (enable + promote draft to release)."""
    try:
        return service.publish_site(site_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{site_id}/unpublish", response_model=SiteResponse)
async def unpublish_site(
    site_id: str,
    service: SiteService = Depends(get_service),
):
    """Unpublish a site entry (disable only, content preserved)."""
    try:
        return service.unpublish_site(site_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{site_id}/thumbnail", response_model=SiteResponse)
async def upload_thumbnail(
    site_id: str,
    file: UploadFile = File(...),
    service: SiteService = Depends(get_service),
):
    """Upload a thumbnail image for a site entry."""
    allowed = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Aina-chan only accepts JPEG, PNG, or WebP! "
                   f"Got '{file.content_type}'~ (╥﹏╥)",
        )


    suffix = os.path.splitext(file.filename or "upload.jpg")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = service.manager.upload_thumbnail(site_id, tmp_path)
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Aina-chan couldn't upload the thumbnail~",
            )
        return SiteResponse(**result)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
