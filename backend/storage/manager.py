import os
import re
from typing import Optional, List
from pocketbase import PocketBase
from backend.util.secrets import SecretsManager


class StorageManager:
    """
    Aina-chan's Storage Manager! (◕‿◕✿)

    Fully self-contained module for the 'storage' collection.
    Tracks metadata of all files and media uploaded to Anita-CMS.

    This can be deleted without breaking anything else!
    """

    COLLECTION_NAME = "storage"

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
                "CREATE UNIQUE INDEX `idx_storage_slug` ON `storage` (`slug`)",
                "CREATE INDEX `idx_storage_folder` ON `storage` (`folder`)",
                "CREATE INDEX `idx_storage_mime` ON `storage` (`mime_type`)",
                "CREATE INDEX `idx_storage_public` ON `storage` (`is_public`)",
            ],
            "fields": [
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

    # ─── Initialization ───────────────────────────────────────

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        if not self.admin_email or not self.admin_password:
            raise ValueError("Aina-chan needs admin email and password! ⊙﹏⊙")
        try:
            self.client.admins.auth_with_password(self.admin_email, self.admin_password)
            self._is_authenticated = True
            return True
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    def ensure_collection_exists(self) -> bool:
        """Create the storage collection if it doesn't exist."""
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False
        try:
            try:
                self.client.collections.get_one(self.COLLECTION_NAME)
                return True
            except Exception:
                self.client.collections.create(self._collection_schema)
                print("Aina-chan created the 'storage' collection! ✨")
                return True
        except Exception as e:
            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False

    # ─── CRUD ─────────────────────────────────────────────────

    def create_record(self, data: dict) -> Optional[dict]:
        """Create a new storage metadata record."""
        try:
            return self.client.collections.create(self.COLLECTION_NAME, data)
        except Exception as e:
            print(f"Aina-chan couldn't create storage record! Error: {e} (╥﹏╥)")
            return None

    def get_record(self, record_id: str) -> Optional[dict]:
        try:
            return self.client.collections.get_one(self.COLLECTION_NAME, record_id)
        except Exception:
            return None

    def get_record_by_slug(self, slug: str) -> Optional[dict]:
        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
                query_params={"filter": f'slug = "{slug}"', "limit": 1},
            )
            items = result.get("items", [])
            return items[0] if items else None
        except Exception:
            return None

    def update_record(self, record_id: str, data: dict) -> Optional[dict]:
        try:
            return self.client.collections.update(self.COLLECTION_NAME, record_id, data)
        except Exception as e:
            print(f"Aina-chan couldn't update storage record! Error: {e} (╥﹏╥)")
            return None

    def delete_record(self, record_id: str) -> bool:
        try:
            self.client.collections.delete(self.COLLECTION_NAME, record_id)
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete storage record! Error: {e} (╥﹏╥)")
            return False

    # ─── Listing with Filters ─────────────────────────────────

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
            return self.client.collections.get_list(self.COLLECTION_NAME, query_params=params)
        except Exception as e:
            print(f"Aina-chan couldn't list storage records! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── Slug Utilities ───────────────────────────────────────

    def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
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
        """Generate a unique storage slug from filename."""
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

    # ─── Folder Operations ────────────────────────────────────

    def list_folders(self) -> List[str]:
        """Get a list of all unique folder paths used in storage."""
        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
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

    # ─── MIME Type Helpers ────────────────────────────────────

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

    # ─── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get storage statistics, grouped by MIME category."""
        total = 0
        total_size = 0
        image_count = 0
        video_count = 0
        audio_count = 0
        document_count = 0
        other_count = 0

        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
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
            "other": other_count,
        }
