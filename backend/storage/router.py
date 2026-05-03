from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from backend.storage.service import StorageService
from backend.storage.schema import (
    StorageCreate,
    StorageUpdate,
    StorageResponse,
    StorageSummaryListResponse,
)


router = APIRouter(
    prefix="/storage",
    tags=["Storage"],
)


def get_service() -> StorageService:
    service = StorageService()
    if not service.initialize():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize storage! (╥﹏╥)",
        )
    return service


# ─── File Upload ─────────────────────────────────────────────────────

@router.post("/upload", response_model=StorageResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(..., description="The file to upload (any type, up to 100MB)"),
    folder: Optional[str] = Form(None, description="Optional folder path"),
    alt_text: Optional[str] = Form(None, description="Alt text for accessibility"),
    caption: Optional[str] = Form(None, description="Caption for the file"),
    is_public: bool = Form(False, description="Whether the file is publicly accessible"),
    labels: Optional[str] = Form(None, description="JSON array of labels"),
    tags: Optional[str] = Form(None, description="JSON array of tags"),
    uploaded_by: Optional[str] = Form(None, description="Who uploaded the file"),
    service: StorageService = Depends(get_service),
):
    """
    Upload a file (any type) to storage.
    Metadata can be provided as form fields.
    """
    # Parse JSON fields if provided
    parsed_labels = None
    parsed_tags = None
    if labels:
        import json
        try:
            parsed_labels = json.loads(labels)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="labels must be a valid JSON array")
    if tags:
        import json
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="tags must be a valid JSON array")

    try:
        result = await service.upload_file(
            file=file,
            folder=folder,
            alt_text=alt_text,
            caption=caption,
            is_public=is_public,
            labels=parsed_labels,
            tags=parsed_tags,
            uploaded_by=uploaded_by,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Metadata-Only Record Creation ──────────────────────────────────

@router.post("", response_model=StorageResponse, status_code=201)
async def create_storage_record(
    data: StorageCreate,
    service: StorageService = Depends(get_service),
):
    """
    Create a storage *metadata* record without an actual file.
    Useful for referencing external files or creating placeholders.
    """
    try:
        return service.create_record(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Existing Routes (unchanged) ────────────────────────────────────

@router.get("", response_model=StorageSummaryListResponse)
async def list_storage(
    page: int = 1,
    per_page: int = 20,
    sort: str = "-created",
    folder: Optional[str] = None,
    mime_type: Optional[str] = None,
    mime_category: Optional[str] = Query(
        None,
        description="Filter by broad MIME category: image, video, audio, document, archive, other",
    ),
    is_public: Optional[bool] = None,
    label: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    service: StorageService = Depends(get_service),
):
    """List storage/media records with filters."""
    return service.list_records(
        page=page,
        per_page=per_page,
        sort=sort,
        folder=folder,
        mime_type=mime_type,
        mime_category=mime_category,
        is_public=is_public,
        label=label,
        tag=tag,
        search=search,
        uploaded_by=uploaded_by,
    )


@router.get("/stats")
async def storage_stats(
    service: StorageService = Depends(get_service),
):
    """Get storage statistics."""
    return service.get_stats()


@router.get("/folders")
async def list_folders(
    service: StorageService = Depends(get_service),
):
    """List all unique folders used in storage."""
    return {"folders": service.list_folders()}


@router.get("/slug/suggest")
async def suggest_slug(
    filename: str = Query(..., description="Original filename to generate slug for"),
    folder: Optional[str] = Query("", description="Optional folder path"),
    service: StorageService = Depends(get_service),
):
    """Suggest a unique storage slug for a given filename."""
    slug = service.suggest_slug(filename, folder)
    return {"slug": slug, "filename": filename, "folder": folder}


@router.get("/folder/{folder_path:path}", response_model=StorageSummaryListResponse)
async def get_folder_contents(
    folder_path: str,
    page: int = 1,
    per_page: int = 50,
    service: StorageService = Depends(get_service),
):
    """Get all records within a specific folder."""
    return service.get_folder_contents(folder_path, page=page, per_page=per_page)


@router.get("/{record_id}", response_model=StorageResponse)
async def get_storage_record(
    record_id: str,
    service: StorageService = Depends(get_service),
):
    """Get a storage record by ID."""
    result = service.get_record(record_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find storage record '{record_id}'~ (╥﹏╥)",
        )
    return result


@router.get("/slug/{slug}", response_model=StorageResponse)
async def get_storage_record_by_slug(
    slug: str,
    service: StorageService = Depends(get_service),
):
    """Get a storage record by its file slug/path."""
    result = service.get_record_by_slug(slug)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find storage record with slug '{slug}'~ (╥﹏╥)",
        )
    return result


@router.put("/{record_id}", response_model=StorageResponse)
async def update_storage_record(
    record_id: str,
    data: StorageUpdate,
    service: StorageService = Depends(get_service),
):
    """Update a storage record."""
    try:
        return service.update_record(record_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{record_id}", status_code=204)
async def delete_storage_record(
    record_id: str,
    service: StorageService = Depends(get_service),
):
    """Delete a storage record."""
    try:
        service.delete_record(record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
