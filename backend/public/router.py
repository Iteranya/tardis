from fastapi import APIRouter, Depends, HTTPException, Query
from backend.collections.service import CollectionService
from backend.collections.schema import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    FieldAddRequest,
    FieldRemoveRequest,
    SchemaValidationResponse,
)


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


def get_service() -> CollectionService:
    """Dependency: provide CollectionService."""
    return CollectionService()


# ─── CRUD Routes ────────────────────────────────────────────────

@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    include_system: bool = Query(False, description="Include system collections?"),
    service: CollectionService = Depends(get_service),
):
    """List all collections (content types)."""
    return service.list_collections(include_system=include_system)


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(
    data: CollectionCreate,
    service: CollectionService = Depends(get_service),
):
    """Create a new collection (content type)."""
    try:
        return service.create_collection(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def collection_stats(
    service: CollectionService = Depends(get_service),
):
    """Get collection statistics."""
    return service.get_stats()


@router.get("/validate", response_model=SchemaValidationResponse)
async def validate_collection_schema(
    data: CollectionCreate,
    service: CollectionService = Depends(get_service),
):
    """
    Validate a collection schema before creating it.

    Aina-chan's safe way to check if everything is correct! (◕‿◕✿)
    """
    return service.validate_schema(data)


@router.get("/{name_or_id}", response_model=CollectionResponse)
async def get_collection(
    name_or_id: str,
    service: CollectionService = Depends(get_service),
):
    """Get a collection by name or ID."""
    result = service.get_collection(name_or_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find collection '{name_or_id}'~ (╥﹏╥)",
        )
    return result


@router.put("/{name_or_id}/rules", response_model=CollectionResponse)
async def update_collection_rules(
    name_or_id: str,
    data: CollectionUpdate,
    service: CollectionService = Depends(get_service),
):
    """Update API rules for a collection."""
    try:
        return service.update_collection_rules(name_or_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name_or_id}", status_code=204)
async def delete_collection(
    name_or_id: str,
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
    service: CollectionService = Depends(get_service),
):
    """
    Delete a collection and ALL its data!

    ⚠️ Aina-chan requires confirm=True! This is irreversible!
    """
    try:
        service.delete_collection(name_or_id, confirm=confirm)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Field Routes ───────────────────────────────────────────────

@router.post("/{name_or_id}/fields", response_model=CollectionResponse)
async def add_field(
    name_or_id: str,
    data: FieldAddRequest,
    service: CollectionService = Depends(get_service),
):
    """Add a new field to a collection."""
    try:
        return service.add_field(name_or_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name_or_id}/fields", response_model=CollectionResponse)
async def remove_field(
    name_or_id: str,
    data: FieldRemoveRequest,
    service: CollectionService = Depends(get_service),
):
    """
    Remove a field from a collection.

    ⚠️ This drops the column and its data!
    """
    try:
        return service.remove_field(name_or_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Duplicate Route ────────────────────────────────────────────

@router.post("/{source_name}/duplicate", response_model=CollectionResponse)
async def duplicate_collection(
    source_name: str,
    new_name: str = Query(..., description="Name for the new collection"),
    service: CollectionService = Depends(get_service),
):
    """Duplicate a collection's schema to create a new one."""
    try:
        return service.duplicate_collection(source_name, new_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
