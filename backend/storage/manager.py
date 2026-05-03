import os
import re
from typing import Optional, List
from pocketbase import PocketBase
from pocketbase.client import FileUpload
from backend.util.auth import authenticate_admin
from backend.util.secrets import SecretsManager


class StorageManager:
    """
    Aina-chan's Storage Manager! (◕‿◕✿)

    Manages the actual file storage in PocketBase.
    Handles uploading, downloading, and metadata for any file type.
    This module is self-contained and can be deleted without breaking others!
    """

    COLLECTION_NAME = "sys_storage"

    @property
    def _collection_schema(self) -> dict:
        return {
            "name": self.COLLECTION_NAME,
            "type": "base",
            "listRule": "",
            "viewRule": "",
            "createRule": "@request.auth.id != ''",
            "updateRule": "@request.auth.id != ''",
            "deleteRule": None,
            "indexes": [
                f"CREATE UNIQUE INDEX idx_{self.COLLECTION_NAME}_slug ON {self.COLLECTION_NAME} (slug)",
                f"CREATE INDEX idx_{self.COLLECTION_NAME}_folder ON {self.COLLECTION_NAME} (folder)",
                f"CREATE INDEX idx_{self.COLLECTION_NAME}_mime ON {self.COLLECTION_NAME} (mime_type)",
                f"CREATE INDEX idx_{self.COLLECTION_NAME}_public ON {self.COLLECTION_NAME} (is_public)",
            ],
            "fields": [
                # ✅ The actual file – PocketBase will store and serve it
                {"name": "file", "type": "file", "required": False, "maxSelect": 1, "maxSize": 104_857_600, "mimeTypes": []},
                {"name": "name", "type": "text", "required": True, "min": 1, "max": 255},
                {"name": "slug", "type": "text", "required": True, "min": 1, "max": 255, "pattern": "^[a-zA-Z0-9_\\-\\.\\/]+$"},
                {"name": "mime_type", "type": "text", "required": True, "max": 100},
                {"name": "size", "type": "number", "required": True, "noDecimal": True, "min": 0},
                {"name": "width", "type": "number", "required": False, "noDecimal": True, "min": 0},
                {"name": "height", "type": "number", "required": False, "noDecimal": True, "min": 0},
                {"name": "duration", "type": "number", "required": False, "min": 0},
                {"name": "alt_text", "type": "text", "required": False, "max": 500},
                {"name": "caption", "type": "text", "required": False, "max": 1000},
                {"name": "folder", "type": "text", "required": False, "max": 200},
                {"name": "labels", "type": "json", "required": False},
                {"name": "tags", "type": "json", "required": False},
                {"name": "uploaded_by", "type": "text", "required": False, "max": 100},
                {"name": "checksum", "type": "text", "required": False, "max": 64},
                {"name": "is_public", "type": "bool", "required": False},
                {"name": "custom", "type": "json", "required": False},
                {"name": "created", "type": "autodate", "onCreate": True, "onUpdate": False},
                {"name": "updated", "type": "autodate", "onCreate": True, "onUpdate": True},
            ],
        }

    # ─── Initialization ──────────────────────────────────────────

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        """Authenticate as superadmin for collection management."""
        if not self.admin_email or not self.admin_password:
            raise ValueError(
                "Aina-chan needs admin email and password to manage collections! ⊙﹏⊙"
            )

        try:
            result = authenticate_admin(
                self.client,
                self.admin_email,
                self.admin_password,
            )
            self._is_authenticated = result
            return result
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    def ensure_collection_exists(self) -> bool:
        """Create the collection if it doesn't exist yet."""
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False

        try:
            # Check if collection already exists
            try:
                self.client.collections.get_one(self.COLLECTION_NAME)
                return True
            except Exception as e:
                error_msg = str(e)
                if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                    return True

            # Try to create it
            self.client.collections.create(self._collection_schema)
            print(f"Aina-chan created the '{self.COLLECTION_NAME}' collection! ✨")
            return True

        except Exception as e:
            error_data = getattr(e, 'data', {})
            if isinstance(error_data, dict):
                data_field = error_data.get('data', {})
                if isinstance(data_field, dict):
                    name_error = data_field.get('name', {})
                    if isinstance(name_error, dict):
                        if name_error.get('code') == 'validation_collection_name_exists':
                            return True

            error_msg = str(e)
            if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                return True

            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False

    # ─── File Upload ─────────────────────────────────────────────

    def upload_file(self, file_path: str, metadata: Optional[dict] = None) -> Optional[dict]:
        """
        Upload a file and create a storage record.

        Args:
            file_path: Path to the file on disk.
            metadata: Additional fields (name, alt_text, folder, etc.).
                     If name is not provided, the filename will be used.

        Returns:
            The created record dictionary, or None on failure.
        """
        if not os.path.isfile(file_path):
            print(f"Aina-chan can't find the file: {file_path} (╥﹏╥)")
            return None

        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Determine MIME type from file extension (basic guess)
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Build data dict
        data = metadata or {}
        data.setdefault("name", filename)
        data.setdefault("mime_type", mime_type)
        data.setdefault("size", file_size)
        if "slug" not in data:
            data["slug"] = self.generate_unique_slug(filename, data.get("folder", ""))

        # Read file as FileUpload
        try:
            with open(file_path, "rb") as f:
                file_upload = FileUpload(
                    filename=filename,
                    data=f.read(),
                    content_type=mime_type,
                )
            data["file"] = file_upload
            return self.client.collection(self.COLLECTION_NAME).create(data)
        except Exception as e:
            print(f"Aina-chan couldn't upload the file! Error: {e} (╥﹏╥)")
            return None

    def upload_file_from_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Upload a file from raw bytes.

        Args:
            file_bytes: The file content.
            filename: Original filename (used for MIME type).
            metadata: Additional fields (name, alt_text, folder, etc.).

        Returns:
            The created record dictionary, or None on failure.
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        data = metadata or {}
        data.setdefault("name", filename)
        data.setdefault("mime_type", mime_type)
        data.setdefault("size", len(file_bytes))
        if "slug" not in data:
            data["slug"] = self.generate_unique_slug(filename, data.get("folder", ""))

        try:
            file_upload = FileUpload(
                filename=filename,
                data=file_bytes,
                content_type=mime_type,
            )
            data["file"] = file_upload
            return self.client.collection(self.COLLECTION_NAME).create(data)
        except Exception as e:
            print(f"Aina-chan couldn't upload the file from bytes! Error: {e} (╥﹏╥)")
            return None

    # ─── CRUD ─────────────────────────────────────────────────────

    def create_record(self, data: dict) -> Optional[dict]:
        """
        Create a new storage metadata record without a file.
        (Use upload_file or upload_file_from_bytes for file uploads.)
        """
        try:
            return self.client.collection(self.COLLECTION_NAME).create(data)
        except Exception as e:
            print(f"Aina-chan couldn't create storage record! Error: {e} (╥﹏╥)")
            return None

    def get_record(self, record_id: str) -> Optional[dict]:
        try:
            return self.client.collection(self.COLLECTION_NAME).get_one(record_id)
        except Exception:
            return None

    def get_record_by_slug(self, slug: str) -> Optional[dict]:
        try:
            result = self.client.collection(self.COLLECTION_NAME).get_list(
                query_params={"filter": f'slug = "{slug}"', "limit": 1},
            )
            items = result.get("items", [])
            return items[0] if items else None
        except Exception:
            return None

    def update_record(self, record_id: str, data: dict) -> Optional[dict]:
        try:
            return self.client.collection(self.COLLECTION_NAME).update(record_id, data)
        except Exception as e:
            print(f"Aina-chan couldn't update storage record! Error: {e} (╥﹏╥)")
            return None

    def delete_record(self, record_id: str) -> bool:
        try:
            self.client.collection(self.COLLECTION_NAME).delete(record_id)
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete storage record! Error: {e} (╥﹏╥)")
            return False

    # ─── Listing with Filters ────────────────────────────────────

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
        filters = []

        if folder is not None:
            filters.append(f'folder = "{folder}"')
        if mime_type:
            filters.append(f'mime_type = "{mime_type}"')
        if mime_category:
            filters.append(f'mime_type ~ "{mime_category}"')
        if is_public is not None:
            filters.append(f"is_public = {str(is_public).lower()}")
        if label:
            filters.append(f'labels ~ "{label}"')
        if tag:
            filters.append(f'tags ~ "{tag}"')
        if uploaded_by:
            filters.append(f'uploaded_by = "{uploaded_by}"')
        if search:
            filters.append(f'(name ~ "{search}" || caption ~ "{search}" || alt_text ~ "{search}")')

        filter_str = " && ".join(filters) if filters else None

        try:
            params = {"page": page, "perPage": per_page, "sort": sort}
            if filter_str:
                params["filter"] = filter_str
            return self.client.collection(self.COLLECTION_NAME).get_list(query_params=params)
        except Exception as e:
            print(f"Aina-chan couldn't list storage records! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── Slug Utilities ─────────────────────────────────────────

    def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        try:
            result = self.client.collection(self.COLLECTION_NAME).get_list(
                query_params={"filter": f'slug = "{slug}"', "limit": 1},
            )
            items = result.get("items", [])
            if not items:
                return False
            if exclude_id:
                return items[0]["id"] != exclude_id
            return True
        except Exception:
            return False

    def generate_slug(self, filename: str, folder: str = "") -> str:
        """Generate a storage slug from filename."""
        base, ext = os.path.splitext(filename)
        base = base.lower()
        base = re.sub(r'[^a-z0-9_\-]', '-', base)
        base = re.sub(r'-+', '-', base).strip('-')
        slug_base = f"{folder}/{base}{ext}".lstrip("/") if folder else f"{base}{ext}"
        return slug_base

    def generate_unique_slug(self, filename: str, folder: str = "") -> str:
        base_slug = self.generate_slug(filename, folder)
        slug = base_slug
        counter = 1
        while self.slug_exists(slug):
            name, ext = os.path.splitext(base_slug)
            slug = f"{name}-{counter}{ext}"
            counter += 1
        return slug

    # ─── Folder Operations ───────────────────────────────────────

    def list_folders(self) -> List[str]:
        """Get a list of all unique folder paths used in storage."""
        try:
            result = self.client.collection(self.COLLECTION_NAME).get_list(
                query_params={"perPage": 500, "fields": "folder"},
            )
            folders = set()
            for item in result.get("items", []):
                f = item.get("folder")
                if f:
                    folders.add(f)
            return sorted(folders)
        except Exception:
            return []

    def get_folder_contents(
        self,
        folder: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """Get all records within a specific folder."""
        return self.list_records(page=page, per_page=per_page, folder=folder)

    # ─── MIME Type Helpers ───────────────────────────────────────

    @staticmethod
    def get_mime_category(mime_type: str) -> str:
        """Get the broad category of a MIME type."""
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("text/"):
            return "document"
        if mime_type == "application/pdf":
            return "document"
        if "spreadsheet" in mime_type:
            return "document"
        if "presentation" in mime_type:
            return "document"
        if "zip" in mime_type or "rar" in mime_type or "tar" in mime_type:
            return "archive"
        return "other"

    @staticmethod
    def is_image(mime_type: str) -> bool:
        return mime_type.startswith("image/")

    @staticmethod
    def is_video(mime_type: str) -> bool:
        return mime_type.startswith("video/")

    @staticmethod
    def is_audio(mime_type: str) -> bool:
        return mime_type.startswith("audio/")

    @staticmethod
    def is_document(mime_type: str) -> bool:
        doc_types = ["text/", "application/pdf", "application/msword",
                     "application/vnd.openxmlformats-officedocument"]
        return any(mime_type.startswith(t) for t in doc_types)

    # ─── Stats ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get storage statistics, grouped by MIME category."""
        total = 0
        total_size = 0
        image_count = 0
        video_count = 0
        audio_count = 0
        document_count = 0
        archive_count = 0
        other_count = 0

        try:
            result = self.client.collection(self.COLLECTION_NAME).get_list(
                query_params={"perPage": 500, "fields": "mime_type,size"},
            )
            for item in result.get("items", []):
                total += 1
                total_size += item.get("size", 0)
                mime = item.get("mime_type", "")
                cat = self.get_mime_category(mime)
                if cat == "image":
                    image_count += 1
                elif cat == "video":
                    video_count += 1
                elif cat == "audio":
                    audio_count += 1
                elif cat == "document":
                    document_count += 1
                elif cat == "archive":
                    archive_count += 1
                else:
                    other_count += 1
        except Exception:
            pass

        return {
            "total_files": total,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "images": image_count,
            "videos": video_count,
            "audio": audio_count,
            "documents": document_count,
            "archives": archive_count,
            "other": other_count,
        }

    # ─── File Download / URL ─────────────────────────────────────

    def get_file_url(self, record_id: str) -> Optional[str]:
        """
        Get the public URL for a stored file.
        Returns None if the record doesn't exist or has no file.
        """
        record = self.get_record(record_id)
        if not record:
            return None
        file_field = record.get("file", "")
        if not file_field:
            return None
        # PocketBase serves files at /api/files/{collection}/{id}/{filename}
        # The "file" field contains the filename
        return f"{self.pb_url}/api/files/{self.COLLECTION_NAME}/{record_id}/{file_field}"
