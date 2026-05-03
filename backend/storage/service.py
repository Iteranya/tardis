from typing import Optional, List
from fastapi import UploadFile
from backend.storage.manager import StorageManager
from backend.storage.schema import (
    StorageCreate,
    StorageUpdate,
    StorageResponse,
    StorageSummary,
)


class StorageService:
    """
    Aina-chan's Business Logic Layer for Storage! (◕‿◕✿)

    Handles validation, slug generation, and file metadata workflows.
    Now with actual file upload support!
    """

    def __init__(self):
        self.manager = StorageManager()

    # ─── Lifecycle ──────────────────────────────────────────────────

    def initialize(self) -> bool:
        return self.manager.ensure_collection_exists()

    # ─── File Uploads ───────────────────────────────────────────────

    async def upload_file(
        self,
        file: UploadFile,
        folder: Optional[str] = None,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None,
        is_public: bool = False,
        labels: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: Optional[str] = None,
    ) -> StorageResponse:
        """
        Upload a file from a FastAPI UploadFile.
        Builds metadata and calls the manager.
        """
        # Read file bytes
        file_bytes = await file.read()
        filename = file.filename or "unnamed"

        # Build metadata dict
        metadata = {
            "alt_text": alt_text,
            "caption": caption,
            "folder": folder,
            "is_public": is_public,
            "labels": labels or [],
            "tags": tags or [],
            "uploaded_by": uploaded_by,
        }
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}

        # Delegate to manager
        result = self.manager.upload_file_from_bytes(
            file_bytes=file_bytes,
            filename=filename,
            metadata=metadata,
        )
        if not result:
            raise RuntimeError("Aina-chan couldn't upload the file~ (╥﹏╥)")

        return StorageResponse(**result)

    # ─── CRUD with Business Logic ───────────────────────────────────

    def create_record(self, data: StorageCreate) -> Optional[StorageResponse]:
        """Create a metadata-only storage record (no file attached)."""
        # Check slug uniqueness
        if self.manager.slug_exists(data.slug):
            raise ValueError(
                f"A storage record with slug '{data.slug}' already exists! "
                f"Aina-chan can't have duplicates~ (╥﹏╥)"
            )

        result = self.manager.create_record(data.model_dump(exclude_unset=True))
        if not result:
            raise RuntimeError("Aina-chan couldn't create the storage record~")
        return StorageResponse(**result)

    def get_record(self, record_id: str) -> Optional[StorageResponse]:
        result = self.manager.get_record(record_id)
        if not result:
            return None
        return StorageResponse(**result)

    def get_record_by_slug(self, slug: str) -> Optional[StorageResponse]:
        result = self.manager.get_record_by_slug(slug)
        if not result:
            return None
        return StorageResponse(**result)

    def update_record(self, record_id: str, data: StorageUpdate) -> Optional[StorageResponse]:
        existing = self.manager.get_record(record_id)
        if not existing:
            raise ValueError(f"Storage record '{record_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] != existing.get("slug"):
            if self.manager.slug_exists(update_data["slug"], exclude_id=record_id):
                raise ValueError(
                    f"Another record already has the slug '{update_data['slug']}'!"
                )

        result = self.manager.update_record(record_id, update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the storage record~")
        return StorageResponse(**result)

    def delete_record(self, record_id: str) -> bool:
        existing = self.manager.get_record(record_id)
        if not existing:
            raise ValueError(f"Storage record '{record_id}' not found~")
        return self.manager.delete_record(record_id)

    # ─── Listing ────────────────────────────────────────────────────

    def list_records(
        self,
        page: int = 1,
        per_page: int = 20,
        sort: str = "-created",
        folder: Optional[str] = None,
        mime_type: Optional[str] = None,
        mime_category: Optional[str] = None,
        is_public: Optional[bool] = None,
        label: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> dict:
        result = self.manager.list_records(
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
        return {
            "items": [StorageSummary(**item) for item in result.get("items", [])],
            "page": result.get("page", page),
            "per_page": result.get("perPage", per_page),
            "total_items": result.get("totalItems", 0),
            "total_pages": result.get("totalPages", 0),
        }

    # ─── Folder Operations ─────────────────────────────────────────

    def list_folders(self) -> List[str]:
        return self.manager.list_folders()

    def get_folder_contents(self, folder: str, page: int = 1, per_page: int = 50) -> dict:
        return self.list_records(page=page, per_page=per_page, folder=folder)

    # ─── Slug Generation ────────────────────────────────────────────

    def suggest_slug(self, filename: str, folder: str = "") -> str:
        return self.manager.generate_unique_slug(filename, folder)

    # ─── Stats ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self.manager.get_stats()
