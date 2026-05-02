# app/routers/pages.py
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pages.schema import PageCreate, PageListResponse, PageResponse, PageUpdate
from pages.pb import PageCollectionManager

# ─── Dependency ───

def get_page_manager() -> PageCollectionManager:
    """
    FastAPI dependency that provides a PageCollectionManager instance.

    Aina-chan ensures the collection exists before returning it! (◕‿◕✿)
    """
    manager = PageCollectionManager()

    # Auto-initialize the collection if needed
    if not manager.ensure_collection_exists():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize the pages collection! (╥﹏╥)",
        )

    return manager


# ─── Router ───

router = APIRouter(
    prefix="/pages",
    tags=["Pages"],
    responses={404: {"description": "Page not found"}},
)


@router.get("", response_model=PageListResponse)
async def list_pages(
    page: int = 1,
    per_page: int = 20,
    sort: str = "-sort_order",
    filter: Optional[str] = None,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Get a paginated list of pages.

    Aina-chan supports filtering and sorting too~♪
    """
    result = manager.list_pages(
        page=page,
        per_page=per_page,
        sort=sort,
        filter=filter,
    )

    return PageListResponse(
        items=[PageResponse(**item) for item in result.get("items", [])],
        page=result.get("page", page),
        per_page=result.get("perPage", per_page),
        total_items=result.get("totalItems", 0),
        total_pages=result.get("totalPages", 0),
    )


@router.post("", response_model=PageResponse, status_code=201)
async def create_page(
    page_data: PageCreate,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Create a new page.

    Aina-chan will check if the slug is already taken! (｀・ω・´)
    """
    # Check for duplicate slug
    existing = manager.get_page_by_slug(page_data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A page with slug '{page_data.slug}' already exists! "
                   f"Aina-chan can't have duplicates~ (╥﹏╥)",
        )

    result = manager.create_page(page_data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't create the page! Something went wrong~",
        )

    return PageResponse(**result)


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Get a single page by its ID.
    """
    result = manager.get_page(page_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find a page with ID '{page_id}'~ (╥﹏╥)",
        )

    return PageResponse(**result)


@router.get("/slug/{slug}", response_model=PageResponse)
async def get_page_by_slug(
    slug: str,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Get a single page by its URL slug.
    """
    result = manager.get_page_by_slug(slug)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find a page with slug '{slug}'~ (╥﹏╥)",
        )

    return PageResponse(**result)


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: str,
    page_data: PageUpdate,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Update an existing page.

    Aina-chan will check slug uniqueness if Senpai is changing the slug! (◕‿◕✿)
    """
    # Check if page exists first
    existing = manager.get_page(page_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find a page with ID '{page_id}'~ (╥﹏╥)",
        )

    # If slug is being changed, check for duplicates
    update_data = page_data.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != existing.get("slug"):
        slug_exists = manager.get_page_by_slug(update_data["slug"])
        if slug_exists and slug_exists["id"] != page_id:
            raise HTTPException(
                status_code=409,
                detail=f"Another page already has the slug '{update_data['slug']}'! "
                       f"Aina-chan can't allow duplicates~",
            )

    result = manager.update_page(page_id, update_data)
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't update the page! Something went wrong~",
        )

    return PageResponse(**result)


@router.delete("/{page_id}", status_code=204)
async def delete_page(
    page_id: str,
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Delete a page by its ID.
    """
    # Check if page exists
    existing = manager.get_page(page_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find a page with ID '{page_id}'~ (╥﹏╥)",
        )

    success = manager.delete_page(page_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't delete the page! Something went wrong~",
        )

    return None


@router.post("/{page_id}/thumbnail", response_model=PageResponse)
async def upload_page_thumbnail(
    page_id: str,
    file: UploadFile = File(...),
    manager: PageCollectionManager = Depends(get_page_manager),
):
    """
    Upload a thumbnail image for a page.

    Aina-chan supports JPEG, PNG, and WebP images up to 5MB! (◕‿◕✿)
    """
    # Check if page exists
    existing = manager.get_page(page_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find a page with ID '{page_id}'~ (╥﹏╥)",
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Aina-chan only accepts JPEG, PNG, or WebP images! "
                   f"Senpai sent '{file.content_type}'~ (╥﹏╥)",
        )

    # Save the uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Upload to PocketBase
        result = manager.upload_thumbnail(page_id, temp_path)
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Aina-chan couldn't upload the thumbnail! Something went wrong~",
            )

        return PageResponse(**result)

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
